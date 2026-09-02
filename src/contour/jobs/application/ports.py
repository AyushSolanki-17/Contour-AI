"""Transaction contract for atomic job and execution-attempt recording."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from contour.jobs.application.job_store import JobRepository
from contour.jobs.application.run_store import RunRepository


class JobUnitOfWork(Protocol):
    """Provide job repositories bound to one atomic operation."""

    @property
    def jobs(self) -> JobRepository:
        """Return the requested-work repository bound to this transaction."""

    @property
    def runs(self) -> RunRepository:
        """Return the job-run repository bound to this transaction."""

    def __enter__(self) -> Self:
        """Begin the transaction and return its repositories."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit on success or discard all job writes on failure."""


class JobTransactionManager(Protocol):
    """Create one explicit atomic boundary for job and run recording."""

    def transaction(self) -> JobUnitOfWork:
        """Return a fresh job transaction."""
