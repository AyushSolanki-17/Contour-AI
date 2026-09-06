"""Transaction contract for atomic job and execution-attempt recording."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from contour.jobs.domain.job import Job, JobId
from contour.jobs.domain.run import Run, RunId
from contour.tenancy.domain.access import AccessContext


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


class JobRepository(Protocol):
    """Persists requested work separately from its execution attempts."""

    def get_job(self, access: AccessContext, job_id: JobId) -> Job | None:
        """Return a durable job by stable identity, if present."""

    def save_job(self, access: AccessContext, job: Job) -> None:
        """Insert one durable job request without overwriting a prior request."""


class RunRepository(Protocol):
    """Persists distinct attempts for a single requested job."""

    def get_run(self, access: AccessContext, run_id: RunId) -> Run | None:
        """Return a run attempt by stable identity, if present."""

    def save_run(self, access: AccessContext, run: Run) -> None:
        """Insert one execution attempt that refers to an existing durable job."""
