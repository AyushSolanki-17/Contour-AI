"""Create the durable source catalog and exact-evidence tables.

Revision ID: 20260820_02
Revises: 20260819_01
Create Date: 2026-08-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_02"
down_revision: str | Sequence[str] | None = "20260819_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create catalog tables whose keys preserve namespaced immutable identity."""
    op.create_table(
        "workspaces",
        sa.Column("namespace", sa.Text(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("owner_name", sa.Text(), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("namespace", "value", name="pk_workspaces"),
    )
    op.create_table(
        "sources",
        sa.Column("namespace", sa.Text(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("workspace_namespace", sa.Text(), nullable=False),
        sa.Column("workspace_value", sa.Text(), nullable=False),
        sa.Column("canonical_locator", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("license", sa.Text(), nullable=True),
        sa.Column("data_classification", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("namespace", "value", name="pk_sources"),
        sa.ForeignKeyConstraint(
            ["workspace_namespace", "workspace_value"],
            ["workspaces.namespace", "workspaces.value"],
            name="fk_sources_workspace",
        ),
    )
    op.create_table(
        "source_versions",
        sa.Column("source_namespace", sa.Text(), nullable=False),
        sa.Column("source_value", sa.Text(), nullable=False),
        sa.Column("content_digest", sa.String(length=64), nullable=False),
        sa.Column("upstream_revision", sa.Text(), nullable=True),
        sa.Column("source_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision_time", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint(
            "source_namespace", "source_value", "content_digest", name="pk_source_versions"
        ),
        sa.ForeignKeyConstraint(
            ["source_namespace", "source_value"],
            ["sources.namespace", "sources.value"],
            name="fk_source_versions_source",
        ),
    )
    op.create_index(
        "uq_source_versions_upstream_revision",
        "source_versions",
        ["source_namespace", "source_value", "upstream_revision"],
        unique=True,
        postgresql_where=sa.text("upstream_revision IS NOT NULL"),
    )
    op.create_table(
        "evidence",
        sa.Column("namespace", sa.Text(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("source_namespace", sa.Text(), nullable=False),
        sa.Column("source_value", sa.Text(), nullable=False),
        sa.Column("content_digest", sa.String(length=64), nullable=False),
        sa.Column("locator", sa.Text(), nullable=False),
        sa.Column("start_offset", sa.BigInteger(), nullable=True),
        sa.Column("end_offset", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("namespace", "value", name="pk_evidence"),
        sa.ForeignKeyConstraint(
            ["source_namespace", "source_value", "content_digest"],
            [
                "source_versions.source_namespace",
                "source_versions.source_value",
                "source_versions.content_digest",
            ],
            name="fk_evidence_source_version",
        ),
        sa.CheckConstraint(
            "(start_offset IS NULL AND end_offset IS NULL) OR "
            "(start_offset >= 0 AND end_offset > start_offset)",
            name="ck_evidence_valid_span",
        ),
    )


def downgrade() -> None:
    """Refuse destructive catalog removal without an explicit recovery procedure."""
    raise NotImplementedError("catalog schema downgrade is intentionally unsupported")
