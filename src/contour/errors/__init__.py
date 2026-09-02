"""Stable cross-capability errors exposed at application boundaries."""

from contour.errors.application import ApplicationError
from contour.errors.records import (
    RecordConflictError,
    RecordPersistenceError,
    RecordReferenceError,
)
from contour.errors.resource import ResourceNotFoundError

__all__ = (
    "ApplicationError",
    "RecordConflictError",
    "RecordPersistenceError",
    "RecordReferenceError",
    "ResourceNotFoundError",
)
