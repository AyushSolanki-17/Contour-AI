"""Persistence contract for durable job execution attempts."""

from __future__ import annotations

from typing import Protocol

from contour.jobs.domain.run import Run, RunId
from contour.tenancy.domain.access import AccessContext


class RunRepository(Protocol):
    """Persists distinct attempts for a single requested job."""

    def get_run(self, access: AccessContext, run_id: RunId) -> Run | None:
        """Return a run attempt by stable identity, if present."""

    def save_run(self, access: AccessContext, run: Run) -> None:
        """Insert one execution attempt that refers to an existing durable job."""
