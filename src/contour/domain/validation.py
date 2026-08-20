"""Shared validation helpers for framework-independent domain values."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contour.domain.evidence import EvidenceId


def require_text(value: str, *, field_name: str) -> str:
    """Validate a required human- or provider-owned text field."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty text without surrounding whitespace")
    return value


def require_evidence_ids(value: tuple[EvidenceId, ...]) -> tuple[EvidenceId, ...]:
    """Require at least one typed, non-duplicated evidence attachment."""
    from contour.domain.evidence import EvidenceId

    if not isinstance(value, tuple) or not value:
        raise ValueError("evidence_ids must contain at least one EvidenceId")
    if any(not isinstance(item, EvidenceId) for item in value):
        raise TypeError("evidence_ids must contain only EvidenceId values")
    if len(set(value)) != len(value):
        raise ValueError("evidence_ids must not contain duplicates")
    return value
