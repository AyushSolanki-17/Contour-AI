"""Framework-independent Phase 0 records and lifecycle invariants."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from contour.domain.identifiers import (
    EntityId,
    EvidenceId,
    JobId,
    RelationshipId,
    RunId,
    SourceId,
    WorkspaceId,
)
from contour.domain.time import TimePoint

JobStatus = Literal["requested", "queued", "running", "succeeded", "failed", "cancelled"]
RunStatus = Literal["pending", "running", "succeeded", "failed", "cancelled"]


def _require_text(value: str, *, field_name: str) -> str:
    """Validate a required human- or provider-owned text field."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty text without surrounding whitespace")
    return value


def _require_evidence_ids(value: tuple[EvidenceId, ...]) -> tuple[EvidenceId, ...]:
    """Require at least one typed evidence attachment."""
    if not isinstance(value, tuple) or not value:
        raise ValueError("evidence_ids must contain at least one EvidenceId")
    if any(not isinstance(item, EvidenceId) for item in value):
        raise TypeError("evidence_ids must contain only EvidenceId values")
    if len(set(value)) != len(value):
        raise ValueError("evidence_ids must not contain duplicates")
    return value


@dataclass(frozen=True, slots=True)
class Workspace:
    """The isolated scope in which sources and derived knowledge are admitted."""

    id: WorkspaceId
    name: str
    owner: str
    settings: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Validate workspace identity and stable configuration values."""
        if not isinstance(self.id, WorkspaceId):
            raise TypeError("id must be a WorkspaceId")
        _require_text(self.name, field_name="name")
        _require_text(self.owner, field_name="owner")
        if not isinstance(self.settings, tuple):
            raise TypeError("settings must be a tuple of key/value pairs")
        for key, value in self.settings:
            _require_text(key, field_name="settings key")
            _require_text(value, field_name="settings value")


@dataclass(frozen=True, slots=True)
class Source:
    """A stable logical origin without mutable latest content."""

    id: SourceId
    workspace_id: WorkspaceId
    canonical_locator: str
    source_type: str
    scope: str
    license: str | None
    data_classification: str

    def __post_init__(self) -> None:
        """Validate source ownership and explicit metadata values."""
        if not isinstance(self.id, SourceId):
            raise TypeError("id must be a SourceId")
        if not isinstance(self.workspace_id, WorkspaceId):
            raise TypeError("workspace_id must be a WorkspaceId")
        for field_name in ("canonical_locator", "source_type", "scope", "data_classification"):
            _require_text(getattr(self, field_name), field_name=field_name)
        if self.license is not None:
            _require_text(self.license, field_name="license")


@dataclass(frozen=True, slots=True)
class Entity:
    """A namespaced entity assertion backed by exact evidence."""

    id: EntityId
    workspace_id: WorkspaceId
    label: str
    evidence_ids: tuple[EvidenceId, ...]
    valid_time: TimePoint
    transaction_time: TimePoint

    def __post_init__(self) -> None:
        """Reject unsupported identity, evidence, or temporal values."""
        if not isinstance(self.id, EntityId):
            raise TypeError("id must be an EntityId")
        if not isinstance(self.workspace_id, WorkspaceId):
            raise TypeError("workspace_id must be a WorkspaceId")
        _require_text(self.label, field_name="label")
        _require_evidence_ids(self.evidence_ids)
        if not isinstance(self.valid_time, TimePoint):
            raise TypeError("valid_time must be a TimePoint")
        if not isinstance(self.transaction_time, TimePoint):
            raise TypeError("transaction_time must be a TimePoint")


@dataclass(frozen=True, slots=True)
class Relationship:
    """A typed, directed relationship whose edge retains its evidence."""

    id: RelationshipId
    workspace_id: WorkspaceId
    from_entity: EntityId
    relationship_type: str
    to_entity: EntityId
    evidence_ids: tuple[EvidenceId, ...]
    valid_time: TimePoint
    transaction_time: TimePoint

    def __post_init__(self) -> None:
        """Reject mixed endpoints, empty relationship types, and missing evidence."""
        if not isinstance(self.id, RelationshipId):
            raise TypeError("id must be a RelationshipId")
        if not isinstance(self.workspace_id, WorkspaceId):
            raise TypeError("workspace_id must be a WorkspaceId")
        if not isinstance(self.from_entity, EntityId):
            raise TypeError("from_entity must be an EntityId")
        if not isinstance(self.to_entity, EntityId):
            raise TypeError("to_entity must be an EntityId")
        _require_text(self.relationship_type, field_name="relationship_type")
        _require_evidence_ids(self.evidence_ids)
        if not isinstance(self.valid_time, TimePoint):
            raise TypeError("valid_time must be a TimePoint")
        if not isinstance(self.transaction_time, TimePoint):
            raise TypeError("transaction_time must be a TimePoint")


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
        _require_text(self.kind, field_name="kind")
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
