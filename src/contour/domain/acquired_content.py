"""Source-neutral exact content admitted by an acquisition adapter."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from contour.domain.source import SourceId
from contour.domain.source_version import ContentDigest
from contour.domain.time_point import TimePoint


@dataclass(frozen=True, slots=True)
class AcquiredContent:
    """Exact bytes and provenance metadata returned by a source adapter."""

    source_id: SourceId
    content: bytes
    content_digest: ContentDigest
    observed_at: TimePoint
    upstream_revision: str | None
    revision_time: TimePoint

    def __post_init__(self) -> None:
        """Validate content identity and preserve unknown upstream metadata."""
        if not isinstance(self.source_id, SourceId):
            raise TypeError("source_id must be a SourceId")
        if not isinstance(self.content, bytes):
            raise TypeError("content must be bytes")
        if not isinstance(self.content_digest, ContentDigest):
            raise TypeError("content_digest must be a ContentDigest")
        if sha256(self.content).hexdigest() != self.content_digest.value:
            raise ValueError("content must match content_digest")
        if not isinstance(self.observed_at, TimePoint):
            raise TypeError("observed_at must be a TimePoint")
        if not self.observed_at.is_known:
            raise ValueError("observed_at must contain the acquisition observation time")
        if self.upstream_revision is not None:
            if not isinstance(self.upstream_revision, str):
                raise TypeError("upstream_revision must be a string or None")
            if (
                not self.upstream_revision
                or self.upstream_revision.strip() != self.upstream_revision
            ):
                raise ValueError(
                    "upstream_revision must be non-empty text without surrounding whitespace"
                )
        if not isinstance(self.revision_time, TimePoint):
            raise TypeError("revision_time must be a TimePoint")
