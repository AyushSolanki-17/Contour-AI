"""Stable application errors for catalog persistence failures."""

from __future__ import annotations

from contour.errors import ApplicationError


class CatalogConflictError(ApplicationError):
    """Raised when catalog identity conflicts with an accepted record."""

    def __init__(self) -> None:
        """Create a conflict error without leaking persistence details."""
        super().__init__(
            code="catalog.conflict",
            message="A catalog record conflicts with an accepted record.",
        )


class CatalogReferenceError(ApplicationError):
    """Raised when a catalog record refers to a record that does not exist."""

    def __init__(self) -> None:
        """Create an invalid-reference error without leaking persistence details."""
        super().__init__(
            code="catalog.invalid_reference",
            message="A catalog record references an unavailable record.",
        )


class CatalogPersistenceError(ApplicationError):
    """Raised when catalog integrity fails for an unclassified reason."""

    def __init__(self) -> None:
        """Create a safe generic catalog persistence error."""
        super().__init__(
            code="catalog.persistence_failed",
            message="Catalog records could not be persisted safely.",
        )


class IdempotencyConflictError(ApplicationError):
    """Raised when an operation key is reused with different input."""

    def __init__(self) -> None:
        """Create a conflict that does not disclose the original input."""
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
