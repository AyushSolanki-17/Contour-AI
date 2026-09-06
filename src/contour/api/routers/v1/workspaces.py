"""Authenticated HTTP controllers for tenant-scoped catalog collections."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query, Request, Response

from contour.api.authentication import CredentialVerifier, bearer_principal
from contour.api.cursor import CursorCodec, CursorScope
from contour.api.cursor import page as collection_page
from contour.api.request_scope import correlation_id
from contour.api.request_scope import tenant_id as parse_tenant_id
from contour.api.schemas.error import ErrorResponse
from contour.api.schemas.v1.workspaces import (
    WorkspaceCreateRequest,
    WorkspacePage,
    WorkspaceResponse,
)
from contour.tenancy.application.collections import TenantCollectionService
from contour.tenancy.domain.access import Principal
from contour.workspaces.application.collections import WorkspaceCollectionService
from contour.workspaces.domain.workspace import Workspace


def create_workspaces_router(
    tenant_service: TenantCollectionService,
    workspace_service: WorkspaceCollectionService,
    verifier: CredentialVerifier,
    cursors: CursorCodec,
) -> APIRouter:
    """Bind workspaces HTTP handlers to explicitly supplied use cases."""
    router = APIRouter()
    principal = bearer_principal(verifier)

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
        access = tenant_service.open_tenant(
            authenticated, parse_tenant_id(tenant_id), correlation_id(request)
        )
        workspace, replayed = workspace_service.create_workspace(access, body.name, idempotency_key)
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
        access = tenant_service.open_tenant(
            authenticated, parse_tenant_id(tenant_id), correlation_id(request)
        )
        scope = CursorScope(str(authenticated.id), str(access.tenant_id), "workspaces", {})
        page, next_cursor = collection_page(
            workspace_service.list_workspaces(access), cursor, limit, scope, cursors
        )
        return WorkspacePage(
            items=tuple(_workspace_response(item) for item in page), cursor=next_cursor
        )

    return router


def _workspace_response(workspace: Workspace) -> WorkspaceResponse:
    """Serialize a workspace domain value at the delivery boundary."""
    return WorkspaceResponse(
        id=str(workspace.id), tenant_id=str(workspace.tenant_id), name=workspace.name
    )
