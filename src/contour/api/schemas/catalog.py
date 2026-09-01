"""Public request and response schemas for tenant-scoped catalog collections."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TenantCreateRequest(BaseModel):
    """Request payload for creating a tenant and initial membership."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)


class TenantResponse(BaseModel):
    """Stable public tenant representation."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str


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


class SourceCreateRequest(BaseModel):
    """Source-neutral registration payload for one logical source."""

    model_config = ConfigDict(frozen=True)

    connector_kind: str = Field(min_length=1)
    canonical_locator: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    license: str | None = None
    data_classification: str = Field(min_length=1)


class SourceResponse(BaseModel):
    """Stable public source registration representation."""

    model_config = ConfigDict(frozen=True)

    id: str
    tenant_id: str
    workspace_id: str
    connector_kind: str
    canonical_locator: str
    scope: str
    license: str | None
    data_classification: str


class TenantPage(BaseModel):
    """One deterministic page of visible tenants."""

    model_config = ConfigDict(frozen=True)

    items: tuple[TenantResponse, ...]
    cursor: str | None = None


class WorkspacePage(BaseModel):
    """One deterministic page of workspaces in a tenant."""

    model_config = ConfigDict(frozen=True)

    items: tuple[WorkspaceResponse, ...]
    cursor: str | None = None


class SourcePage(BaseModel):
    """One deterministic page of sources in a workspace."""

    model_config = ConfigDict(frozen=True)

    items: tuple[SourceResponse, ...]
    cursor: str | None = None
