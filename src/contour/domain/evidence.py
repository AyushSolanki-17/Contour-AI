"""Evidence identity and exact locator.

Evidence is the inspectable connection from a derived record back to one
immutable source version. The identifier and locator are one conceptual family,
so they are intentionally co-located.
"""

from __future__ import annotations

from dataclasses import dataclass

from contour.domain.identifier_validation import require_identifier_value, require_namespace
from contour.domain.source_version import SourceVersionId


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

    source_version_id: SourceVersionId
    locator: str
    start_offset: int | None = None
    end_offset: int | None = None

    def __post_init__(self) -> None:
        """Reject ambiguous locators and spans detached from a source version."""
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
            "source_version_id": str(self.source_version_id),
            "locator": self.locator,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
        }
