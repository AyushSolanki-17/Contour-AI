"""HTTP controllers for workspace and logical-source product resources."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path

from contour.api.schemas.error import ErrorResponse
from contour.api.schemas.workspace_source import (
    SourceCanonicalId,
    SourcePutRequest,
    SourceResponse,
    WorkspaceCanonicalId,
    WorkspacePutRequest,
    WorkspaceResponse,
)
from contour.domain.source import Source, SourceId
from contour.domain.workspace import Workspace, WorkspaceId
from contour.services.workspace_source_service import WorkspaceSourceService

type ResponseDocumentation = dict[int | str, dict[str, Any]]

_INVALID_RESPONSE: ResponseDocumentation = {
    400: {"model": ErrorResponse, "description": "Invalid request"}
}
_NOT_FOUND_RESPONSE: ResponseDocumentation = {
    404: {"model": ErrorResponse, "description": "Resource not found"}
}
_CONFLICT_RESPONSE: ResponseDocumentation = {
    409: {"model": ErrorResponse, "description": "Identity conflict"}
}
_UNSUPPORTED_RESPONSE: ResponseDocumentation = {
    422: {"model": ErrorResponse, "description": "Unsupported source"}
}
_DEPENDENCY_RESPONSE: ResponseDocumentation = {
    503: {"model": ErrorResponse, "description": "Required dependency unavailable"}
}


def create_workspace_source_router(service: WorkspaceSourceService) -> APIRouter:
    """Bind workspace/source use cases to the versioned HTTP contract."""
    router = APIRouter(prefix="/api/v1", tags=["catalog"])

    @router.put(
        "/workspaces/{workspace_id}",
        response_model=WorkspaceResponse,
        responses=_INVALID_RESPONSE | _CONFLICT_RESPONSE | _DEPENDENCY_RESPONSE,
    )
    def put_workspace(
        workspace_id: Annotated[
            WorkspaceCanonicalId, Path(description="Canonical workspace identifier")
        ],
        request: Annotated[WorkspacePutRequest, Body()],
    ) -> WorkspaceResponse:
        """Create a workspace or return its exact accepted replay."""
        workspace = service.put_workspace(_workspace_id(workspace_id), name=request.name)
        return _workspace_response(workspace)

    @router.get(
        "/workspaces/{workspace_id}",
        response_model=WorkspaceResponse,
        responses=_INVALID_RESPONSE | _NOT_FOUND_RESPONSE | _DEPENDENCY_RESPONSE,
    )
    def get_workspace(
        workspace_id: Annotated[
            WorkspaceCanonicalId, Path(description="Canonical workspace identifier")
        ],
    ) -> WorkspaceResponse:
        """Return an accepted workspace by canonical identity."""
        return _workspace_response(service.get_workspace(_workspace_id(workspace_id)))

    @router.put(
        "/workspaces/{workspace_id}/sources/{source_id}",
        response_model=SourceResponse,
        responses=(
            _INVALID_RESPONSE
            | _NOT_FOUND_RESPONSE
            | _CONFLICT_RESPONSE
            | _UNSUPPORTED_RESPONSE
            | _DEPENDENCY_RESPONSE
        ),
    )
    def put_source(
        workspace_id: Annotated[
            WorkspaceCanonicalId, Path(description="Canonical workspace identifier")
        ],
        source_id: Annotated[SourceCanonicalId, Path(description="Canonical source identifier")],
        request: Annotated[SourcePutRequest, Body()],
    ) -> SourceResponse:
        """Register a supported logical source or return its exact replay."""
        source = Source(
            _source_id(source_id),
            service.tenant_id,
            _workspace_id(workspace_id),
            request.canonical_locator,
            request.source_type,
            request.scope,
            request.license,
            request.data_classification,
        )
        return _source_response(service.put_source(source))

    @router.get(
        "/workspaces/{workspace_id}/sources/{source_id}",
        response_model=SourceResponse,
        responses=_INVALID_RESPONSE | _NOT_FOUND_RESPONSE | _DEPENDENCY_RESPONSE,
    )
    def get_source(
        workspace_id: Annotated[
            WorkspaceCanonicalId, Path(description="Canonical workspace identifier")
        ],
        source_id: Annotated[SourceCanonicalId, Path(description="Canonical source identifier")],
    ) -> SourceResponse:
        """Return a source only through its owning workspace path."""
        source = service.get_source(_workspace_id(workspace_id), _source_id(source_id))
        return _source_response(source)

    return router


def _workspace_id(value: str) -> WorkspaceId:
    """Translate one canonical public identifier into its domain value."""
    namespace, local_value = value.rsplit(":", maxsplit=1)
    return WorkspaceId(namespace, local_value)


def _source_id(value: str) -> SourceId:
    """Translate one canonical public identifier into its domain value."""
    namespace, local_value = value.rsplit(":", maxsplit=1)
    return SourceId(namespace, local_value)


def _workspace_response(workspace: Workspace) -> WorkspaceResponse:
    """Translate a workspace domain value into its public representation."""
    return WorkspaceResponse(id=str(workspace.id), name=workspace.name, owner=workspace.owner)


def _source_response(source: Source) -> SourceResponse:
    """Translate a source domain value into its public representation."""
    return SourceResponse(
        id=str(source.id),
        workspace_id=str(source.workspace_id),
        source_type=source.source_type,
        canonical_locator=source.canonical_locator,
        scope=source.scope,
        license=source.license,
        data_classification=source.data_classification,
    )
