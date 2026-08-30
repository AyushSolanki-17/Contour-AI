"""Bind all durable records to a tenant-owned workspace.

Revision ID: 20260830_06
Revises: 20260825_05
Create Date: 2026-08-30

Legacy databases predate Tenant identity.  Their accepted records are assigned
atomically to the one explicit ``LEGACY:default`` tenant; no source, content,
or evidence metadata is rewritten.  If this revision fails, PostgreSQL rolls
back its transactional DDL and data updates, so retrying ``alembic upgrade
head`` is the recovery path.  Downgrade is intentionally unsupported because
removing ownership columns would destroy the security boundary.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260830_06"
down_revision: str | Sequence[str] | None = "20260825_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TENANT_NAMESPACE = "LEGACY"
_TENANT_VALUE = "default"


def upgrade() -> None:
    """Add tenant ownership, backfill legacy rows, and enforce composite lineage."""
    op.create_table(
        "tenants",
        sa.Column("namespace", sa.Text(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("namespace", "value", name="pk_tenants"),
    )
    op.bulk_insert(
        sa.table(
            "tenants",
            sa.column("namespace", sa.Text()),
            sa.column("value", sa.Text()),
            sa.column("name", sa.Text()),
        ),
        [{"namespace": _TENANT_NAMESPACE, "value": _TENANT_VALUE, "name": "Legacy tenant"}],
    )

    _add_ownership_columns("workspaces", workspace=False)
    _add_ownership_columns("sources", workspace=False)
    _add_ownership_columns("source_versions", workspace=True)
    _add_ownership_columns("evidence", workspace=True)
    _add_ownership_columns("entities", workspace=False)
    _add_ownership_columns("entity_evidence", workspace=True)
    _add_ownership_columns("relationships", workspace=False)
    _add_ownership_columns("relationship_evidence", workspace=True)
    _add_ownership_columns("jobs", workspace=False)
    _add_ownership_columns("runs", workspace=True)

    _backfill_ownership()
    _require_ownership_columns()
    _create_ownership_constraints()


def _add_ownership_columns(table_name: str, *, workspace: bool) -> None:
    """Add nullable ownership columns before their data backfill."""
    op.add_column(table_name, sa.Column("tenant_namespace", sa.Text(), nullable=True))
    op.add_column(table_name, sa.Column("tenant_value", sa.Text(), nullable=True))
    if workspace:
        op.add_column(table_name, sa.Column("workspace_namespace", sa.Text(), nullable=True))
        op.add_column(table_name, sa.Column("workspace_value", sa.Text(), nullable=True))


def _backfill_ownership() -> None:
    """Derive every legacy tuple from its pre-existing workspace lineage."""
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE workspaces SET tenant_namespace = :namespace, tenant_value = :value"
        ).bindparams(namespace=_TENANT_NAMESPACE, value=_TENANT_VALUE)
    )
    bind.execute(
        sa.text(
            "UPDATE sources AS record SET tenant_namespace = workspace.tenant_namespace, "
            "tenant_value = workspace.tenant_value FROM workspaces AS workspace "
            "WHERE record.workspace_namespace = workspace.namespace "
            "AND record.workspace_value = workspace.value"
        )
    )
    bind.execute(
        sa.text(
            "UPDATE source_versions AS record SET "
            "tenant_namespace = source.tenant_namespace, tenant_value = source.tenant_value, "
            "workspace_namespace = source.workspace_namespace, "
            "workspace_value = source.workspace_value FROM sources AS source "
            "WHERE record.source_namespace = source.namespace AND record.source_value = source.value"
        )
    )
    bind.execute(
        sa.text(
            "UPDATE evidence AS record SET "
            "tenant_namespace = version.tenant_namespace, tenant_value = version.tenant_value, "
            "workspace_namespace = version.workspace_namespace, "
            "workspace_value = version.workspace_value FROM source_versions AS version "
            "WHERE record.source_namespace = version.source_namespace "
            "AND record.source_value = version.source_value "
            "AND record.content_digest = version.content_digest"
        )
    )
    for table_name in ("entities", "relationships", "jobs"):
        bind.execute(
            sa.text(
                f"UPDATE {table_name} AS record SET "
                "tenant_namespace = workspace.tenant_namespace, "
                "tenant_value = workspace.tenant_value FROM workspaces AS workspace "
                "WHERE record.workspace_namespace = workspace.namespace "
                "AND record.workspace_value = workspace.value"
            )
        )
    bind.execute(
        sa.text(
            "UPDATE entity_evidence AS record SET "
            "tenant_namespace = entity.tenant_namespace, tenant_value = entity.tenant_value, "
            "workspace_namespace = entity.workspace_namespace, "
            "workspace_value = entity.workspace_value FROM entities AS entity "
            "WHERE record.entity_namespace = entity.namespace AND record.entity_value = entity.value"
        )
    )
    bind.execute(
        sa.text(
            "UPDATE relationship_evidence AS record SET "
            "tenant_namespace = relationship.tenant_namespace, "
            "tenant_value = relationship.tenant_value, "
            "workspace_namespace = relationship.workspace_namespace, "
            "workspace_value = relationship.workspace_value FROM relationships AS relationship "
            "WHERE record.relationship_namespace = relationship.namespace "
            "AND record.relationship_value = relationship.value"
        )
    )
    bind.execute(
        sa.text(
            "UPDATE runs AS record SET tenant_namespace = job.tenant_namespace, "
            "tenant_value = job.tenant_value, workspace_namespace = job.workspace_namespace, "
            "workspace_value = job.workspace_value FROM jobs AS job "
            "WHERE record.job_namespace = job.namespace AND record.job_value = job.value"
        )
    )


def _require_ownership_columns() -> None:
    """Make the completed ownership backfill mandatory for every durable row."""
    tables = {
        "workspaces": False,
        "sources": False,
        "source_versions": True,
        "evidence": True,
        "entities": False,
        "entity_evidence": True,
        "relationships": False,
        "relationship_evidence": True,
        "jobs": False,
        "runs": True,
    }
    for table_name, owns_workspace in tables.items():
        op.alter_column(table_name, "tenant_namespace", nullable=False)
        op.alter_column(table_name, "tenant_value", nullable=False)
        if owns_workspace:
            op.alter_column(table_name, "workspace_namespace", nullable=False)
            op.alter_column(table_name, "workspace_value", nullable=False)


def _create_ownership_constraints() -> None:
    """Use composite keys so child rows cannot cross ownership boundaries."""
    op.create_foreign_key(
        "fk_workspaces_tenant",
        "workspaces",
        "tenants",
        ["tenant_namespace", "tenant_value"],
        ["namespace", "value"],
    )
    op.create_unique_constraint(
        "uq_workspaces_ownership",
        "workspaces",
        ["namespace", "value", "tenant_namespace", "tenant_value"],
    )
    _create_owned_workspace_constraint("sources", "fk_sources_workspace_ownership")
    op.create_unique_constraint(
        "uq_sources_ownership",
        "sources",
        [
            "namespace",
            "value",
            "workspace_namespace",
            "workspace_value",
            "tenant_namespace",
            "tenant_value",
        ],
    )
    _create_owned_source_constraint()
    op.create_unique_constraint(
        "uq_source_versions_ownership",
        "source_versions",
        [
            "source_namespace",
            "source_value",
            "content_digest",
            "workspace_namespace",
            "workspace_value",
            "tenant_namespace",
            "tenant_value",
        ],
    )
    _create_owned_version_constraint()
    op.create_unique_constraint(
        "uq_evidence_ownership",
        "evidence",
        [
            "namespace",
            "value",
            "workspace_namespace",
            "workspace_value",
            "tenant_namespace",
            "tenant_value",
        ],
    )
    _create_owned_workspace_constraint("entities", "fk_entities_workspace_ownership")
    op.create_unique_constraint(
        "uq_entities_ownership",
        "entities",
        [
            "namespace",
            "value",
            "workspace_namespace",
            "workspace_value",
            "tenant_namespace",
            "tenant_value",
        ],
    )
    _create_entity_evidence_constraints()
    _create_owned_workspace_constraint("relationships", "fk_relationships_workspace_ownership")
    _create_relationship_constraints()
    _create_relationship_evidence_constraints()
    _create_owned_workspace_constraint("jobs", "fk_jobs_workspace_ownership")
    op.create_unique_constraint(
        "uq_jobs_ownership",
        "jobs",
        [
            "namespace",
            "value",
            "workspace_namespace",
            "workspace_value",
            "tenant_namespace",
            "tenant_value",
        ],
    )
    op.create_foreign_key(
        "fk_runs_job_ownership",
        "runs",
        "jobs",
        [
            "job_namespace",
            "job_value",
            "workspace_namespace",
            "workspace_value",
            "tenant_namespace",
            "tenant_value",
        ],
        [
            "namespace",
            "value",
            "workspace_namespace",
            "workspace_value",
            "tenant_namespace",
            "tenant_value",
        ],
    )


def _create_owned_workspace_constraint(table_name: str, constraint_name: str) -> None:
    """Bind one workspace-owned record to the matching tenant tuple."""
    op.create_foreign_key(
        constraint_name,
        table_name,
        "workspaces",
        ["workspace_namespace", "workspace_value", "tenant_namespace", "tenant_value"],
        ["namespace", "value", "tenant_namespace", "tenant_value"],
    )


def _create_owned_source_constraint() -> None:
    """Bind source versions to their source's workspace and tenant."""
    op.create_foreign_key(
        "fk_source_versions_source_ownership",
        "source_versions",
        "sources",
        [
            "source_namespace",
            "source_value",
            "workspace_namespace",
            "workspace_value",
            "tenant_namespace",
            "tenant_value",
        ],
        [
            "namespace",
            "value",
            "workspace_namespace",
            "workspace_value",
            "tenant_namespace",
            "tenant_value",
        ],
    )


