"""PostgreSQL transaction composition for knowledge admission."""

from __future__ import annotations

from types import TracebackType

from sqlalchemy import Engine

from contour.infrastructure.postgres.entity_repository import PostgresEntityRepository
from contour.infrastructure.postgres.relationship_repository import PostgresRelationshipRepository
from contour.infrastructure.postgres.transaction_scope import PostgresTransactionScope
from contour.knowledge.application.entity_store import EntityRepository
from contour.knowledge.application.relationship_store import RelationshipRepository


class PostgresKnowledgeTransactionManager:
    """Create PostgreSQL transactions for one knowledge admission operation."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the manager with an engine owned by composition.

        Args:
            engine: SQLAlchemy engine that owns the connection pool.
        """
        self._engine = engine

    def transaction(self) -> PostgresKnowledgeUnitOfWork:
        """Create an unopened knowledge-scoped unit of work.

        Returns:
            A transaction that exposes only knowledge repositories.
        """
        return PostgresKnowledgeUnitOfWork(self._engine)


class PostgresKnowledgeUnitOfWork:
    """Bind entity and relationship repositories to one atomic transaction."""

    def __init__(self, engine: Engine) -> None:
        """Initialize an unopened knowledge transaction.

        Args:
            engine: SQLAlchemy engine that owns the connection pool.
        """
        self._scope = PostgresTransactionScope(engine)
        self._entities: EntityRepository | None = None
        self._relationships: RelationshipRepository | None = None

    @property
    def entities(self) -> EntityRepository:
        """Return the entity repository in the active transaction.

        Returns:
            Entity repository bound to this transaction.

        Raises:
            RuntimeError: If the transaction has not been opened.
        """
        return self._require_active(self._entities, name="entity repository")

    @property
    def relationships(self) -> RelationshipRepository:
        """Return the relationship repository in the active transaction.

        Returns:
            Relationship repository bound to this transaction.

        Raises:
            RuntimeError: If the transaction has not been opened.
        """
        return self._require_active(self._relationships, name="relationship repository")

    def __enter__(self) -> PostgresKnowledgeUnitOfWork:
        """Open the transaction and compose its knowledge repositories.

        Returns:
            This active unit of work.
        """
        connection = self._scope.open()
        self._entities = PostgresEntityRepository(connection)
        self._relationships = PostgresRelationshipRepository(connection)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Complete the transaction and remove scoped repository references."""
        self._clear()
        self._scope.close(exc_type, exc_value, traceback)

    def _clear(self) -> None:
        """Release repositories that are valid only while the scope is open."""
        self._entities = None
        self._relationships = None

    @staticmethod
    def _require_active[T](resource: T | None, *, name: str) -> T:
        """Return an active repository or reject out-of-scope use.

        Args:
            resource: Repository initialized when the transaction began.
            name: Human-readable repository name for the error message.

        Returns:
            The initialized repository.

        Raises:
            RuntimeError: If the transaction scope is not active.
        """
        if resource is None:
            raise RuntimeError(f"knowledge {name} requires an active transaction")
        return resource
