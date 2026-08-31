"""Stable application errors for the authenticated product contract."""

from __future__ import annotations

from contour.services.error import ApplicationError


class IdempotencyConflictError(ApplicationError):
    """Raised when a replay key is reused with a different request payload."""

    def __init__(self) -> None:
        """Create a conflict that does not disclose the original request."""
        super().__init__(
            code="request.idempotency_conflict",
            message="The idempotency key was already used for a different request.",
        )


class SourceAlreadyRegisteredError(ApplicationError):
    """Raised when one workspace already has the requested logical source."""

    def __init__(self) -> None:
        """Create a source-neutral duplicate registration outcome."""
        super().__init__(
            code="source.already_registered",
            message="The source is already registered in this workspace.",
        )


class UnsupportedConnectorError(ApplicationError):
    """Raised when a connector kind has not been admitted by this deployment."""

    def __init__(self) -> None:
        """Create a safe unsupported connector outcome."""
        super().__init__(
            code="source.unsupported_connector",
            message="The requested connector kind is not supported.",
        )


class UnauthenticatedError(ApplicationError):
    """Raised when a product request has no valid bearer credential."""

    def __init__(self) -> None:
        """Create a credential-safe authentication outcome."""
        super().__init__(code="auth.unauthenticated", message="Authentication is required.")
