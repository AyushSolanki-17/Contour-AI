"""Application orchestration for evidence-backed knowledge records."""

from __future__ import annotations

from collections.abc import Sequence

from contour.domain.access import AccessContext
from contour.domain.entity import Entity
from contour.domain.relationship import Relationship
from contour.repositories.knowledge_transaction import KnowledgeTransactionManager
from contour.services.resource_errors import ResourceNotFoundError


class KnowledgePersistenceService:
    """Admits cohesive evidence-backed knowledge assertions atomically."""

    def __init__(self, transactions: KnowledgeTransactionManager) -> None:
        """Initialize the service with the knowledge transaction boundary."""
        self._transactions = transactions

    def admit_knowledge(
        self, *, access: AccessContext, entities: Sequence[Entity], relationship: Relationship
    ) -> None:
        """Persist entities and one evidence-backed relationship atomically.

        Raises:
            ResourceNotFoundError: If the scope or supplied records do not share one owner.
        """
        entity_ids = {entity.id for entity in entities}
        if not {relationship.from_entity, relationship.to_entity}.issubset(entity_ids):
            raise ResourceNotFoundError()
        if not access.permits(relationship.tenant_id):
            raise ResourceNotFoundError()
        if any(entity.workspace_id != relationship.workspace_id for entity in entities):
            raise ResourceNotFoundError()
        if any(entity.tenant_id != relationship.tenant_id for entity in entities):
            raise ResourceNotFoundError()

        with self._transactions.transaction() as transaction:
            for entity in entities:
                transaction.entities.save_entity(access, entity)
            transaction.relationships.save_relationship(access, relationship)
