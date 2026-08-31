"""Application orchestration for durable knowledge and execution records."""

from __future__ import annotations

from collections.abc import Sequence

from contour.domain.access import AccessContext
from contour.domain.entity import Entity
from contour.domain.job import Job
from contour.domain.relationship import Relationship
from contour.domain.run import Run
from contour.repositories.records_transaction import RecordTransactionManager
from contour.services.access_errors import ResourceNotFoundError


class RecordPersistenceService:
    """Admits cohesive knowledge assertions and execution attempts atomically."""

    def __init__(self, transactions: RecordTransactionManager) -> None:
        """Initialize the service with the record transaction boundary."""
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

    def record_execution(self, *, access: AccessContext, job: Job, runs: Sequence[Run]) -> None:
        """Persist one requested job and all supplied attempts atomically.

        Raises:
            ResourceNotFoundError: If the scope or attempts do not share the requested job.
        """
        if any(run.job_id != job.id for run in runs):
            raise ResourceNotFoundError()
        if not access.permits(job.tenant_id):
            raise ResourceNotFoundError()
        if any(
            run.tenant_id != job.tenant_id or run.workspace_id != job.workspace_id for run in runs
        ):
            raise ResourceNotFoundError()

        with self._transactions.transaction() as transaction:
            transaction.jobs.save_job(access, job)
            for run in runs:
                transaction.runs.save_run(access, run)
