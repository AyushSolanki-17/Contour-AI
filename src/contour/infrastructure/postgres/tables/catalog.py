"""SQLAlchemy Core tables for durable catalog and evidence records."""

from __future__ import annotations

import sqlalchemy as sa

from contour.infrastructure.postgres.tables.metadata import metadata

workspaces = sa.Table(
    "workspaces",
    metadata,
    sa.Column("namespace", sa.Text(), nullable=False),
    sa.Column("value", sa.Text(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("owner_name", sa.Text(), nullable=False),
    sa.Column("settings", sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint("namespace", "value", name="pk_workspaces"),
)

sources = sa.Table(
    "sources",
    metadata,
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

source_versions = sa.Table(
    "source_versions",
    metadata,
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
sa.Index(
    "uq_source_versions_upstream_revision",
    source_versions.c.source_namespace,
    source_versions.c.source_value,
    source_versions.c.upstream_revision,
    unique=True,
    postgresql_where=source_versions.c.upstream_revision.is_not(None),
)

evidence = sa.Table(
    "evidence",
    metadata,
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
