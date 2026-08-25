"""Persistence contract for exact content-addressed artifacts."""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from contour.domain.source_version import ContentDigest


class ArtifactWriteState(StrEnum):
    """Describe whether a verified artifact was created, reused, or repaired."""

    CREATED = "created"
    UNCHANGED = "unchanged"
    REPAIRED = "repaired"


class ArtifactRepository(Protocol):
    """Stores and retrieves exact bytes by their declared SHA-256 identity."""

    def persist(self, content: bytes, digest: ContentDigest) -> ArtifactWriteState:
        """Atomically persist verified bytes and report the durable outcome."""

    def retrieve(self, digest: ContentDigest) -> bytes:
        """Return bytes only when the stored content matches its address."""