def _create_owned_version_constraint() -> None:
    """Bind evidence records to one immutable version's ownership tuple."""
    op.create_foreign_key(
        "fk_evidence_source_version_ownership",
        "evidence",
        "source_versions",
        [
            "source_namespace",
            "source_value",
            "content_digest",
            "workspace_namespace",
            "workspace_value",
            "tenant_namespace",
            "tenant_value",
        ],
        [
            "source_namespace",
            "source_value",
            "content_digest",
            "workspace_namespace",
            "workspace_value",
            "tenant_namespace",
            "tenant_value",
        ],
    )


def _create_entity_evidence_constraints() -> None:
    """Require every entity evidence attachment to share one owner tuple."""
    ownership = ["workspace_namespace", "workspace_value", "tenant_namespace", "tenant_value"]
    op.create_foreign_key(
        "fk_entity_evidence_entity_ownership",
        "entity_evidence",
        "entities",
        ["entity_namespace", "entity_value", *ownership],
        ["namespace", "value", *ownership],
    )
    op.create_foreign_key(
        "fk_entity_evidence_evidence_ownership",
        "entity_evidence",
        "evidence",
        ["evidence_namespace", "evidence_value", *ownership],
        ["namespace", "value", *ownership],
    )


def _create_relationship_constraints() -> None:
    """Require relationship endpoints and primary evidence to share its owner."""
    ownership = ["workspace_namespace", "workspace_value", "tenant_namespace", "tenant_value"]
    op.create_unique_constraint(
        "uq_relationships_ownership",
        "relationships",
        ["namespace", "value", *ownership],
    )
    for prefix, constraint_name in (
        ("from", "fk_relationships_from_entity_ownership"),
        ("to", "fk_relationships_to_entity_ownership"),
    ):
        op.create_foreign_key(
            constraint_name,
            "relationships",
            "entities",
            [f"{prefix}_namespace", f"{prefix}_value", *ownership],
            ["namespace", "value", *ownership],
        )
    op.create_foreign_key(
        "fk_relationships_primary_evidence_ownership",
        "relationships",
        "evidence",
        ["primary_evidence_namespace", "primary_evidence_value", *ownership],
        ["namespace", "value", *ownership],
    )


def _create_relationship_evidence_constraints() -> None:
    """Require each relationship evidence attachment to share one owner tuple."""
    ownership = ["workspace_namespace", "workspace_value", "tenant_namespace", "tenant_value"]
    op.create_foreign_key(
        "fk_relationship_evidence_relationship_ownership",
        "relationship_evidence",
        "relationships",
        ["relationship_namespace", "relationship_value", *ownership],
        ["namespace", "value", *ownership],
    )
    op.create_foreign_key(
        "fk_relationship_evidence_evidence_ownership",
        "relationship_evidence",
        "evidence",
        ["evidence_namespace", "evidence_value", *ownership],
        ["namespace", "value", *ownership],
    )


def downgrade() -> None:
    """Refuse destructive removal of mandatory tenant ownership."""
    raise NotImplementedError("tenant ownership downgrade is intentionally unsupported")
