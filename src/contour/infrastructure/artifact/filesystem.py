"""Atomic filesystem storage for SHA-256-addressed artifacts."""

from __future__ import annotations

import os
import tempfile
from hashlib import sha256
from pathlib import Path

from contour.sources.application.artifact_errors import (
    ArtifactIntegrityError,
    ArtifactNotFoundError,
    ArtifactPersistenceError,
)
from contour.sources.application.artifact_store import ArtifactWriteState
from contour.sources.domain.source_version import ContentDigest


class FileSystemArtifactRepository:
    """Stores exact bytes under a deterministic digest-derived filesystem path."""

    def __init__(self, root: Path) -> None:
        """Bind the adapter to a caller-owned artifact root."""
        if not isinstance(root, Path):
            raise TypeError("root must be a pathlib.Path")
        self._root = root

    def artifact_path(self, digest: ContentDigest) -> Path:
        """Resolve the stable path used for a validated SHA-256 digest."""
        return self._root / "sha256" / digest.value[:2] / digest.value[2:]

    def persist(self, content: bytes, digest: ContentDigest) -> ArtifactWriteState:
        """Atomically create or repair bytes after verifying their declared digest.

        Raises:
            ArtifactIntegrityError: If supplied bytes do not match the digest.
            ArtifactPersistenceError: If the filesystem operation cannot finish safely.
        """
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")
        if not isinstance(digest, ContentDigest):
            raise TypeError("digest must be a ContentDigest")
        if sha256(content).hexdigest() != digest.value:
            raise ArtifactIntegrityError()

        path = self.artifact_path(digest)
        state = ArtifactWriteState.CREATED
        try:
            existing = self.retrieve(digest)
        except ArtifactNotFoundError:
            pass
        except ArtifactIntegrityError:
            state = ArtifactWriteState.REPAIRED
        else:
            if existing == content:
                return ArtifactWriteState.UNCHANGED
            raise ArtifactIntegrityError()

        self._replace_atomically(path, content)
        if self.retrieve(digest) != content:
            raise ArtifactIntegrityError()
        return state

    def retrieve(self, digest: ContentDigest) -> bytes:
        """Read exact bytes while rejecting absence and checksum mismatch.

        Raises:
            ArtifactNotFoundError: If no artifact exists for the digest.
            ArtifactIntegrityError: If stored bytes do not match the digest.
            ArtifactPersistenceError: If the filesystem read cannot complete safely.
        """
        if not isinstance(digest, ContentDigest):
            raise TypeError("digest must be a ContentDigest")
        try:
            content = self.artifact_path(digest).read_bytes()
        except FileNotFoundError as error:
            raise ArtifactNotFoundError() from error
        except OSError as error:
            raise ArtifactPersistenceError() from error
        if sha256(content).hexdigest() != digest.value:
            raise ArtifactIntegrityError()
        return content

    @staticmethod
    def _replace_atomically(path: Path, content: bytes) -> None:
        """Durably replace one artifact without exposing a partial target file."""
        temporary_path: Path | None = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(prefix=".artifact-", dir=path.parent)
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "wb") as temporary_file:
                temporary_file.write(content)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, path)
            temporary_path = None
            directory_descriptor = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
        except OSError as error:
            raise ArtifactPersistenceError() from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
