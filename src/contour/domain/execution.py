"""Framework-independent durable job and execution-attempt records."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from contour.domain._validation import require_text
from contour.domain.identifiers import JobId, RunId, WorkspaceId
from contour.domain.time import TimePoint

JobStatus = Literal["requested", "queued", "running", "succeeded", "failed", "cancelled"]
RunStatus = Literal["pending", "running", "succeeded", "failed", "cancelled"]


@dataclass(frozen=True, slots=True)
class Job:
    """A durable request for work, distinct from each execution attempt."""

    id: JobId
    workspace_id: WorkspaceId
    kind: str
    requested_at: TimePoint
    status: JobStatus = "requested"

    def __post_init__(self) -> None:
        """Validate job identity, request time, and lifecycle state."""
        if not isinstance(self.id, JobId):
            raise TypeError("id must be a JobId")
        if not isinstance(self.workspace_id, WorkspaceId):
            raise TypeError("workspace_id must be a WorkspaceId")
        require_text(self.kind, field_name="kind")
        if not isinstance(self.requested_at, TimePoint):
            raise TypeError("requested_at must be a TimePoint")
        if self.status not in {
            "requested",
            "queued",
            "running",
            "succeeded",
            "failed",
            "cancelled",
        }:
            raise ValueError("invalid job status")

    def queue(self) -> Job:
        """Move a newly requested job into the durable queue."""
        if self.status != "requested":
            raise ValueError("only requested jobs can be queued")
        return replace(self, status="queued")

    def start(self) -> Job:
        """Mark a queued job as actively executing."""
        if self.status != "queued":
            raise ValueError("only queued jobs can start")
        return replace(self, status="running")

    def finish(self, *, succeeded: bool) -> Job:
        """Complete a running job successfully or terminally failed.

        Args:
            succeeded: Whether the execution produced an accepted result.
        """
        if self.status != "running":
            raise ValueError("only running jobs can finish")
        return replace(self, status="succeeded" if succeeded else "failed")

    def cancel(self) -> Job:
        """Cancel a job that has not reached a terminal state."""
        if self.status in {"succeeded", "failed", "cancelled"}:
            raise ValueError("terminal jobs cannot be cancelled")
        return replace(self, status="cancelled")


@dataclass(frozen=True, slots=True)
class Run:
    """One execution attempt linked to exactly one requested job."""

    id: RunId
    job_id: JobId
    started_at: TimePoint
    status: RunStatus = "pending"

    def __post_init__(self) -> None:
        """Validate run identity, job linkage, and lifecycle state."""
        if not isinstance(self.id, RunId):
            raise TypeError("id must be a RunId")
        if not isinstance(self.job_id, JobId):
            raise TypeError("job_id must be a JobId")
        if not isinstance(self.started_at, TimePoint):
            raise TypeError("started_at must be a TimePoint")
        if self.status not in {"pending", "running", "succeeded", "failed", "cancelled"}:
            raise ValueError("invalid run status")

    def start(self) -> Run:
        """Move a pending execution attempt into active execution."""
        if self.status != "pending":
            raise ValueError("only pending runs can start")
        return replace(self, status="running")

    def finish(self, *, succeeded: bool) -> Run:
        """Complete a running attempt successfully or terminally failed.

        Args:
            succeeded: Whether this attempt produced an accepted result.
        """
        if self.status != "running":
            raise ValueError("only running runs can finish")
        return replace(self, status="succeeded" if succeeded else "failed")

    def cancel(self) -> Run:
        """Cancel an attempt that has not reached a terminal state."""
        if self.status in {"succeeded", "failed", "cancelled"}:
            raise ValueError("terminal runs cannot be cancelled")
        return replace(self, status="cancelled")
