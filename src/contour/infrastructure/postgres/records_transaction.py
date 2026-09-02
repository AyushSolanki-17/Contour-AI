"""PostgreSQL transaction composition for knowledge and execution records."""

from __future__ import annotations

from types import TracebackType

from psycopg.errors import CheckViolation, ForeignKeyViolation, UniqueViolation
from sqlalchemy import Connection, Engine
from sqlalchemy.engine import RootTransaction
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from contour.errors import (
    RecordConflictError,
    RecordPersistenceError,
    RecordReferenceError,
)
from contour.infrastructure.postgres.entity_repository import PostgresEntityRepository
from contour.infrastructure.postgres.job_repository import PostgresJobRepository
from contour.infrastructure.postgres.relationship_repository import PostgresRelationshipRepository
from contour.infrastructure.postgres.run_repository import PostgresRunRepository
from contour.jobs.application.job_store import JobRepository
from contour.jobs.application.run_store import RunRepository
from contour.knowledge.application.entity_store import EntityRepository
from contour.knowledge.application.relationship_store import RelationshipRepository


class PostgresRecordTransactionManager:
    """Factory for record transactions backed by a process-scoped engine."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the factory with an engine owned by the composition root."""
        self._engine = engine

    def transaction(self) -> PostgresRecordUnitOfWork:
        """Create one unopened transaction scope for a record operation."""
        return PostgresRecordUnitOfWork(self._engine)


class PostgresRecordUnitOfWork:
    """Bind knowledge and execution repositories to one atomic transaction."""

    def __init__(self, engine: Engine) -> None:
        """Initialize an unopened transaction scope for the supplied engine."""
        self._engine = engine
        self._connection: Connection | None = None
        self._transaction: RootTransaction | None = None
        self._entities: EntityRepository | None = None
        self._relationships: RelationshipRepository | None = None
        self._jobs: JobRepository | None = None
        self._runs: RunRepository | None = None

    @property
    def entities(self) -> EntityRepository:
        """Return the entity repository in the active transaction."""
        return self._require_active(self._entities, name="entity repository")

    @property
    def relationships(self) -> RelationshipRepository:
        """Return the relationship repository in the active transaction."""
        return self._require_active(self._relationships, name="relationship repository")

    @property
    def jobs(self) -> JobRepository:
        """Return the job repository in the active transaction."""
        return self._require_active(self._jobs, name="job repository")

    @property
    def runs(self) -> RunRepository:
        """Return the run repository in the active transaction."""
        return self._require_active(self._runs, name="run repository")

    def __enter__(self) -> PostgresRecordUnitOfWork:
        """Checkout one pooled connection and compose scoped repositories."""
        connection: Connection | None = None
        try:
            connection = self._engine.connect()
            transaction = connection.begin()
        except SQLAlchemyError as error:
            if connection is not None:
                connection.close()
            raise RecordPersistenceError() from error

        self._connection = connection
        self._transaction = transaction
        self._entities = PostgresEntityRepository(connection)
        self._relationships = PostgresRelationshipRepository(connection)
        self._jobs = PostgresJobRepository(connection)
        self._runs = PostgresRunRepository(connection)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit or roll back, release the connection, and translate integrity errors."""
        connection = self._require_active(self._connection, name="connection")
        transaction = self._require_active(self._transaction, name="transaction")
        completion_error: SQLAlchemyError | None = None
        try:
            if exc_type is None:
                try:
                    transaction.commit()
                except SQLAlchemyError as error:
                    completion_error = error
            else:
                try:
                    transaction.rollback()
                except SQLAlchemyError as error:
                    completion_error = error
        finally:
            connection.close()
            self._clear()

        persistence_error = completion_error or (
            exc_value if isinstance(exc_value, SQLAlchemyError) else None
        )
        if persistence_error is not None:
            raise _translate_persistence_error(persistence_error) from persistence_error

    def _clear(self) -> None:
        """Remove references to all resources after the scope closes."""
        self._connection = None
        self._transaction = None
        self._entities = None
        self._relationships = None
        self._jobs = None
        self._runs = None

    @staticmethod
    def _require_active[T](resource: T | None, *, name: str) -> T:
        """Return an active scoped resource or reject out-of-scope access."""
        if resource is None:
            raise RuntimeError(f"record {name} requires an active transaction")
        return resource


def _translate_persistence_error(error: SQLAlchemyError) -> Exception:
    """Translate database failures into stable application errors."""
    if isinstance(error, IntegrityError) and isinstance(error.orig, UniqueViolation):
        return RecordConflictError()
    if isinstance(error, IntegrityError) and isinstance(error.orig, ForeignKeyViolation):
        return RecordReferenceError()
    if isinstance(error, IntegrityError) and isinstance(error.orig, CheckViolation):
        return RecordPersistenceError()
    return RecordPersistenceError()
