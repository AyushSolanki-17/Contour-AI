"""Authenticated HTTP controllers for tenant-scoped catalog collections."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query, Response

from contour.api.authentication import CredentialVerifier, bearer_principal
from contour.api.cursor import CursorCodec, CursorScope
from contour.api.cursor import page as collection_page
from contour.api.schemas.error import ErrorResponse
from contour.api.schemas.v1.tenants import TenantCreateRequest, TenantPage, TenantResponse
from contour.tenancy.application.collections import TenantCollectionService
from contour.tenancy.domain.access import Principal


def create_tenants_router(
    tenant_service: TenantCollectionService,
    verifier: CredentialVerifier,
    cursors: CursorCodec,
) -> APIRouter:
    """Bind tenants HTTP handlers to explicitly supplied use cases."""
    router = APIRouter()
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
        tenant, replayed = tenant_service.create_tenant(authenticated, body.name, idempotency_key)
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
        page, next_cursor = collection_page(
            tenant_service.list_tenants(authenticated), cursor, limit, scope, cursors
        )
        return TenantPage(
            items=tuple(TenantResponse(id=str(item.id), name=item.name) for item in page),
            cursor=next_cursor,
        )

    return router
