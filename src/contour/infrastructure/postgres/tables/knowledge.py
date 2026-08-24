"""SQLAlchemy Core tables for evidence-backed knowledge and execution records."""

from __future__ import annotations

import sqlalchemy as sa

from contour.infrastructure.postgres.tables.catalog import evidence, workspaces
from contour.infrastructure.postgres.tables.metadata import metadata

entities = sa.Table(
    "entities",
    metadata,
    sa.Column("namespace", sa.Text(), nullable=False),
    sa.Column("value", sa.Text(), nullable=False),
    sa.Column("workspace_namespace", sa.Text(), nullable=False),
    sa.Column("workspace_value", sa.Text(), nullable=False),
    sa.Column("label", sa.Text(), nullable=False),
    sa.Column("valid_time", sa.DateTime(timezone=True), nullable=True),
    sa.Column("transaction_time", sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint("namespace", "value", name="pk_entities"),
    sa.ForeignKeyConstraint(
        ["workspace_namespace", "workspace_value"],
        ["workspaces.namespace", "workspaces.value"],
        name="fk_entities_workspace",
    ),
)

entity_evidence = sa.Table(
    "entity_evidence",
    metadata,
    sa.Column("entity_namespace", sa.Text(), nullable=False),
    sa.Column("entity_value", sa.Text(), nullable=False),
    sa.Column("position", sa.SmallInteger(), nullable=False),
    sa.Column("evidence_namespace", sa.Text(), nullable=False),
    sa.Column("evidence_value", sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint(
        "entity_namespace", "entity_value", "position", name="pk_entity_evidence"
    ),
    sa.UniqueConstraint(
        "entity_namespace",
        "entity_value",
        "evidence_namespace",
        "evidence_value",
        name="uq_entity_evidence_attachment",
    ),
    sa.ForeignKeyConstraint(
        ["entity_namespace", "entity_value"],
        ["entities.namespace", "entities.value"],
        name="fk_entity_evidence_entity",
    ),
    sa.ForeignKeyConstraint(
        ["evidence_namespace", "evidence_value"],
        ["evidence.namespace", "evidence.value"],
        name="fk_entity_evidence_evidence",
    ),
    sa.CheckConstraint("position >= 0", name="ck_entity_evidence_position"),
)

relationships = sa.Table(
    "relationships",
    metadata,
    sa.Column("namespace", sa.Text(), nullable=False),
    sa.Column("value", sa.Text(), nullable=False),
    sa.Column("workspace_namespace", sa.Text(), nullable=False),
    sa.Column("workspace_value", sa.Text(), nullable=False),
    sa.Column("from_namespace", sa.Text(), nullable=False),
    sa.Column("from_value", sa.Text(), nullable=False),
    sa.Column("relationship_type", sa.Text(), nullable=False),
    sa.Column("to_namespace", sa.Text(), nullable=False),
    sa.Column("to_value", sa.Text(), nullable=False),
    sa.Column("primary_evidence_namespace", sa.Text(), nullable=False),
    sa.Column("primary_evidence_value", sa.Text(), nullable=False),
    sa.Column("valid_time", sa.DateTime(timezone=True), nullable=True),
    sa.Column("transaction_time", sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint("namespace", "value", name="pk_relationships"),
    sa.ForeignKeyConstraint(
        ["workspace_namespace", "workspace_value"],
        ["workspaces.namespace", "workspaces.value"],
        name="fk_relationships_workspace",
    ),
    sa.ForeignKeyConstraint(
        ["from_namespace", "from_value"],
        ["entities.namespace", "entities.value"],
        name="fk_relationships_from_entity",
    ),
    sa.ForeignKeyConstraint(
        ["to_namespace", "to_value"],
        ["entities.namespace", "entities.value"],
        name="fk_relationships_to_entity",
    ),
    sa.ForeignKeyConstraint(
        ["primary_evidence_namespace", "primary_evidence_value"],
        ["evidence.namespace", "evidence.value"],
        name="fk_relationships_primary_evidence",
    ),
)

relationship_evidence = sa.Table(
    "relationship_evidence",
    metadata,
    sa.Column("relationship_namespace", sa.Text(), nullable=False),
    sa.Column("relationship_value", sa.Text(), nullable=False),
    sa.Column("position", sa.SmallInteger(), nullable=False),
    sa.Column("evidence_namespace", sa.Text(), nullable=False),
    sa.Column("evidence_value", sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint(
        "relationship_namespace", "relationship_value", "position", name="pk_relationship_evidence"
    ),
    sa.UniqueConstraint(
        "relationship_namespace",
        "relationship_value",
        "evidence_namespace",
        "evidence_value",
        name="uq_relationship_evidence_attachment",
    ),
    sa.ForeignKeyConstraint(
        ["relationship_namespace", "relationship_value"],
        ["relationships.namespace", "relationships.value"],
        name="fk_relationship_evidence_relationship",
    ),
    sa.ForeignKeyConstraint(
        ["evidence_namespace", "evidence_value"],
        ["evidence.namespace", "evidence.value"],
        name="fk_relationship_evidence_evidence",
    ),
    sa.CheckConstraint("position >= 0", name="ck_relationship_evidence_position"),
)

jobs = sa.Table(
    "jobs",
    metadata,
    sa.Column("namespace", sa.Text(), nullable=False),
    sa.Column("value", sa.Text(), nullable=False),
    sa.Column("workspace_namespace", sa.Text(), nullable=False),
    sa.Column("workspace_value", sa.Text(), nullable=False),
    sa.Column("kind", sa.Text(), nullable=False),
    sa.Column("requested_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("status", sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint("namespace", "value", name="pk_jobs"),
    sa.ForeignKeyConstraint(
        ["workspace_namespace", "workspace_value"],
        ["workspaces.namespace", "workspaces.value"],
        name="fk_jobs_workspace",
    ),
    sa.CheckConstraint(
        "status IN ('requested', 'queued', 'running', 'succeeded', 'failed', 'cancelled')",
        name="ck_jobs_status",
    ),
)

runs = sa.Table(
    "runs",
    metadata,
    sa.Column("namespace", sa.Text(), nullable=False),
    sa.Column("value", sa.Text(), nullable=False),
    sa.Column("job_namespace", sa.Text(), nullable=False),
    sa.Column("job_value", sa.Text(), nullable=False),
    sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("status", sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint("namespace", "value", name="pk_runs"),
    sa.ForeignKeyConstraint(
        ["job_namespace", "job_value"],
        ["jobs.namespace", "jobs.value"],
        name="fk_runs_job",
    ),
    sa.CheckConstraint(
        "status IN ('pending', 'running', 'succeeded', 'failed', 'cancelled')",
        name="ck_runs_status",
    ),
)

# Keep imports of prerequisite tables explicit: these foreign keys document the durable lineage.
assert evidence.metadata is metadata
assert workspaces.metadata is metadata
