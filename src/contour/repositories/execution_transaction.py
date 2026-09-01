"""Transaction contract for atomic job and execution-attempt recording."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from contour.repositories.job import JobRepository
from contour.repositories.run import RunRepository


class ExecutionUnitOfWork(Protocol):
    """Provide execution repositories bound to one atomic operation."""

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
        """Commit on success or discard all execution writes on failure."""


class ExecutionTransactionManager(Protocol):
    """Create one explicit atomic boundary for job and run recording."""

    def transaction(self) -> ExecutionUnitOfWork:
        """Return a fresh execution transaction."""
