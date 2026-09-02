"""Persistence contract for durable requested work."""

from __future__ import annotations

from typing import Protocol

from contour.jobs.domain.job import Job, JobId
from contour.tenancy.domain.access import AccessContext


class JobRepository(Protocol):
    """Persists requested work separately from its execution attempts."""

    def get_job(self, access: AccessContext, job_id: JobId) -> Job | None:
        """Return a durable job by stable identity, if present."""

    def save_job(self, access: AccessContext, job: Job) -> None:
        """Insert one durable job request without overwriting a prior request."""
