"""Immutable source-version and exact-evidence domain values."""

from __future__ import annotations

from dataclasses import dataclass

from contour.domain.identifiers import ContentDigest, SourceId, SourceVersionId
from contour.domain.time import TimePoint


def _require_optional_metadata(value: str | None, *, field_name: str) -> str | None:
    """Validate optional source metadata without inventing an unavailable value.

    Raises:
        TypeError: If a supplied value is not text.
        ValueError: If a supplied value is empty or has surrounding whitespace.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty text without surrounding whitespace")
    return value


@dataclass(frozen=True, slots=True)
class SourceVersion:
    """Immutable metadata for exact bytes observed from one logical source."""

    id: SourceVersionId
    source_id: SourceId
    content_digest: ContentDigest
    upstream_revision: str | None
    source_time: TimePoint
    revision_time: TimePoint

    def __post_init__(self) -> None:
        """Ensure the version key cannot describe another source or content."""
        if not isinstance(self.id, SourceVersionId):
            raise TypeError("id must be a SourceVersionId")
        if not isinstance(self.source_id, SourceId):
            raise TypeError("source_id must be a SourceId")
        if not isinstance(self.content_digest, ContentDigest):
            raise TypeError("content_digest must be a ContentDigest")
        if self.id.source_id != self.source_id:
            raise ValueError("source version id must reference the supplied source_id")
        if self.id.content_digest != self.content_digest:
            raise ValueError("source version id must reference the supplied content_digest")
        object.__setattr__(
            self,
            "upstream_revision",
            _require_optional_metadata(self.upstream_revision, field_name="upstream_revision"),
        )
        if not isinstance(self.source_time, TimePoint):
            raise TypeError("source_time must be a TimePoint")
        if not isinstance(self.revision_time, TimePoint):
            raise TypeError("revision_time must be a TimePoint")

    def to_primitive(self) -> dict[str, str | None]:
        """Return a framework-neutral representation preserving unknown times."""
        return {
            "id": str(self.id),
            "source_id": str(self.source_id),
            "content_digest": str(self.content_digest),
            "upstream_revision": self.upstream_revision,
            "source_time": self.source_time.to_primitive(),
            "revision_time": self.revision_time.to_primitive(),
        }


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
