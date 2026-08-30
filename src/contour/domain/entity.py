"""Evidence-backed knowledge entity and its namespaced identity."""

from __future__ import annotations

from dataclasses import dataclass

from contour.domain.evidence import EvidenceId
from contour.domain.identifier_validation import require_identifier_value, require_namespace
from contour.domain.tenant import TenantId
from contour.domain.time_point import TimePoint
from contour.domain.validation import require_evidence_ids, require_text
from contour.domain.workspace import WorkspaceId


@dataclass(frozen=True, slots=True)
class EntityId:
    """A namespaced identity for one knowledge-model entity."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed entity identity components."""
        object.__setattr__(self, "namespace", require_namespace(self.namespace))
        object.__setattr__(self, "value", require_identifier_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized entity identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class Entity:
    """A namespaced entity assertion backed by exact evidence."""

    id: EntityId
    tenant_id: TenantId
    workspace_id: WorkspaceId
    label: str
    evidence_ids: tuple[EvidenceId, ...]
    valid_time: TimePoint
    transaction_time: TimePoint

    def __post_init__(self) -> None:
        """Reject unsupported identity, evidence, or temporal values."""
        if not isinstance(self.id, EntityId):
            raise TypeError("id must be an EntityId")
        if not isinstance(self.tenant_id, TenantId):
            raise TypeError("tenant_id must be a TenantId")
        if not isinstance(self.workspace_id, WorkspaceId):
            raise TypeError("workspace_id must be a WorkspaceId")
        require_text(self.label, field_name="label")
        require_evidence_ids(self.evidence_ids)
        if not isinstance(self.valid_time, TimePoint):
            raise TypeError("valid_time must be a TimePoint")
        if not isinstance(self.transaction_time, TimePoint):
            raise TypeError("transaction_time must be a TimePoint")
