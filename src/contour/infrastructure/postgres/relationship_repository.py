"""PostgreSQL repository for evidence-backed relationship assertions."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from sqlalchemy import Connection, insert, select

from contour.domain.entity import EntityId
from contour.domain.evidence import EvidenceId
from contour.domain.relationship import Relationship, RelationshipId
from contour.domain.time_point import TimePoint
from contour.domain.workspace import WorkspaceId
from contour.infrastructure.postgres.tables.knowledge import relationship_evidence, relationships


class PostgresRelationshipRepository:
    """Maps relationships and their edge-level evidence in one transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its caller-owned transaction connection."""
        self._connection = connection

    def get_relationship(self, relationship_id: RelationshipId) -> Relationship | None:
        """Return a relationship with exact evidence attachments in stored order."""
        row = (
            self._connection.execute(
                select(relationships).where(
                    relationships.c.namespace == relationship_id.namespace,
                    relationships.c.value == relationship_id.value,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None

        evidence_rows = self._connection.execute(
            select(
                relationship_evidence.c.evidence_namespace, relationship_evidence.c.evidence_value
            )
            .where(
                relationship_evidence.c.relationship_namespace == relationship_id.namespace,
                relationship_evidence.c.relationship_value == relationship_id.value,
            )
            .order_by(relationship_evidence.c.position)
        ).mappings()
        evidence_ids = tuple(
            EvidenceId(
                cast(str, evidence_row["evidence_namespace"]),
                cast(str, evidence_row["evidence_value"]),
            )
            for evidence_row in evidence_rows
        )
        return Relationship(
            relationship_id,
            WorkspaceId(cast(str, row["workspace_namespace"]), cast(str, row["workspace_value"])),
            EntityId(cast(str, row["from_namespace"]), cast(str, row["from_value"])),
            cast(str, row["relationship_type"]),
            EntityId(cast(str, row["to_namespace"]), cast(str, row["to_value"])),
            evidence_ids,
            TimePoint(cast(datetime | None, row["valid_time"])),
            TimePoint(cast(datetime | None, row["transaction_time"])),
        )

    def save_relationship(self, relationship: Relationship) -> None:
        """Insert a relationship and all mandatory edge-level evidence attachments."""
        self._connection.execute(
            insert(relationships).values(
                namespace=relationship.id.namespace,
                value=relationship.id.value,
                workspace_namespace=relationship.workspace_id.namespace,
                workspace_value=relationship.workspace_id.value,
                from_namespace=relationship.from_entity.namespace,
                from_value=relationship.from_entity.value,
                relationship_type=relationship.relationship_type,
                to_namespace=relationship.to_entity.namespace,
                to_value=relationship.to_entity.value,
                primary_evidence_namespace=relationship.evidence_ids[0].namespace,
                primary_evidence_value=relationship.evidence_ids[0].value,
                valid_time=relationship.valid_time.value,
                transaction_time=relationship.transaction_time.value,
            )
        )
        self._connection.execute(
            insert(relationship_evidence),
            [
                {
                    "relationship_namespace": relationship.id.namespace,
                    "relationship_value": relationship.id.value,
                    "position": position,
                    "evidence_namespace": evidence_id.namespace,
                    "evidence_value": evidence_id.value,
                }
                for position, evidence_id in enumerate(relationship.evidence_ids)
            ],
        )
