"""Contracts for the real content-addressed filesystem boundary."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from contour.infrastructure.artifact.filesystem import FileSystemArtifactRepository
from contour.sources.application.artifact_errors import (
    ArtifactIntegrityError,
    ArtifactNotFoundError,
    ArtifactPersistenceError,
)
from contour.sources.application.artifact_store import ArtifactWriteState
from contour.sources.domain.source_version import ContentDigest


def _digest(content: bytes) -> ContentDigest:
    """Return the domain digest for exact test bytes."""
    return ContentDigest(sha256(content).hexdigest())


def test_artifact_round_trip_is_content_addressed_and_idempotent(tmp_path: Path) -> None:
    content = b"exact admitted PEP bytes"
    digest = _digest(content)
    repository = FileSystemArtifactRepository(tmp_path)

    assert repository.persist(content, digest) is ArtifactWriteState.CREATED
    assert repository.persist(content, digest) is ArtifactWriteState.UNCHANGED
    assert repository.retrieve(digest) == content
    assert repository.artifact_path(digest) == (
        tmp_path / "sha256" / digest.value[:2] / digest.value[2:]
    )
    assert tuple(path for path in tmp_path.rglob("*") if path.is_file()) == (
        repository.artifact_path(digest),
    )


def test_missing_and_corrupt_artifacts_are_explicit_and_repairable(tmp_path: Path) -> None:
    content = b"recoverable admitted bytes"
    digest = _digest(content)
    repository = FileSystemArtifactRepository(tmp_path)

    with pytest.raises(ArtifactNotFoundError):
        repository.retrieve(digest)

    repository.persist(content, digest)
    repository.artifact_path(digest).write_bytes(b"corrupt")
    with pytest.raises(ArtifactIntegrityError):
        repository.retrieve(digest)

    assert repository.persist(content, digest) is ArtifactWriteState.REPAIRED
    assert repository.retrieve(digest) == content


def test_artifact_failures_do_not_create_an_integrity_invalid_target(tmp_path: Path) -> None:
    content = b"validated content"
    digest = _digest(content)
    repository = FileSystemArtifactRepository(tmp_path)

    with pytest.raises(ArtifactIntegrityError):
        repository.persist(b"different content", digest)
    assert not repository.artifact_path(digest).exists()

    blocked_root = tmp_path / "not-a-directory"
    blocked_root.write_text("occupied", encoding="utf-8")
    blocked_repository = FileSystemArtifactRepository(blocked_root)
    with pytest.raises(ArtifactPersistenceError) as error:
        blocked_repository.persist(content, digest)

    assert str(blocked_root) not in str(error.value)
