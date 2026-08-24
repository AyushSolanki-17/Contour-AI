"""Create durable knowledge assertions and execution records.

Revision ID: 20260824_04
Revises: 20260824_03
Create Date: 2026-08-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260824_04"
down_revision: str | Sequence[str] | None = "20260824_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create records that retain evidence attachments and independent run attempts."""
    op.create_table(
        "entities",
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
    op.create_table(
        "entity_evidence",
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
    op.create_table(
        "relationships",
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
    op.create_table(
        "relationship_evidence",
        sa.Column("relationship_namespace", sa.Text(), nullable=False),
        sa.Column("relationship_value", sa.Text(), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column("evidence_namespace", sa.Text(), nullable=False),
        sa.Column("evidence_value", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint(
            "relationship_namespace",
            "relationship_value",
            "position",
            name="pk_relationship_evidence",
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
    op.create_table(
        "jobs",
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
    op.create_table(
        "runs",
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


def downgrade() -> None:
    """Refuse destructive record removal without an explicit recovery procedure."""
    raise NotImplementedError("knowledge and execution record removal is intentionally unsupported")
