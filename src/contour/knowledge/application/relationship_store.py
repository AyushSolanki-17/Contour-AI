"""Persistence contract for evidence-backed relationship assertions."""

from __future__ import annotations

from typing import Protocol

from contour.knowledge.domain.relationship import Relationship, RelationshipId
from contour.tenancy.domain.access import AccessContext


class RelationshipRepository(Protocol):
    """Persists directed relationships together with their edge-level evidence."""

    def get_relationship(
        self, access: AccessContext, relationship_id: RelationshipId
    ) -> Relationship | None:
        """Return a relationship and its ordered exact evidence, if admitted."""

    def save_relationship(self, access: AccessContext, relationship: Relationship) -> None:
        """Insert a relationship only when its endpoints and evidence exist."""
