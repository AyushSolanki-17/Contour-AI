"""Public request and response schemas for workspace and source resources."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

RequiredText = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
WorkspaceCanonicalId = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=255,
        pattern=r"^WORKSPACE:[A-Za-z0-9._~-]+$",
    ),
]
SourceCanonicalId = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=255,
        pattern=r"^SOURCE(?::[A-Z][A-Z0-9_-]*)*:[A-Za-z0-9._~-]+$",
    ),
]


class WorkspacePutRequest(BaseModel):
    """Representation accepted when creating a trusted-local workspace."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: RequiredText = Field(max_length=200)


class WorkspaceResponse(BaseModel):
    """Canonical public representation of one workspace."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    owner: str


class SourcePutRequest(BaseModel):
    """Source-neutral logical-source registration representation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_type: Annotated[
        str,
        StringConstraints(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_-]*$"),
    ]
    canonical_locator: RequiredText = Field(max_length=2048)
    scope: RequiredText = Field(max_length=200)
    license: RequiredText | None = Field(default=None, max_length=200)
    data_classification: RequiredText = Field(max_length=200)


class SourceResponse(BaseModel):
    """Canonical public representation of one registered logical source."""

    model_config = ConfigDict(frozen=True)

    id: str
    workspace_id: str
    source_type: str
    canonical_locator: str
    scope: str
    license: str | None
    data_classification: str
