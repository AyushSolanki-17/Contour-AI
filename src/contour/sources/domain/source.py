"""Logical source aggregate and identity.

A source describes a stable origin and its admission metadata. Mutable observed
content belongs to :class:`SourceVersion`, so a source can never silently mean
the latest retrieved bytes.
"""

from __future__ import annotations

from dataclasses import dataclass

from contour.identifiers import require_identifier_value, require_namespace
from contour.tenancy.domain.tenant import TenantId
from contour.validation import require_text
from contour.workspaces.domain.workspace import WorkspaceId


@dataclass(frozen=True, slots=True)
class SourceId:
    """A source-owned identifier within an explicit namespace."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed source identity components."""
        object.__setattr__(self, "namespace", require_namespace(self.namespace))
        object.__setattr__(self, "value", require_identifier_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized source identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class Source:
    """A stable logical origin without mutable latest content."""

    id: SourceId
    tenant_id: TenantId
    workspace_id: WorkspaceId
    canonical_locator: str
    source_type: str
    scope: str
    license: str | None
    data_classification: str

    def __post_init__(self) -> None:
        """Validate source ownership and explicit metadata values."""
        if not isinstance(self.id, SourceId):
            raise TypeError("id must be a SourceId")
        if not isinstance(self.tenant_id, TenantId):
            raise TypeError("tenant_id must be a TenantId")
        if not isinstance(self.workspace_id, WorkspaceId):
            raise TypeError("workspace_id must be a WorkspaceId")
        for field_name in ("canonical_locator", "source_type", "scope", "data_classification"):
            require_text(getattr(self, field_name), field_name=field_name)
        if self.license is not None:
            require_text(self.license, field_name="license")
