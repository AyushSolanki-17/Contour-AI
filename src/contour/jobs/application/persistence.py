"""Application orchestration for durable jobs and job runs."""

from __future__ import annotations

from collections.abc import Sequence

from contour.errors import ResourceNotFoundError
from contour.jobs.application.ports import JobTransactionManager
from contour.jobs.domain.job import Job
from contour.jobs.domain.run import Run
from contour.tenancy.domain.access import AccessContext


class JobPersistenceService:
    """Record one requested job and its supplied runs atomically."""

    def __init__(self, transactions: JobTransactionManager) -> None:
        """Initialize the service with the job transaction boundary."""
        self._transactions = transactions

    def record(self, *, access: AccessContext, job: Job, runs: Sequence[Run]) -> None:
        """Persist a job and attempts that share its verified owner and identity.

        Raises:
            ResourceNotFoundError: If the scope or attempts do not share the requested job.
        """
        if any(run.job_id != job.id for run in runs):
            raise ResourceNotFoundError()
        if not access.permits(job.tenant_id):
            raise ResourceNotFoundError()
        if any(
            run.tenant_id != job.tenant_id or run.workspace_id != job.workspace_id for run in runs
        ):
            raise ResourceNotFoundError()

        with self._transactions.transaction() as transaction:
            transaction.jobs.save_job(access, job)
            for run in runs:
                transaction.runs.save_run(access, run)
