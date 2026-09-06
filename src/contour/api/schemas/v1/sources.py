"""Public sources request and response schemas."""

from pydantic import BaseModel, ConfigDict, Field


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


class SourcePage(BaseModel):
    """One deterministic page of sources in a workspace."""

    model_config = ConfigDict(frozen=True)

    items: tuple[SourceResponse, ...]
    cursor: str | None = None
