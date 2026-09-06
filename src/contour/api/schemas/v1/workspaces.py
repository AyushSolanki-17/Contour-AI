"""Public workspaces request and response schemas."""

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreateRequest(BaseModel):
    """Request payload for creating one workspace in a selected tenant."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)


class WorkspaceResponse(BaseModel):
    """Stable public workspace representation."""

    model_config = ConfigDict(frozen=True)

    id: str
    tenant_id: str
    name: str


class WorkspacePage(BaseModel):
    """One deterministic page of workspaces in a tenant."""

    model_config = ConfigDict(frozen=True)

    items: tuple[WorkspaceResponse, ...]
    cursor: str | None = None
