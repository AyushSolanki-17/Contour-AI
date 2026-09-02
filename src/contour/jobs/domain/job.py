"""Durable requested-work record and its identity."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from contour.identifiers import require_identifier_value, require_namespace
from contour.tenancy.domain.tenant import TenantId
from contour.time import TimePoint
from contour.validation import require_text
from contour.workspaces.domain.workspace import WorkspaceId

JobStatus = Literal["requested", "queued", "running", "succeeded", "failed", "cancelled"]


@dataclass(frozen=True, slots=True)
class JobId:
    """A stable identifier for one requested unit of work."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed job identity components."""
        object.__setattr__(self, "namespace", require_namespace(self.namespace))
        object.__setattr__(self, "value", require_identifier_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized job identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class Job:
    """A durable request for work, distinct from each execution attempt."""

    id: JobId
    tenant_id: TenantId
    workspace_id: WorkspaceId
    kind: str
    requested_at: TimePoint
    status: JobStatus = "requested"

    def __post_init__(self) -> None:
        """Validate job identity, request time, and lifecycle state."""
        if not isinstance(self.id, JobId):
            raise TypeError("id must be a JobId")
        if not isinstance(self.tenant_id, TenantId):
            raise TypeError("tenant_id must be a TenantId")
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
