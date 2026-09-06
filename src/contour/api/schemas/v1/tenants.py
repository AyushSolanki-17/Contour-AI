"""Public tenants request and response schemas."""

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


class TenantPage(BaseModel):
    """One deterministic page of visible tenants."""

    model_config = ConfigDict(frozen=True)

    items: tuple[TenantResponse, ...]
    cursor: str | None = None
