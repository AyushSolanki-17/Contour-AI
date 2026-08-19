"""Framework-independent entity and relationship assertion records."""

from __future__ import annotations

from dataclasses import dataclass

from contour.domain._validation import require_evidence_ids, require_text
from contour.domain.identifiers import EntityId, EvidenceId, RelationshipId, WorkspaceId
from contour.domain.time import TimePoint


@dataclass(frozen=True, slots=True)
class Entity:
    """A namespaced entity assertion backed by exact evidence."""

    id: EntityId
    workspace_id: WorkspaceId
    label: str
    evidence_ids: tuple[EvidenceId, ...]
    valid_time: TimePoint
    transaction_time: TimePoint

    def __post_init__(self) -> None:
        """Reject unsupported identity, evidence, or temporal values."""
        if not isinstance(self.id, EntityId):
            raise TypeError("id must be an EntityId")
        if not isinstance(self.workspace_id, WorkspaceId):
            raise TypeError("workspace_id must be a WorkspaceId")
        require_text(self.label, field_name="label")
        require_evidence_ids(self.evidence_ids)
        if not isinstance(self.valid_time, TimePoint):
            raise TypeError("valid_time must be a TimePoint")
        if not isinstance(self.transaction_time, TimePoint):
            raise TypeError("transaction_time must be a TimePoint")


@dataclass(frozen=True, slots=True)
class Relationship:
    """A typed, directed relationship whose edge retains its evidence."""

    id: RelationshipId
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
