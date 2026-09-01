"""Enforce one logical source registration per workspace and connector.

Revision ID: 20260901_09
Revises: 20260831_08
Create Date: 2026-09-01

The constraint makes the existing application-level duplicate check safe under
concurrency. If legacy duplicate registrations exist, the migration fails
without deleting or merging data; operators must resolve the conflicting
records explicitly and retry the transactional upgrade.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260901_09"
down_revision: str | Sequence[str] | None = "20260831_08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Reject duplicate connector registrations inside one workspace."""
    op.create_unique_constraint(
        "uq_sources_registration",
        "sources",
        [
            "workspace_namespace",
            "workspace_value",
            "source_type",
            "canonical_locator",
        ],
    )


def downgrade() -> None:
    """Refuse to weaken durable duplicate-registration protection."""
    raise NotImplementedError("source registration uniqueness downgrade is unsupported")
