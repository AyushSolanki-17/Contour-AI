"""Enforce complete exact-evidence spans.

Revision ID: 20260824_03
Revises: 20260820_02
Create Date: 2026-08-24
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260824_03"
down_revision: str | Sequence[str] | None = "20260820_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Replace the span check with a predicate that cannot evaluate to NULL."""
    op.drop_constraint("ck_evidence_valid_span", "evidence", type_="check")
    op.create_check_constraint(
        "ck_evidence_valid_span",
        "evidence",
        "(start_offset IS NULL AND end_offset IS NULL) OR "
        "(start_offset IS NOT NULL AND end_offset IS NOT NULL "
        "AND start_offset >= 0 AND end_offset > start_offset)",
    )


def downgrade() -> None:
    """Refuse to weaken durable evidence-span validation during downgrade."""
    raise NotImplementedError("evidence span constraint downgrade is intentionally unsupported")
