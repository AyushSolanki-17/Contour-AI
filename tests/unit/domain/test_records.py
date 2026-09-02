"""Contracts for Phase 0 records, evidence attachments, and execution state."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from contour.jobs.domain.job import Job, JobId
from contour.jobs.domain.run import Run, RunId
from contour.knowledge.domain.entity import Entity, EntityId
from contour.knowledge.domain.evidence import EvidenceId
from contour.knowledge.domain.relationship import Relationship, RelationshipId
from contour.sources.domain.source import SourceId
from contour.tenancy.domain.tenant import TenantId
from contour.time import TimePoint
from contour.workspaces.domain.workspace import Workspace, WorkspaceId


def workspace_id() -> WorkspaceId:
    """Return a valid test workspace identity."""
    return WorkspaceId("WORKSPACE", "test")


def tenant_id() -> TenantId:
    """Return a valid tenant identity for ownership-bound records."""
    return TenantId("TENANT", "test")


def evidence_id(value: str = "e-1") -> EvidenceId:
    """Return a valid test evidence identity."""
    return EvidenceId("EVIDENCE", value)


def test_records_require_typed_identity_and_edge_evidence() -> None:
    workspace = Workspace(workspace_id(), tenant_id(), "Test workspace", "maintainer")
    entity_a = Entity(
        id=EntityId("PEP", "723"),
        tenant_id=workspace.tenant_id,
        workspace_id=workspace.id,
        label="PEP 723",
        evidence_ids=(evidence_id(),),
        valid_time=TimePoint.unknown(),
        transaction_time=TimePoint(datetime(2026, 8, 20, tzinfo=UTC)),
    )
    entity_b = Entity(
        id=EntityId("PYTHON", "3.14"),
        tenant_id=workspace.tenant_id,
        workspace_id=workspace.id,
        label="Python 3.14",
        evidence_ids=(evidence_id("e-2"),),
        valid_time=TimePoint.unknown(),
        transaction_time=TimePoint.unknown(),
    )

    relationship = Relationship(
        id=RelationshipId("REL", "723-replaces-722"),
        tenant_id=workspace.tenant_id,
        workspace_id=workspace.id,
        from_entity=entity_a.id,
        relationship_type="replaces",
        to_entity=entity_b.id,
        evidence_ids=(evidence_id(),),
        valid_time=TimePoint.unknown(),
        transaction_time=TimePoint.unknown(),
    )

    assert relationship.evidence_ids == (evidence_id(),)
    assert not entity_a.valid_time.is_known
    assert entity_a.transaction_time.is_known

    assert relationship.to_entity == EntityId("PYTHON", "3.14")

    with pytest.raises(TypeError, match="from_entity"):
        Relationship(
            id=relationship.id,
            tenant_id=workspace.tenant_id,
            workspace_id=workspace.id,
            from_entity=SourceId("SOURCE:PEP", "723"),  # type: ignore[arg-type]
            relationship_type="replaces",
            to_entity=entity_b.id,
            evidence_ids=(evidence_id(),),
            valid_time=TimePoint.unknown(),
            transaction_time=TimePoint.unknown(),
        )

    with pytest.raises(ValueError, match="at least one"):
        Relationship(
            id=relationship.id,
            tenant_id=workspace.tenant_id,
            workspace_id=workspace.id,
            from_entity=entity_a.id,
            relationship_type="replaces",
            to_entity=entity_b.id,
            evidence_ids=(),
            valid_time=TimePoint.unknown(),
            transaction_time=TimePoint.unknown(),
        )


def test_job_and_run_preserve_requested_work_and_attempt_lifecycles() -> None:
    job = Job(JobId("JOB", "j-1"), tenant_id(), workspace_id(), "ingest", TimePoint.unknown())
    queued = job.queue()
    running = queued.start()
    run = Run(
        RunId("RUN", "r-1"), tenant_id(), workspace_id(), running.id, TimePoint.unknown()
    ).start()

    assert running.finish(succeeded=False).status == "failed"
    assert run.finish(succeeded=True).status == "succeeded"
    assert job.status == "requested"
    assert queued.status == "queued"

    with pytest.raises(ValueError, match="running"):
        job.finish(succeeded=True)
