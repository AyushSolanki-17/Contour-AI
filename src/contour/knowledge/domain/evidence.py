"""Evidence identity and exact locator.

Evidence is the inspectable connection from a derived record back to one
immutable source version. The identifier and locator are one conceptual family,
so they are intentionally co-located.
"""

from __future__ import annotations

from dataclasses import dataclass

from contour.identifiers import require_identifier_value, require_namespace
from contour.sources.domain.source_version import SourceVersionId
from contour.tenancy.domain.tenant import TenantId
from contour.workspaces.domain.workspace import WorkspaceId


def require_evidence_ids(value: tuple[EvidenceId, ...]) -> tuple[EvidenceId, ...]:
    """Require one or more distinct evidence identifiers for a knowledge assertion.

    Args:
        value: Candidate evidence identifiers attached to an entity or relationship.

    Returns:
        The validated tuple unchanged.

    Raises:
        TypeError: If an item is not an EvidenceId.
        ValueError: If the tuple is empty or contains duplicate identifiers.
    """
    if not isinstance(value, tuple) or not value:
        raise ValueError("evidence_ids must contain at least one EvidenceId")
    if any(not isinstance(item, EvidenceId) for item in value):
        raise TypeError("evidence_ids must contain only EvidenceId values")
    if len(set(value)) != len(value):
        raise ValueError("evidence_ids must not contain duplicates")
    return value


@dataclass(frozen=True, slots=True)
class EvidenceId:
    """A distinct identifier reserved for an evidence record."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed evidence identity components."""
        object.__setattr__(self, "namespace", require_namespace(self.namespace))
        object.__setattr__(self, "value", require_identifier_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized evidence identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class EvidenceLocator:
    """An inspectable field or byte span inside exactly one immutable version."""

    tenant_id: TenantId
    workspace_id: WorkspaceId
    source_version_id: SourceVersionId
    locator: str
    start_offset: int | None = None
    end_offset: int | None = None

    def __post_init__(self) -> None:
        """Reject ambiguous locators and spans detached from a source version."""
        if not isinstance(self.tenant_id, TenantId):
            raise TypeError("tenant_id must be a TenantId")
        if not isinstance(self.workspace_id, WorkspaceId):
            raise TypeError("workspace_id must be a WorkspaceId")
        if not isinstance(self.source_version_id, SourceVersionId):
            raise TypeError("source_version_id must be a SourceVersionId")
        if not isinstance(self.locator, str):
            raise TypeError("locator must be a string")
        if not self.locator or self.locator.strip() != self.locator:
            raise ValueError("locator must be non-empty text without surrounding whitespace")
        if (self.start_offset is None) != (self.end_offset is None):
            raise ValueError("evidence spans require both start_offset and end_offset")
        if self.start_offset is not None and (
            isinstance(self.start_offset, bool) or not isinstance(self.start_offset, int)
        ):
            raise TypeError("start_offset must be an integer or None")
        if self.end_offset is not None and (
            isinstance(self.end_offset, bool) or not isinstance(self.end_offset, int)
        ):
            raise TypeError("end_offset must be an integer or None")
        if self.start_offset is not None and (
            self.start_offset < 0 or self.end_offset is None or self.end_offset <= self.start_offset
        ):
            raise ValueError("evidence spans must be non-negative and have a positive length")

    def to_primitive(self) -> dict[str, str | int | None]:
        """Return a framework-neutral exact locator representation."""
        return {
            "tenant_id": str(self.tenant_id),
            "workspace_id": str(self.workspace_id),
            "source_version_id": str(self.source_version_id),
            "locator": self.locator,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
        }
