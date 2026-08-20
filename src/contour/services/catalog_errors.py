"""Stable application errors for catalog persistence failures."""

from __future__ import annotations

from contour.services.error import ApplicationError


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
