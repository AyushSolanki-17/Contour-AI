"""SQLAlchemy Core tables for durable execution requests and attempts."""

from __future__ import annotations

import sqlalchemy as sa

from contour.infrastructure.postgres.tables.catalog import workspaces
from contour.infrastructure.postgres.tables.metadata import metadata

jobs = sa.Table(
    "jobs",
    metadata,
    sa.Column("namespace", sa.Text(), nullable=False),
    sa.Column("value", sa.Text(), nullable=False),
    sa.Column("tenant_namespace", sa.Text(), nullable=False),
    sa.Column("tenant_value", sa.Text(), nullable=False),
    sa.Column("workspace_namespace", sa.Text(), nullable=False),
    sa.Column("workspace_value", sa.Text(), nullable=False),
    sa.Column("kind", sa.Text(), nullable=False),
    sa.Column("requested_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("status", sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint("namespace", "value", name="pk_jobs"),
    sa.UniqueConstraint(
        "namespace",
        "value",
        "workspace_namespace",
        "workspace_value",
        "tenant_namespace",
        "tenant_value",
        name="uq_jobs_ownership",
    ),
    sa.ForeignKeyConstraint(
        ["workspace_namespace", "workspace_value"],
        ["workspaces.namespace", "workspaces.value"],
        name="fk_jobs_workspace",
    ),
    sa.ForeignKeyConstraint(
        ["workspace_namespace", "workspace_value", "tenant_namespace", "tenant_value"],
        [
            "workspaces.namespace",
            "workspaces.value",
            "workspaces.tenant_namespace",
            "workspaces.tenant_value",
        ],
        name="fk_jobs_workspace_ownership",
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
    sa.Column("tenant_namespace", sa.Text(), nullable=False),
    sa.Column("tenant_value", sa.Text(), nullable=False),
    sa.Column("workspace_namespace", sa.Text(), nullable=False),
    sa.Column("workspace_value", sa.Text(), nullable=False),
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
    sa.ForeignKeyConstraint(
        [
            "job_namespace",
            "job_value",
            "workspace_namespace",
            "workspace_value",
            "tenant_namespace",
            "tenant_value",
        ],
        [
            "jobs.namespace",
            "jobs.value",
            "jobs.workspace_namespace",
            "jobs.workspace_value",
            "jobs.tenant_namespace",
            "jobs.tenant_value",
        ],
        name="fk_runs_job_ownership",
    ),
    sa.CheckConstraint(
        "status IN ('pending', 'running', 'succeeded', 'failed', 'cancelled')",
        name="ck_runs_status",
    ),
)

assert workspaces.metadata is metadata
