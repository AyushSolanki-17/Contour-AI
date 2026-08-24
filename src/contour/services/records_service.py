"""Application orchestration for durable knowledge and execution records."""

from __future__ import annotations

from collections.abc import Sequence

from contour.domain.entity import Entity
from contour.domain.job import Job
from contour.domain.relationship import Relationship
from contour.domain.run import Run
from contour.repositories.records_transaction import RecordTransactionManager


class RecordPersistenceService:
    """Admits cohesive knowledge assertions and execution attempts atomically."""

    def __init__(self, transactions: RecordTransactionManager) -> None:
        """Initialize the service with the record transaction boundary."""
        self._transactions = transactions

    def admit_knowledge(self, *, entities: Sequence[Entity], relationship: Relationship) -> None:
        """Persist entities and one evidence-backed relationship atomically.

        Raises:
            ValueError: If the supplied entities cannot satisfy the relationship endpoints.
        """
        entity_ids = {entity.id for entity in entities}
        if not {relationship.from_entity, relationship.to_entity}.issubset(entity_ids):
            raise ValueError("relationship endpoints must be included in the admitted entities")
        if any(entity.workspace_id != relationship.workspace_id for entity in entities):
            raise ValueError("entities and relationship must belong to the same workspace")

        with self._transactions.transaction() as transaction:
            for entity in entities:
                transaction.entities.save_entity(entity)
            transaction.relationships.save_relationship(relationship)

    def record_execution(self, *, job: Job, runs: Sequence[Run]) -> None:
        """Persist one requested job and all supplied attempts atomically.

        Raises:
            ValueError: If an attempt belongs to a different requested job.
        """
        if any(run.job_id != job.id for run in runs):
            raise ValueError("every run must belong to the recorded job")

        with self._transactions.transaction() as transaction:
            transaction.jobs.save_job(job)
            for run in runs:
                transaction.runs.save_run(run)
