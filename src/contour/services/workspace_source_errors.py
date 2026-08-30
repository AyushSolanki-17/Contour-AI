"""Stable application errors for workspace and source product operations."""

from __future__ import annotations

from contour.services.error import ApplicationError


class ResourceNotFoundError(ApplicationError):
    """Raised when a workspace-scoped product resource is unavailable."""

    def __init__(self) -> None:
        """Create a not-found error that does not disclose nearby resources."""
        super().__init__(
            code="resource.not_found",
            message="The requested resource was not found.",
        )


class ResourceConflictError(ApplicationError):
    """Raised when an accepted identity has a different representation."""

    def __init__(self) -> None:
        """Create an identity-conflict error without exposing accepted values."""
        super().__init__(
            code="resource.conflict",
            message="The resource identity conflicts with an accepted resource.",
        )


class UnsupportedSourceError(ApplicationError):
    """Raised when no configured source capability accepts a registration."""

    def __init__(self) -> None:
        """Create a source-support error without leaking adapter internals."""
        super().__init__(
            code="source.unsupported",
            message="The source configuration is not supported.",
        )
