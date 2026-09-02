"""Immutable observed source content and its content-addressed identity.

This module owns the version family: the SHA-256 digest, a source-qualified
version identifier, and immutable metadata for the exact bytes admitted to
Contour. Keeping the family together makes the source-version invariant visible
without making the logical-source module do double duty.
"""

from __future__ import annotations

from dataclasses import dataclass

from contour.identifiers import require_sha256_digest
from contour.sources.domain.source import SourceId
from contour.tenancy.domain.tenant import TenantId
from contour.time import TimePoint
from contour.workspaces.domain.workspace import WorkspaceId


@dataclass(frozen=True, slots=True)
class ContentDigest:
    """The SHA-256 identity of the exact bytes admitted for a source version."""

    value: str

    def __post_init__(self) -> None:
        """Reject digests that cannot be a canonical SHA-256 value."""
        object.__setattr__(self, "value", require_sha256_digest(self.value))

    def __str__(self) -> str:
        """Return the algorithm-qualified digest serialization."""
        return f"sha256:{self.value}"


@dataclass(frozen=True, slots=True)
class SourceVersionId:
    """The immutable identity of one source's admitted content version."""

    source_id: SourceId
    content_digest: ContentDigest

    def __post_init__(self) -> None:
        """Require source and digest values with their intended domain types."""
        if not isinstance(self.source_id, SourceId):
            raise TypeError("source_id must be a SourceId")
        if not isinstance(self.content_digest, ContentDigest):
            raise TypeError("content_digest must be a ContentDigest")

    def __str__(self) -> str:
        """Return a source-qualified immutable version key."""
        return f"{self.source_id}@{self.content_digest}"


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
    tenant_id: TenantId
    workspace_id: WorkspaceId
    source_id: SourceId
    content_digest: ContentDigest
    observed_at: TimePoint
    upstream_revision: str | None
    source_time: TimePoint
    revision_time: TimePoint

    def __post_init__(self) -> None:
        """Ensure the version key cannot describe another source or content."""
        if not isinstance(self.id, SourceVersionId):
            raise TypeError("id must be a SourceVersionId")
        if not isinstance(self.tenant_id, TenantId):
            raise TypeError("tenant_id must be a TenantId")
        if not isinstance(self.workspace_id, WorkspaceId):
            raise TypeError("workspace_id must be a WorkspaceId")
        if not isinstance(self.source_id, SourceId):
            raise TypeError("source_id must be a SourceId")
        if not isinstance(self.content_digest, ContentDigest):
            raise TypeError("content_digest must be a ContentDigest")
        if self.id.source_id != self.source_id:
            raise ValueError("source version id must reference the supplied source_id")
        if self.id.content_digest != self.content_digest:
            raise ValueError("source version id must reference the supplied content_digest")
        if not isinstance(self.observed_at, TimePoint):
            raise TypeError("observed_at must be a TimePoint")
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
            "tenant_id": str(self.tenant_id),
            "workspace_id": str(self.workspace_id),
            "source_id": str(self.source_id),
            "content_digest": str(self.content_digest),
            "observed_at": self.observed_at.to_primitive(),
            "upstream_revision": self.upstream_revision,
            "source_time": self.source_time.to_primitive(),
            "revision_time": self.revision_time.to_primitive(),
        }
