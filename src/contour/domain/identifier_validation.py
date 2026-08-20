"""Shared validation rules for namespaced domain identifiers."""

from __future__ import annotations

import re

_NAMESPACE_PATTERN = re.compile(r"[A-Z][A-Z0-9_-]*(?::[A-Z][A-Z0-9_-]*)*")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def require_namespace(value: str) -> str:
    """Validate a stable, uppercase namespace token sequence.

    Raises:
        TypeError: If the value is not text.
        ValueError: If the namespace is empty or malformed.
    """
    if not isinstance(value, str):
        raise TypeError("namespace must be a string")
    if not _NAMESPACE_PATTERN.fullmatch(value):
        raise ValueError("namespace must contain uppercase tokens separated by ':'")
    return value


def require_identifier_value(value: str, *, field_name: str) -> str:
    """Validate one non-empty identifier component.

    Raises:
        TypeError: If the value is not text.
        ValueError: If the value is empty or contains a reserved separator.
    """
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be non-empty text without whitespace")
    if "@" in value:
        raise ValueError(f"{field_name} must not contain '@'")
    return value


def require_sha256_digest(value: str) -> str:
    """Validate the canonical lowercase hexadecimal form of a SHA-256 digest."""
    if not isinstance(value, str):
        raise TypeError("digest value must be a string")
    if not _SHA256_PATTERN.fullmatch(value):
        raise ValueError("digest value must be 64 lowercase hexadecimal characters")
    return value
