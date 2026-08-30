"""Durable execution-attempt record and its identity."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from contour.domain.identifier_validation import require_identifier_value, require_namespace
from contour.domain.job import JobId
from contour.domain.tenant import TenantId
from contour.domain.time_point import TimePoint
from contour.domain.workspace import WorkspaceId

RunStatus = Literal["pending", "running", "succeeded", "failed", "cancelled"]


@dataclass(frozen=True, slots=True)
class RunId:
    """A stable identifier for one execution attempt of a requested job."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed run identity components."""
        object.__setattr__(self, "namespace", require_namespace(self.namespace))
        object.__setattr__(self, "value", require_identifier_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized run identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class Run:
    """One execution attempt linked to exactly one requested job."""

    id: RunId
    tenant_id: TenantId
    workspace_id: WorkspaceId
    job_id: JobId
    started_at: TimePoint
    status: RunStatus = "pending"

    def __post_init__(self) -> None:
        """Validate run identity, job linkage, and lifecycle state."""
        if not isinstance(self.id, RunId):
            raise TypeError("id must be a RunId")
        if not isinstance(self.tenant_id, TenantId):
            raise TypeError("tenant_id must be a TenantId")
        if not isinstance(self.workspace_id, WorkspaceId):
            raise TypeError("workspace_id must be a WorkspaceId")
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
