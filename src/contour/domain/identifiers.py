"""Typed, namespaced identifiers for immutable source evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass

_NAMESPACE_PATTERN = re.compile(r"[A-Z][A-Z0-9_-]*(?::[A-Z][A-Z0-9_-]*)*")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def _require_namespace(value: str) -> str:
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


def _require_local_value(value: str, *, field_name: str) -> str:
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


@dataclass(frozen=True, slots=True)
class SourceId:
    """A source-owned identifier within an explicit namespace."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed source identity components."""
        object.__setattr__(self, "namespace", _require_namespace(self.namespace))
        object.__setattr__(self, "value", _require_local_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized source identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class EvidenceId:
    """A distinct identifier reserved for an evidence record."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed evidence identity components."""
        object.__setattr__(self, "namespace", _require_namespace(self.namespace))
        object.__setattr__(self, "value", _require_local_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized evidence identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class ContentDigest:
    """The SHA-256 identity of the exact bytes admitted for a source version."""

    value: str

    def __post_init__(self) -> None:
        """Reject digests that cannot be a canonical SHA-256 value."""
        if not isinstance(self.value, str):
            raise TypeError("digest value must be a string")
        if not _SHA256_PATTERN.fullmatch(self.value):
            raise ValueError("digest value must be 64 lowercase hexadecimal characters")

    def __str__(self) -> str:
        """Return the algorithm-qualified digest serialization."""
        return f"sha256:{self.value}"


@dataclass(frozen=True, slots=True)
class SourceVersionId:
    """The immutable identity of one source's admitted content version."""

    source_id: SourceId
    content_digest: ContentDigest

    def __post_init__(self) -> None:
        """Require source and digest values with their intended domain types."""
        if not isinstance(self.source_id, SourceId):
            raise TypeError("source_id must be a SourceId")
        if not isinstance(self.content_digest, ContentDigest):
            raise TypeError("content_digest must be a ContentDigest")

    def __str__(self) -> str:
        """Return a source-qualified immutable version key."""
        return f"{self.source_id}@{self.content_digest}"


@dataclass(frozen=True, slots=True)
class WorkspaceId:
    """A stable identifier for one isolated Contour workspace."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed workspace identity components."""
        object.__setattr__(self, "namespace", _require_namespace(self.namespace))
        object.__setattr__(self, "value", _require_local_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized workspace identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class EntityId:
    """A namespaced identity for one knowledge-model entity."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed entity identity components."""
        object.__setattr__(self, "namespace", _require_namespace(self.namespace))
        object.__setattr__(self, "value", _require_local_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized entity identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class RelationshipId:
    """A stable identifier for one evidence-backed relationship assertion."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed relationship identity components."""
        object.__setattr__(self, "namespace", _require_namespace(self.namespace))
        object.__setattr__(self, "value", _require_local_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized relationship identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class JobId:
    """A stable identifier for one requested unit of work."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed job identity components."""
        object.__setattr__(self, "namespace", _require_namespace(self.namespace))
        object.__setattr__(self, "value", _require_local_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized job identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class RunId:
    """A stable identifier for one execution attempt of a requested job."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed run identity components."""
        object.__setattr__(self, "namespace", _require_namespace(self.namespace))
        object.__setattr__(self, "value", _require_local_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized run identifier."""
        return f"{self.namespace}:{self.value}"
