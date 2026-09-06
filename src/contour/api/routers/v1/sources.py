"""Authenticated HTTP controllers for tenant-scoped catalog collections."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query, Request, Response

from contour.api.authentication import CredentialVerifier, bearer_principal
from contour.api.cursor import CursorCodec, CursorScope
from contour.api.cursor import page as collection_page
from contour.api.request_scope import correlation_id
from contour.api.request_scope import tenant_id as parse_tenant_id
from contour.api.request_scope import workspace_id as parse_workspace_id
from contour.api.schemas.error import ErrorResponse
from contour.api.schemas.v1.sources import SourceCreateRequest, SourcePage, SourceResponse
from contour.sources.application.registration import SourceCollectionService
from contour.sources.domain.source import Source
from contour.tenancy.application.collections import TenantCollectionService
from contour.tenancy.domain.access import Principal


def create_sources_router(
    tenant_service: TenantCollectionService,
    source_service: SourceCollectionService,
    verifier: CredentialVerifier,
    cursors: CursorCodec,
) -> APIRouter:
    """Bind sources HTTP handlers to explicitly supplied use cases."""
    router = APIRouter()
    principal = bearer_principal(verifier)

    @router.post(
        "/tenants/{tenant_id}/workspaces/{workspace_id}/sources",
        response_model=SourceResponse,
        status_code=201,
        responses={
            401: {"model": ErrorResponse},
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
        },
    )
    def create_source(
        request: Request,
        tenant_id: str,
        workspace_id: str,
        body: SourceCreateRequest,
        response: Response,
        idempotency_key: str = Header(
            alias="Idempotency-Key", min_length=1, max_length=128, pattern=r"^[\x21-\x7e]+$"
        ),
        authenticated: Principal = Depends(principal),
    ) -> SourceResponse:
        """Register or safely replay one source in an accessible workspace."""
        access = tenant_service.open_tenant(
            authenticated, parse_tenant_id(tenant_id), correlation_id(request)
        )
        source, replayed = source_service.create_source(
            access=access,
            workspace_id=parse_workspace_id(workspace_id),
            connector_kind=body.connector_kind,
            canonical_locator=body.canonical_locator,
            scope=body.scope,
            license_name=body.license,
            data_classification=body.data_classification,
            idempotency_key=idempotency_key,
        )
        if replayed:
            response.status_code = 200
        return _source_response(source)

    @router.get(
        "/tenants/{tenant_id}/workspaces/{workspace_id}/sources",
        response_model=SourcePage,
        responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def list_sources(
        request: Request,
        tenant_id: str,
        workspace_id: str,
        cursor: str | None = None,
        limit: int = Query(default=50, ge=1, le=100),
        authenticated: Principal = Depends(principal),
    ) -> SourcePage:
        """List sources in one verified workspace in deterministic order."""
        access = tenant_service.open_tenant(
            authenticated, parse_tenant_id(tenant_id), correlation_id(request)
        )
        nested_workspace_id = parse_workspace_id(workspace_id)
        scope = CursorScope(
            str(authenticated.id), str(access.tenant_id), f"sources:{nested_workspace_id}", {}
        )
        page, next_cursor = collection_page(
            source_service.list_sources(access, nested_workspace_id), cursor, limit, scope, cursors
        )
        return SourcePage(items=tuple(_source_response(item) for item in page), cursor=next_cursor)

    return router


def _source_response(source: Source) -> SourceResponse:
    """Serialize a source domain value at the delivery boundary."""
    return SourceResponse(
        id=str(source.id),
        tenant_id=str(source.tenant_id),
        workspace_id=str(source.workspace_id),
        connector_kind=source.source_type,
        canonical_locator=source.canonical_locator,
        scope=source.scope,
        license=source.license,
        data_classification=source.data_classification,
    )
