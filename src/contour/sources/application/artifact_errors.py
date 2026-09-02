"""Stable application errors for content-addressed artifact failures."""

from __future__ import annotations

from contour.errors import ApplicationError


class ArtifactNotFoundError(ApplicationError):
    """Raised when a requested content-addressed artifact is absent."""

    def __init__(self) -> None:
        """Create a safe missing-artifact error."""
        super().__init__(
            code="artifact.not_found",
            message="The content-addressed artifact is unavailable.",
        )


class ArtifactIntegrityError(ApplicationError):
    """Raised when supplied or stored bytes do not match their address."""

    def __init__(self) -> None:
        """Create a safe checksum error without exposing content or paths."""
        super().__init__(
            code="artifact.integrity_failed",
            message="The content-addressed artifact failed its integrity check.",
        )


class ArtifactPersistenceError(ApplicationError):
    """Raised when artifact I/O cannot complete safely."""

    def __init__(self) -> None:
        """Create a safe artifact persistence error."""
        super().__init__(
            code="artifact.persistence_failed",
            message="The content-addressed artifact could not be persisted safely.",
        )
