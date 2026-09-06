"""PostgreSQL transactions for source operations."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine

from contour.infrastructure.postgres.idempotency_repository import PostgresIdempotencyRepository
from contour.infrastructure.postgres.source_repository import PostgresSourceRepository
from contour.infrastructure.postgres.source_version_repository import (
    PostgresSourceVersionRepository,
)
from contour.infrastructure.postgres.transaction_scope import (
    PostgresTransactionScope,
    translate_catalog_error,
)
from contour.infrastructure.postgres.workspace_repository import PostgresWorkspaceRepository
from contour.sources.application.ports import SourceUnitOfWork


class PostgresSourceTransactionManager:
    """Bind only the repositories required by source operations."""

    def __init__(self, engine: Engine) -> None:
        """Retain the process-owned pool; each operation checks out its own connection."""
        self._engine = engine

    @contextmanager
    def transaction(self) -> Iterator[SourceUnitOfWork]:
        """Commit all operation writes together or roll back on failure."""
        scope = PostgresTransactionScope(self._engine, translate_error=translate_catalog_error)
        with scope.transaction() as connection:
            yield SourceUnitOfWork(
                workspaces=PostgresWorkspaceRepository(connection),
                sources=PostgresSourceRepository(connection),
                source_versions=PostgresSourceVersionRepository(connection),
                idempotency=PostgresIdempotencyRepository(connection),
            )
