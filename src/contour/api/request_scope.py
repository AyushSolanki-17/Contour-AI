"""HTTP identifier and correlation translation for tenant-scoped requests."""

from uuid import uuid4

from fastapi import Request

from contour.errors import ResourceNotFoundError
from contour.tenancy.domain.tenant import TenantId
from contour.workspaces.domain.workspace import WorkspaceId


def tenant_id(value: str) -> TenantId:
    """Parse a route tenant identifier without exposing malformed ID distinctions."""
    try:
        namespace, local_value = value.rsplit(":", 1)
        return TenantId(namespace, local_value)
    except ValueError as error:
        raise ResourceNotFoundError() from error


def workspace_id(value: str) -> WorkspaceId:
    """Parse a route workspace identifier without exposing malformed ID distinctions."""
    try:
        namespace, local_value = value.rsplit(":", 1)
        return WorkspaceId(namespace, local_value)
    except ValueError as error:
        raise ResourceNotFoundError() from error


def correlation_id(request: Request) -> str:
    """Return a safe caller correlation ID or generate a non-secret request ID."""
    return (
        getattr(request.state, "correlation_id", None)
        or request.headers.get("X-Correlation-ID")
        or str(uuid4())
    )
