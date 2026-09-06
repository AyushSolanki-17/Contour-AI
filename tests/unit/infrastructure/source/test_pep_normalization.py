"""Contracts for deterministic PEP normalization and exact raw locators."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest

from contour.infrastructure.artifact.filesystem import FileSystemArtifactRepository
from contour.infrastructure.source.pep_normalizer import PepHtmlNormalizer, PepNormalizationError
from contour.sources.application.normalization import SourceNormalizationService
from contour.sources.domain.source import SourceId
from contour.sources.domain.source_version import ContentDigest, SourceVersion, SourceVersionId
from contour.tenancy.domain.tenant import TenantId
from contour.time import TimePoint
from contour.workspaces.domain.workspace import WorkspaceId

_FIXTURE = Path(__file__).resolve().parents[3] / "fixtures" / "pep_0723.html"


def _version(content: bytes) -> SourceVersion:
    """Create the immutable raw version represented by the fixture bytes."""
    source_id = SourceId("SOURCE:PEP", "723")
    digest = ContentDigest(sha256(content).hexdigest())
    return SourceVersion(
        SourceVersionId(source_id, digest),
        TenantId("TENANT", "normalization"),
        WorkspaceId("WORKSPACE", "normalization"),
        source_id,
        digest,
        TimePoint(datetime(2026, 9, 6, tzinfo=UTC)),
        "fixture-r1",
        TimePoint.unknown(),
        TimePoint.unknown(),
    )


def test_normalization_is_deterministic_and_preserves_exact_raw_locators(tmp_path: Path) -> None:
    """The normalized artifact records stable derivation and raw-byte spans."""
    raw = _FIXTURE.read_bytes()
    version = _version(raw)
    service = SourceNormalizationService(
        FileSystemArtifactRepository(tmp_path), PepHtmlNormalizer()
    )

    first = service.normalize(version, raw)
    repeated = service.normalize(version, raw)

    assert repeated.artifact_digest == first.artifact_digest
    assert repeated.artifact_state.value == "unchanged"
    assert first.normalized.source_version_id == version.id
    assert first.normalized.transformation == "pep-html-normalizer-v1"
    assert (
        first.normalized.content
        == b"title: PEP 723\nsummary: Pinned public-fixture excerpt for deterministic Phase 0 tests.\n"
    )
    for locator in first.normalized.locators:
        assert (
            raw[locator.raw_start : locator.raw_end].decode() in first.normalized.content.decode()
        )


@pytest.mark.parametrize(
    "raw",
    [
        b"<html><body><h1>PEP 723</h1></body></html>",
        b"<html><body><h1>PEP&nbsp;723</h1><p>x</p></body></html>",
    ],
)
def test_normalization_rejects_missing_or_unlocatable_fields(raw: bytes) -> None:
    """Malformed structure and locator loss never produce partial normalized output."""
    with pytest.raises(PepNormalizationError):
        PepHtmlNormalizer().normalize(_version(raw), raw)


def test_normalization_rejects_bytes_that_do_not_match_the_raw_version(tmp_path: Path) -> None:
    """Normalization cannot derive a manifest from content outside the immutable version."""
    raw = _FIXTURE.read_bytes()
    service = SourceNormalizationService(
        FileSystemArtifactRepository(tmp_path), PepHtmlNormalizer()
    )

    with pytest.raises(ValueError, match="raw_content"):
        service.normalize(_version(raw), raw + b"changed")
