"""Generic validation rules for framework-independent domain values."""

from __future__ import annotations


def require_text(value: str, *, field_name: str) -> str:
    """Validate a required human- or provider-owned text field."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty text without surrounding whitespace")
    return value
