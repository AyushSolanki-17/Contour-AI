"""Shared PostgreSQL transaction lifecycle mechanics."""

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


class PostgresTransactionScope:
    """Manage one connection and root transaction for a PostgreSQL unit of work."""

    def __init__(self, engine: Engine) -> None:
        """Initialize an unopened scope from a process-owned engine.

        Args:
            engine: SQLAlchemy engine that owns the connection pool.
        """
        self._engine = engine
        self._connection: Connection | None = None
        self._transaction: RootTransaction | None = None

    def open(self) -> Connection:
        """Checkout a connection and begin its root transaction.

        Returns:
            The connection that repositories must use for this unit of work.

        Raises:
            RecordPersistenceError: If PostgreSQL cannot begin the transaction.
        """
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
        return connection

    def close(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit or roll back the scope, then release its connection.

        Args:
            exc_type: Exception type raised by the protected operation, if any.
            exc_value: Exception raised by the protected operation, if any.
            traceback: Traceback for the protected operation, if any.

        Raises:
            RecordConflictError: If a uniqueness constraint rejects the operation.
            RecordReferenceError: If a foreign-key constraint rejects the operation.
            RecordPersistenceError: If PostgreSQL cannot safely complete the operation.
        """
        del traceback
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
        """Release references after the scope has completed."""
        self._connection = None
        self._transaction = None

    @staticmethod
    def _require_active[T](resource: T | None, *, name: str) -> T:
        """Return an active resource or reject out-of-scope use.

        Args:
            resource: Resource initialized when the transaction began.
            name: Human-readable resource name for the error message.

        Returns:
            The initialized resource.

        Raises:
            RuntimeError: If the transaction scope is not active.
        """
        if resource is None:
            raise RuntimeError(f"PostgreSQL {name} requires an active transaction")
        return resource


def _translate_persistence_error(error: SQLAlchemyError) -> Exception:
    """Translate a database failure into a stable application error.

    Args:
        error: SQLAlchemy error emitted while completing a transaction.

    Returns:
        An application error that does not expose database details.
    """
    if isinstance(error, IntegrityError) and isinstance(error.orig, UniqueViolation):
        return RecordConflictError()
    if isinstance(error, IntegrityError) and isinstance(error.orig, ForeignKeyViolation):
        return RecordReferenceError()
    if isinstance(error, IntegrityError) and isinstance(error.orig, CheckViolation):
        return RecordPersistenceError()
    return RecordPersistenceError()
