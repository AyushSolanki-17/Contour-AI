"""PostgreSQL repository for evidence-backed entity assertions."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from sqlalchemy import Connection, insert, select

from contour.infrastructure.postgres.tables.knowledge import entities, entity_evidence
from contour.knowledge.domain.entity import Entity, EntityId
from contour.knowledge.domain.evidence import EvidenceId
from contour.tenancy.domain.access import AccessContext
from contour.tenancy.domain.tenant import TenantId
from contour.time import TimePoint
from contour.workspaces.domain.workspace import WorkspaceId


class PostgresEntityRepository:
    """Maps entities and their ordered evidence in a caller-owned transaction."""

    def __init__(self, connection: Connection) -> None:
        """Bind the repository to its caller-owned transaction connection."""
        self._connection = connection

    def get_entity(self, access: AccessContext, entity_id: EntityId) -> Entity | None:
        """Return an entity with all exact evidence attachments in stored order."""
        row = (
            self._connection.execute(
                select(entities).where(
                    entities.c.namespace == entity_id.namespace,
                    entities.c.value == entity_id.value,
                    entities.c.tenant_namespace == access.tenant_id.namespace,
                    entities.c.tenant_value == access.tenant_id.value,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None

        evidence_rows = self._connection.execute(
            select(entity_evidence.c.evidence_namespace, entity_evidence.c.evidence_value)
            .where(
                entity_evidence.c.entity_namespace == entity_id.namespace,
                entity_evidence.c.entity_value == entity_id.value,
            )
            .order_by(entity_evidence.c.position)
        ).mappings()
        evidence_ids = tuple(
            EvidenceId(
                cast(str, evidence_row["evidence_namespace"]),
                cast(str, evidence_row["evidence_value"]),
            )
            for evidence_row in evidence_rows
        )
        return Entity(
            entity_id,
            TenantId(cast(str, row["tenant_namespace"]), cast(str, row["tenant_value"])),
            WorkspaceId(cast(str, row["workspace_namespace"]), cast(str, row["workspace_value"])),
            cast(str, row["label"]),
            evidence_ids,
            TimePoint(cast(datetime | None, row["valid_time"])),
            TimePoint(cast(datetime | None, row["transaction_time"])),
        )

    def save_entity(self, access: AccessContext, entity: Entity) -> None:
        """Insert an entity and all mandatory evidence attachments atomically."""
        if not access.permits(entity.tenant_id):
            raise ValueError("entity is outside access scope")
        self._connection.execute(
            insert(entities).values(
                namespace=entity.id.namespace,
                value=entity.id.value,
                tenant_namespace=entity.tenant_id.namespace,
                tenant_value=entity.tenant_id.value,
                workspace_namespace=entity.workspace_id.namespace,
                workspace_value=entity.workspace_id.value,
                label=entity.label,
                valid_time=entity.valid_time.value,
                transaction_time=entity.transaction_time.value,
            )
        )
        self._connection.execute(
            insert(entity_evidence),
            [
                {
                    "entity_namespace": entity.id.namespace,
                    "entity_value": entity.id.value,
                    "tenant_namespace": entity.tenant_id.namespace,
                    "tenant_value": entity.tenant_id.value,
                    "workspace_namespace": entity.workspace_id.namespace,
                    "workspace_value": entity.workspace_id.value,
                    "position": position,
                    "evidence_namespace": evidence_id.namespace,
                    "evidence_value": evidence_id.value,
                }
                for position, evidence_id in enumerate(entity.evidence_ids)
            ],
        )
