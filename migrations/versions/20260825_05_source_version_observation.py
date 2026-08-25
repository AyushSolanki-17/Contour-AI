"""Retain source-version observation time without fabricating legacy values.

Revision ID: 20260825_05
Revises: 20260824_04
Create Date: 2026-08-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260825_05"
down_revision: str | Sequence[str] | None = "20260824_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add observation time while preserving explicit unknowns in legacy rows."""
    op.add_column(
        "source_versions",
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "source_versions",
        sa.Column(
            "observation_time_unknown",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.alter_column(
        "source_versions",
        "observation_time_unknown",
        server_default=sa.false(),
    )
    op.create_check_constraint(
        "ck_source_versions_observed_at",
        "source_versions",
        "(observed_at IS NULL) = observation_time_unknown",
    )


def downgrade() -> None:
    """Refuse destructive observation-time removal without explicit recovery."""
    raise NotImplementedError("source-version observation downgrade is intentionally unsupported")
