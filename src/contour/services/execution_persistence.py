"""Application orchestration for durable jobs and execution attempts."""

from __future__ import annotations

from collections.abc import Sequence

from contour.domain.access import AccessContext
from contour.domain.job import Job
from contour.domain.run import Run
from contour.repositories.execution_transaction import ExecutionTransactionManager
from contour.services.resource_errors import ResourceNotFoundError


class ExecutionPersistenceService:
    """Record one requested job and its supplied execution attempts atomically."""

    def __init__(self, transactions: ExecutionTransactionManager) -> None:
        """Initialize the service with the execution transaction boundary."""
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
