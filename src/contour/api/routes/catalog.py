"""Authenticated HTTP controllers for tenant-scoped catalog collections."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Query, Request, Response

from contour.api.authentication import CredentialVerifier, bearer_principal
from contour.api.cursor import CursorCodec, CursorScope
from contour.api.schemas.catalog import (
    SourceCreateRequest,
    SourcePage,
    SourceResponse,
    TenantCreateRequest,
    TenantPage,
    TenantResponse,
    WorkspaceCreateRequest,
    WorkspacePage,
    WorkspaceResponse,
)
from contour.api.schemas.error import ErrorResponse
from contour.domain.access import Principal
from contour.domain.source import Source
from contour.domain.tenant import TenantId
from contour.domain.workspace import Workspace, WorkspaceId
from contour.services.catalog_collections import CatalogCollectionService
from contour.services.resource_errors import ResourceNotFoundError


def create_catalog_router(
    service: CatalogCollectionService, verifier: CredentialVerifier, cursors: CursorCodec
) -> APIRouter:
    """Bind authenticated catalog services to their frozen HTTP routes."""
    router = APIRouter(prefix="/api/v1", tags=["product"])
    principal = bearer_principal(verifier)

    @router.post(
        "/tenants",
        response_model=TenantResponse,
        status_code=201,
        responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    )
    def create_tenant(
        body: TenantCreateRequest,
        response: Response,
        idempotency_key: str = Header(
            alias="Idempotency-Key", min_length=1, max_length=128, pattern=r"^[\x21-\x7e]+$"
        ),
        authenticated: Principal = Depends(principal),
    ) -> TenantResponse:
        """Create a tenant and membership for the authenticated principal."""
        tenant, replayed = service.create_tenant(authenticated, body.name, idempotency_key)
        if replayed:
            response.status_code = 200
        return TenantResponse(id=str(tenant.id), name=tenant.name)

    @router.get("/tenants", response_model=TenantPage, responses={401: {"model": ErrorResponse}})
    def list_tenants(
        cursor: str | None = None,
        limit: int = Query(default=50, ge=1, le=100),
        authenticated: Principal = Depends(principal),
    ) -> TenantPage:
        """List only tenants that the authenticated principal can access."""
        scope = CursorScope(str(authenticated.id), "global", "tenants", {})
        page, next_cursor = _page(
            service.list_tenants(authenticated), cursor, limit, scope, cursors
        )
        return TenantPage(
            items=tuple(TenantResponse(id=str(item.id), name=item.name) for item in page),
            cursor=next_cursor,
        )

    @router.post(
        "/tenants/{tenant_id}/workspaces",
        response_model=WorkspaceResponse,
        status_code=201,
        responses={
            401: {"model": ErrorResponse},
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
        },
    )
    def create_workspace(
        request: Request,
        tenant_id: str,
        body: WorkspaceCreateRequest,
        response: Response,
        idempotency_key: str = Header(
            alias="Idempotency-Key", min_length=1, max_length=128, pattern=r"^[\x21-\x7e]+$"
        ),
        authenticated: Principal = Depends(principal),
    ) -> WorkspaceResponse:
        """Create or safely replay one workspace in an accessible tenant."""
        access = service.open_tenant(authenticated, _tenant_id(tenant_id), _correlation_id(request))
        workspace, replayed = service.create_workspace(access, body.name, idempotency_key)
        if replayed:
            response.status_code = 200
        return WorkspaceResponse(
            id=str(workspace.id), tenant_id=str(workspace.tenant_id), name=workspace.name
        )

    @router.get(
        "/tenants/{tenant_id}/workspaces",
        response_model=WorkspacePage,
        responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    )
    def list_workspaces(
        request: Request,
        tenant_id: str,
        cursor: str | None = None,
        limit: int = Query(default=50, ge=1, le=100),
        authenticated: Principal = Depends(principal),
    ) -> WorkspacePage:
        """List workspaces in one verified tenant in deterministic order."""
        access = service.open_tenant(authenticated, _tenant_id(tenant_id), _correlation_id(request))
        scope = CursorScope(str(authenticated.id), str(access.tenant_id), "workspaces", {})
        page, next_cursor = _page(service.list_workspaces(access), cursor, limit, scope, cursors)
        return WorkspacePage(
            items=tuple(_workspace_response(item) for item in page), cursor=next_cursor
        )

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
        access = service.open_tenant(authenticated, _tenant_id(tenant_id), _correlation_id(request))
        source, replayed = service.create_source(
            access=access,
            workspace_id=_workspace_id(workspace_id),
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
        access = service.open_tenant(authenticated, _tenant_id(tenant_id), _correlation_id(request))
        nested_workspace_id = _workspace_id(workspace_id)
        scope = CursorScope(
            str(authenticated.id), str(access.tenant_id), f"sources:{nested_workspace_id}", {}
        )
        page, next_cursor = _page(
            service.list_sources(access, nested_workspace_id), cursor, limit, scope, cursors
        )
        return SourcePage(items=tuple(_source_response(item) for item in page), cursor=next_cursor)

    return router


def _tenant_id(value: str) -> TenantId:
    """Parse a route tenant identifier without exposing malformed ID distinctions."""
    try:
        namespace, local_value = value.rsplit(":", 1)
        return TenantId(namespace, local_value)
    except ValueError as error:
        raise ResourceNotFoundError() from error


def _workspace_id(value: str) -> WorkspaceId:
    """Parse a route workspace identifier without exposing malformed ID distinctions."""
    try:
        namespace, local_value = value.rsplit(":", 1)
        return WorkspaceId(namespace, local_value)
    except ValueError as error:
        raise ResourceNotFoundError() from error


def _correlation_id(request: Request) -> str:
    """Return a safe caller correlation ID or generate a non-secret request ID."""
    return request.headers.get("X-Correlation-ID") or str(uuid4())


def _workspace_response(workspace: Workspace) -> WorkspaceResponse:
    """Serialize a workspace domain value at the delivery boundary."""
    return WorkspaceResponse(
        id=str(workspace.id), tenant_id=str(workspace.tenant_id), name=workspace.name
    )


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


def _page[T](
    items: tuple[T, ...], cursor: str | None, limit: int, scope: CursorScope, cursors: CursorCodec
) -> tuple[tuple[T, ...], str | None]:
    """Return one deterministic cursor page from identity-ordered collection records."""
    start = 0
    if cursor is not None:
        after = cursors.decode(cursor, scope)
        identities = [str(getattr(item, "id")) for item in items]
        try:
            start = identities.index(after) + 1
        except ValueError as error:
            raise ResourceNotFoundError() from error
    page = items[start : start + limit]
    next_cursor = (
        cursors.encode(scope, str(getattr(page[-1], "id")))
        if start + len(page) < len(items)
        else None
    )
    return page, next_cursor
