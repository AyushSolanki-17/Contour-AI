"""Persistence contract for evidence-backed entity assertions."""

from __future__ import annotations

from typing import Protocol

from contour.domain.entity import Entity, EntityId


class EntityRepository(Protocol):
    """Persists entities whose identity and evidence attachments are immutable."""

    def get_entity(self, entity_id: EntityId) -> Entity | None:
        """Return an entity and its ordered exact evidence, if it is admitted."""

    def save_entity(self, entity: Entity) -> None:
        """Insert an entity with at least one exact evidence attachment."""
