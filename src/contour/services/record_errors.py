"""Stable application errors for knowledge and execution persistence."""

from __future__ import annotations

from contour.services.error import ApplicationError


class RecordConflictError(ApplicationError):
    """Raised when a durable record conflicts with an accepted identity."""

    def __init__(self) -> None:
        """Create a conflict error without leaking persistence details."""
        super().__init__(
            code="records.conflict",
            message="A knowledge or execution record conflicts with an accepted record.",
        )


class RecordReferenceError(ApplicationError):
    """Raised when a record refers to an unavailable durable record."""

    def __init__(self) -> None:
        """Create an invalid-reference error without leaking persistence details."""
        super().__init__(
            code="records.invalid_reference",
            message="A knowledge or execution record references an unavailable record.",
        )


class RecordPersistenceError(ApplicationError):
    """Raised when an unclassified persistence failure prevents safe acceptance."""

    def __init__(self) -> None:
        """Create a generic persistence error that does not expose database details."""
        super().__init__(
            code="records.persistence_failed",
            message="Knowledge or execution records could not be persisted safely.",
        )
