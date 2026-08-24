"""Transaction contracts for durable knowledge and execution records."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from contour.repositories.entity import EntityRepository
from contour.repositories.job import JobRepository
from contour.repositories.relationship import RelationshipRepository
from contour.repositories.run import RunRepository


class RecordUnitOfWork(Protocol):
    """Provides knowledge and execution repositories for one atomic operation."""

    @property
    def entities(self) -> EntityRepository:
        """Return the entity repository bound to this transaction."""

    @property
    def relationships(self) -> RelationshipRepository:
        """Return the relationship repository bound to this transaction."""

    @property
    def jobs(self) -> JobRepository:
        """Return the requested-work repository bound to this transaction."""

    @property
    def runs(self) -> RunRepository:
        """Return the execution-attempt repository bound to this transaction."""

    def __enter__(self) -> Self:
        """Begin the transaction and return its repositories."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit on success or discard all record writes on failure."""


class RecordTransactionManager(Protocol):
    """Creates one explicit atomic boundary for knowledge and execution writes."""

    def transaction(self) -> RecordUnitOfWork:
        """Return a fresh transaction scope."""
