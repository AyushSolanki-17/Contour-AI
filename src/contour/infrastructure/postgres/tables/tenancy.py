"""SQLAlchemy Core tables for tenants, principals, memberships, and operation replay."""

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
