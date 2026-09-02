"""Evidence-backed relationship assertion and its namespaced identity."""

from __future__ import annotations

from dataclasses import dataclass

from contour.identifiers import require_identifier_value, require_namespace
from contour.knowledge.domain.entity import EntityId
from contour.knowledge.domain.evidence import EvidenceId, require_evidence_ids
from contour.tenancy.domain.tenant import TenantId
from contour.time import TimePoint
from contour.validation import require_text
from contour.workspaces.domain.workspace import WorkspaceId


@dataclass(frozen=True, slots=True)
class RelationshipId:
    """A stable identifier for one evidence-backed relationship assertion."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed relationship identity components."""
        object.__setattr__(self, "namespace", require_namespace(self.namespace))
        object.__setattr__(self, "value", require_identifier_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized relationship identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class Relationship:
    """A typed, directed relationship whose edge retains its evidence."""

    id: RelationshipId
    tenant_id: TenantId
    workspace_id: WorkspaceId
    from_entity: EntityId
    relationship_type: str
    to_entity: EntityId
    evidence_ids: tuple[EvidenceId, ...]
    valid_time: TimePoint
    transaction_time: TimePoint

    def __post_init__(self) -> None:
        """Reject mixed endpoints, empty relationship types, and missing evidence."""
        if not isinstance(self.id, RelationshipId):
            raise TypeError("id must be a RelationshipId")
        if not isinstance(self.tenant_id, TenantId):
            raise TypeError("tenant_id must be a TenantId")
        if not isinstance(self.workspace_id, WorkspaceId):
            raise TypeError("workspace_id must be a WorkspaceId")
        if not isinstance(self.from_entity, EntityId):
            raise TypeError("from_entity must be an EntityId")
        if not isinstance(self.to_entity, EntityId):
            raise TypeError("to_entity must be an EntityId")
        require_text(self.relationship_type, field_name="relationship_type")
        require_evidence_ids(self.evidence_ids)
        if not isinstance(self.valid_time, TimePoint):
            raise TypeError("valid_time must be a TimePoint")
        if not isinstance(self.transaction_time, TimePoint):
            raise TypeError("transaction_time must be a TimePoint")
