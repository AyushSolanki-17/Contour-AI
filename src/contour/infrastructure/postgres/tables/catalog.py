"""SQLAlchemy Core tables for durable catalog and evidence records."""

from __future__ import annotations

import sqlalchemy as sa

from contour.infrastructure.postgres.tables.metadata import metadata

tenants = sa.Table(
    "tenants",
    metadata,
    sa.Column("namespace", sa.Text(), nullable=False),
    sa.Column("value", sa.Text(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint("namespace", "value", name="pk_tenants"),
)

principals = sa.Table(
    "principals",
    metadata,
    sa.Column("namespace", sa.Text(), nullable=False),
    sa.Column("value", sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint("namespace", "value", name="pk_principals"),
)

memberships = sa.Table(
    "memberships",
    metadata,
    sa.Column("principal_namespace", sa.Text(), nullable=False),
    sa.Column("principal_value", sa.Text(), nullable=False),
    sa.Column("tenant_namespace", sa.Text(), nullable=False),
    sa.Column("tenant_value", sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint(
        "principal_namespace",
        "principal_value",
        "tenant_namespace",
        "tenant_value",
        name="pk_memberships",
    ),
    sa.ForeignKeyConstraint(
        ["principal_namespace", "principal_value"],
        ["principals.namespace", "principals.value"],
        name="fk_memberships_principal",
    ),
    sa.ForeignKeyConstraint(
        ["tenant_namespace", "tenant_value"],
        ["tenants.namespace", "tenants.value"],
        name="fk_memberships_tenant",
    ),
)

idempotency_records = sa.Table(
    "idempotency_records",
    metadata,
    sa.Column("principal_namespace", sa.Text(), nullable=False),
    sa.Column("principal_value", sa.Text(), nullable=False),
    sa.Column("scope", sa.Text(), nullable=False),
    sa.Column("route", sa.Text(), nullable=False),
    sa.Column("key", sa.Text(), nullable=False),
    sa.Column("payload_digest", sa.String(length=64), nullable=False),
    sa.Column("response", sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint(
        "principal_namespace",
        "principal_value",
        "scope",
        "route",
        "key",
        name="pk_idempotency_records",
    ),
    sa.ForeignKeyConstraint(
        ["principal_namespace", "principal_value"],
        ["principals.namespace", "principals.value"],
        name="fk_idempotency_records_principal",
    ),
)

workspaces = sa.Table(
    "workspaces",
    metadata,
    sa.Column("namespace", sa.Text(), nullable=False),
    sa.Column("value", sa.Text(), nullable=False),
    sa.Column("tenant_namespace", sa.Text(), nullable=False),
    sa.Column("tenant_value", sa.Text(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("owner_name", sa.Text(), nullable=False),
    sa.Column("settings", sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint("namespace", "value", name="pk_workspaces"),
    sa.UniqueConstraint(
        "namespace",
        "value",
        "tenant_namespace",
        "tenant_value",
        name="uq_workspaces_ownership",
    ),
    sa.ForeignKeyConstraint(
        ["tenant_namespace", "tenant_value"],
        ["tenants.namespace", "tenants.value"],
        name="fk_workspaces_tenant",
    ),
)

sources = sa.Table(
    "sources",
    metadata,
    sa.Column("namespace", sa.Text(), nullable=False),
    sa.Column("value", sa.Text(), nullable=False),
    sa.Column("tenant_namespace", sa.Text(), nullable=False),
    sa.Column("tenant_value", sa.Text(), nullable=False),
    sa.Column("workspace_namespace", sa.Text(), nullable=False),
    sa.Column("workspace_value", sa.Text(), nullable=False),
    sa.Column("canonical_locator", sa.Text(), nullable=False),
    sa.Column("source_type", sa.Text(), nullable=False),
    sa.Column("scope", sa.Text(), nullable=False),
    sa.Column("license", sa.Text(), nullable=True),
    sa.Column("data_classification", sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint("namespace", "value", name="pk_sources"),
    sa.UniqueConstraint(
        "namespace",
        "value",
        "workspace_namespace",
        "workspace_value",
        "tenant_namespace",
        "tenant_value",
        name="uq_sources_ownership",
    ),
    sa.UniqueConstraint(
        "workspace_namespace",
        "workspace_value",
        "source_type",
        "canonical_locator",
        name="uq_sources_registration",
    ),
    sa.ForeignKeyConstraint(
        ["workspace_namespace", "workspace_value"],
        ["workspaces.namespace", "workspaces.value"],
        name="fk_sources_workspace",
    ),
    sa.ForeignKeyConstraint(
        ["workspace_namespace", "workspace_value", "tenant_namespace", "tenant_value"],
        [
            "workspaces.namespace",
            "workspaces.value",
            "workspaces.tenant_namespace",
            "workspaces.tenant_value",
        ],
        name="fk_sources_workspace_ownership",
    ),
)

source_versions = sa.Table(
    "source_versions",
    metadata,
    sa.Column("source_namespace", sa.Text(), nullable=False),
    sa.Column("source_value", sa.Text(), nullable=False),
    sa.Column("content_digest", sa.String(length=64), nullable=False),
    sa.Column("tenant_namespace", sa.Text(), nullable=False),
    sa.Column("tenant_value", sa.Text(), nullable=False),
    sa.Column("workspace_namespace", sa.Text(), nullable=False),
    sa.Column("workspace_value", sa.Text(), nullable=False),
    sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column(
        "observation_time_unknown",
        sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
    ),
    sa.UniqueConstraint(
        "source_namespace",
        "source_value",
        "content_digest",
        "workspace_namespace",
        "workspace_value",
        "tenant_namespace",
        "tenant_value",
        name="uq_source_versions_ownership",
    ),
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
    sa.ForeignKeyConstraint(
        [
            "source_namespace",
            "source_value",
            "workspace_namespace",
            "workspace_value",
            "tenant_namespace",
            "tenant_value",
        ],
        [
            "sources.namespace",
            "sources.value",
            "sources.workspace_namespace",
            "sources.workspace_value",
            "sources.tenant_namespace",
            "sources.tenant_value",
        ],
        name="fk_source_versions_source_ownership",
    ),
    sa.CheckConstraint(
        "(observed_at IS NULL) = observation_time_unknown",
        name="ck_source_versions_observed_at",
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
    sa.Column("tenant_namespace", sa.Text(), nullable=False),
    sa.Column("tenant_value", sa.Text(), nullable=False),
    sa.Column("workspace_namespace", sa.Text(), nullable=False),
    sa.Column("workspace_value", sa.Text(), nullable=False),
    sa.Column("source_namespace", sa.Text(), nullable=False),
    sa.Column("source_value", sa.Text(), nullable=False),
    sa.Column("content_digest", sa.String(length=64), nullable=False),
    sa.Column("locator", sa.Text(), nullable=False),
    sa.Column("start_offset", sa.BigInteger(), nullable=True),
    sa.Column("end_offset", sa.BigInteger(), nullable=True),
    sa.PrimaryKeyConstraint("namespace", "value", name="pk_evidence"),
    sa.UniqueConstraint(
        "namespace",
        "value",
        "workspace_namespace",
        "workspace_value",
        "tenant_namespace",
        "tenant_value",
        name="uq_evidence_ownership",
    ),
    sa.ForeignKeyConstraint(
        ["source_namespace", "source_value", "content_digest"],
        [
            "source_versions.source_namespace",
            "source_versions.source_value",
            "source_versions.content_digest",
        ],
        name="fk_evidence_source_version",
    ),
    sa.ForeignKeyConstraint(
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
            "source_versions.source_namespace",
            "source_versions.source_value",
            "source_versions.content_digest",
            "source_versions.workspace_namespace",
            "source_versions.workspace_value",
            "source_versions.tenant_namespace",
            "source_versions.tenant_value",
        ],
        name="fk_evidence_source_version_ownership",
    ),
    sa.CheckConstraint(
        "(start_offset IS NULL AND end_offset IS NULL) OR "
        "(start_offset IS NOT NULL AND end_offset IS NOT NULL "
        "AND start_offset >= 0 AND end_offset > start_offset)",
        name="ck_evidence_valid_span",
    ),
)
