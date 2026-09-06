"""Artifact-first persistence for deterministic normalized source content."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from contour.sources.application.artifact_store import ArtifactRepository, ArtifactWriteState
from contour.sources.domain.normalized_content import NormalizedContent
from contour.sources.domain.source_version import ContentDigest, SourceVersion


class ContentNormalizer(Protocol):
    """Transforms one immutable raw version into source-neutral normalized content."""

    def normalize(self, version: SourceVersion, raw_content: bytes) -> NormalizedContent:
        """Return deterministic normalized content with exact raw-byte locators."""


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    """The durable normalized manifest artifact and its verified write outcome."""

    normalized: NormalizedContent
    artifact_digest: ContentDigest
    artifact_state: ArtifactWriteState


class SourceNormalizationService:
    """Normalize immutable raw bytes and persist a rebuildable manifest artifact."""

    def __init__(self, artifacts: ArtifactRepository, normalizer: ContentNormalizer) -> None:
        """Bind the source-neutral artifact store and source-specific transformer."""
        self._artifacts = artifacts
        self._normalizer = normalizer

    def normalize(self, version: SourceVersion, raw_content: bytes) -> NormalizationResult:
        """Persist a canonical manifest derived from one verified raw source version.

        Raises:
            ValueError: If raw bytes do not match the immutable source-version digest.
        """
        if ContentDigest(sha256(raw_content).hexdigest()) != version.content_digest:
            raise ValueError("raw_content does not match source version identity")
        normalized = self._normalizer.normalize(version, raw_content)
        manifest = _manifest_bytes(normalized)
        digest = ContentDigest(sha256(manifest).hexdigest())
        return NormalizationResult(normalized, digest, self._artifacts.persist(manifest, digest))


def _manifest_bytes(normalized: NormalizedContent) -> bytes:
    """Serialize derivation, normalized bytes, and exact locators canonically."""
    payload = {
        "content": normalized.content.decode("utf-8"),
        "locators": [locator.to_primitive() for locator in normalized.locators],
        "source_version_id": str(normalized.source_version_id),
        "transformation": normalized.transformation,
    }
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode()
