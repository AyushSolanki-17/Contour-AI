"""Establish the initial Contour migration revision.

Revision ID: 20260819_01
Revises:
Create Date: 2026-08-19

This intentionally has no application tables.  It records the migration
baseline; Phase 0.2 owns the first durable domain schema.
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "20260819_01"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Record the baseline through Alembic's version table."""


def downgrade() -> None:
    """Do not provide destructive downgrade behavior for the baseline."""
