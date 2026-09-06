"""Transaction contract for atomic evidence-backed knowledge admission."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from contour.knowledge.domain.entity import Entity, EntityId
from contour.knowledge.domain.evidence import EvidenceId, EvidenceLocator
from contour.knowledge.domain.relationship import Relationship, RelationshipId
from contour.tenancy.domain.access import AccessContext


class KnowledgeUnitOfWork(Protocol):
    """Provide knowledge repositories bound to one atomic operation."""

    @property
    def entities(self) -> EntityRepository:
        """Return the entity repository bound to this transaction."""

    @property
    def relationships(self) -> RelationshipRepository:
        """Return the relationship repository bound to this transaction."""

    def __enter__(self) -> Self:
        """Begin the transaction and return its repositories."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit on success or discard all knowledge writes on failure."""


class KnowledgeTransactionManager(Protocol):
    """Create one explicit atomic boundary for knowledge admission."""

    def transaction(self) -> KnowledgeUnitOfWork:
        """Return a fresh knowledge transaction."""


class EntityRepository(Protocol):
    """Persists entities whose identity and evidence attachments are immutable."""

    def get_entity(self, access: AccessContext, entity_id: EntityId) -> Entity | None:
        """Return an entity and its ordered exact evidence, if it is admitted."""

    def save_entity(self, access: AccessContext, entity: Entity) -> None:
        """Insert an entity with at least one exact evidence attachment."""


class EvidenceRepository(Protocol):
    """Persists exact evidence locators bound to immutable source versions."""

    def get_evidence(
        self, access: AccessContext, evidence_id: EvidenceId
    ) -> EvidenceLocator | None:
        """Return an exact evidence locator by stable identity, if admitted."""

    def save_evidence(
        self, access: AccessContext, evidence_id: EvidenceId, locator: EvidenceLocator
    ) -> None:
        """Persist one evidence record bound to exactly one source version."""


class RelationshipRepository(Protocol):
    """Persists directed relationships together with their edge-level evidence."""

    def get_relationship(
        self, access: AccessContext, relationship_id: RelationshipId
    ) -> Relationship | None:
        """Return a relationship and its ordered exact evidence, if admitted."""

    def save_relationship(self, access: AccessContext, relationship: Relationship) -> None:
        """Insert a relationship only when its endpoints and evidence exist."""
