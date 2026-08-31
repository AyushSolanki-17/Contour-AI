"""Persist tenant-scoped product idempotency responses.

Revision ID: 20260831_08
Revises: 20260831_07
Create Date: 2026-08-31

The table is additive. PostgreSQL transactional DDL rolls back a failed upgrade;
retrying ``alembic upgrade head`` is the recovery path.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260831_08"
down_revision: str | Sequence[str] | None = "20260831_07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create replay records keyed by principal, selected tenant, route, and key."""
    op.create_table(
        "idempotency_records",
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


def downgrade() -> None:
    """Remove the additive replay table."""
    op.drop_table("idempotency_records")
