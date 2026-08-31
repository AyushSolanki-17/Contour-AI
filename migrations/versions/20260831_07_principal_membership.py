"""Add provider-neutral principals and tenant memberships.

Revision ID: 20260831_07
Revises: 20260830_06
Create Date: 2026-08-31

This additive revision creates no memberships for legacy tenant data because a
legacy owner cannot safely be inferred. Deploy the revision before code that
requires access contexts. If it fails, PostgreSQL rolls back its transactional
DDL; retrying ``alembic upgrade head`` is the recovery path.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260831_07"
down_revision: str | Sequence[str] | None = "20260830_06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create durable principal identities and their tenant grants."""
    op.create_table(
        "principals",
        sa.Column("namespace", sa.Text(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("namespace", "value", name="pk_principals"),
    )
    op.create_table(
        "memberships",
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


def downgrade() -> None:
    """Remove additive identity tables in reverse dependency order."""
    op.drop_table("memberships")
    op.drop_table("principals")
