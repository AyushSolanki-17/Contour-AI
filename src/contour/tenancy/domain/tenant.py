"""Tenant aggregate and identity for durable Contour ownership."""

from __future__ import annotations

from dataclasses import dataclass

from contour.identifiers import require_identifier_value, require_namespace
from contour.validation import require_text


@dataclass(frozen=True, slots=True)
class TenantId:
    """A stable identifier for one security and ownership boundary."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed tenant identity components."""
        object.__setattr__(self, "namespace", require_namespace(self.namespace))
        object.__setattr__(self, "value", require_identifier_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized tenant identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class Tenant:
    """The durable owner of workspaces and their derived records."""

    id: TenantId
    name: str

    def __post_init__(self) -> None:
        """Validate tenant identity and visible name."""
        if not isinstance(self.id, TenantId):
            raise TypeError("id must be a TenantId")
        require_text(self.name, field_name="name")
