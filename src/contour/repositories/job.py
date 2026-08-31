"""Persistence contract for durable requested work."""

from __future__ import annotations

from typing import Protocol

from contour.domain.access import AccessContext
from contour.domain.job import Job, JobId


class JobRepository(Protocol):
    """Persists requested work separately from its execution attempts."""

    def get_job(self, access: AccessContext, job_id: JobId) -> Job | None:
        """Return a durable job by stable identity, if present."""

    def save_job(self, access: AccessContext, job: Job) -> None:
        """Insert one durable job request without overwriting a prior request."""
