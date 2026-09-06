"""PostgreSQL transactions for workspace operations."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine

from contour.infrastructure.postgres.idempotency_repository import PostgresIdempotencyRepository
from contour.infrastructure.postgres.transaction_scope import (
    PostgresTransactionScope,
    translate_catalog_error,
)
from contour.infrastructure.postgres.workspace_repository import PostgresWorkspaceRepository
from contour.workspaces.application.ports import WorkspaceUnitOfWork


class PostgresWorkspaceTransactionManager:
    """Bind only the repositories required by workspace operations."""

    def __init__(self, engine: Engine) -> None:
        """Retain the process-owned pool; each operation checks out its own connection."""
        self._engine = engine

    @contextmanager
    def transaction(self) -> Iterator[WorkspaceUnitOfWork]:
        """Commit all operation writes together or roll back on failure."""
        scope = PostgresTransactionScope(self._engine, translate_error=translate_catalog_error)
        with scope.transaction() as connection:
            yield WorkspaceUnitOfWork(
                workspaces=PostgresWorkspaceRepository(connection),
                idempotency=PostgresIdempotencyRepository(connection),
            )
