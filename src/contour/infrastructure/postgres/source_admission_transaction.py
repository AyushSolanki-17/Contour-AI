"""PostgreSQL transactions for source admission operations."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine

from contour.infrastructure.postgres.evidence_repository import PostgresEvidenceRepository
from contour.infrastructure.postgres.source_repository import PostgresSourceRepository
from contour.infrastructure.postgres.source_version_repository import (
    PostgresSourceVersionRepository,
)
from contour.infrastructure.postgres.transaction_scope import (
    PostgresTransactionScope,
    translate_catalog_error,
)
from contour.infrastructure.postgres.workspace_repository import PostgresWorkspaceRepository
from contour.workflows.source_admission import SourceAdmissionUnitOfWork


class PostgresSourceAdmissionTransactionManager:
    """Bind only the repositories required by source admission operations."""

    def __init__(self, engine: Engine) -> None:
        """Retain the process-owned pool; each operation checks out its own connection."""
        self._engine = engine

    @contextmanager
    def transaction(self) -> Iterator[SourceAdmissionUnitOfWork]:
        """Commit all operation writes together or roll back on failure."""
        scope = PostgresTransactionScope(self._engine, translate_error=translate_catalog_error)
        with scope.transaction() as connection:
            yield SourceAdmissionUnitOfWork(
                workspaces=PostgresWorkspaceRepository(connection),
                sources=PostgresSourceRepository(connection),
                source_versions=PostgresSourceVersionRepository(connection),
                evidence=PostgresEvidenceRepository(connection),
            )
