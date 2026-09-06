"""Stable application errors for catalog persistence failures."""

from __future__ import annotations

from contour.errors import ApplicationError


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
