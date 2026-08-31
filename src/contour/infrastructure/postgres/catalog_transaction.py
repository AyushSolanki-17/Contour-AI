"""PostgreSQL transaction composition for catalog services."""

from __future__ import annotations

from types import TracebackType

from psycopg.errors import ForeignKeyViolation, UniqueViolation
from sqlalchemy import Connection, Engine
from sqlalchemy.engine import RootTransaction
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from contour.infrastructure.postgres.access_repository import (
    PostgresMembershipRepository,
    PostgresPrincipalRepository,
)
from contour.infrastructure.postgres.evidence_repository import PostgresEvidenceRepository
from contour.infrastructure.postgres.source_repository import PostgresSourceRepository
from contour.infrastructure.postgres.source_version_repository import (
    PostgresSourceVersionRepository,
)
from contour.infrastructure.postgres.tenant_repository import PostgresTenantRepository
from contour.infrastructure.postgres.workspace_repository import PostgresWorkspaceRepository
from contour.repositories.access import MembershipRepository, PrincipalRepository
from contour.repositories.catalog_transaction import CatalogUnitOfWork
from contour.repositories.evidence import EvidenceRepository
from contour.repositories.source import SourceRepository
from contour.repositories.source_version import SourceVersionRepository
from contour.repositories.tenant import TenantRepository
from contour.repositories.workspace import WorkspaceRepository
from contour.services.catalog_errors import (
    CatalogConflictError,
    CatalogPersistenceError,
    CatalogReferenceError,
)


class PostgresCatalogTransactionManager:
    """Factory for catalog transactions backed by a process-scoped engine."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the factory with an engine owned by the composition root."""
        self._engine = engine

    def transaction(self) -> CatalogUnitOfWork:
        """Create one unopened transaction scope for a catalog operation."""
        return PostgresCatalogUnitOfWork(self._engine)


class PostgresCatalogUnitOfWork:
    """Bind focused catalog repositories to one atomic database transaction."""

    def __init__(self, engine: Engine) -> None:
        """Initialize an unopened transaction scope for the supplied engine."""
        self._engine = engine
        self._connection: Connection | None = None
        self._transaction: RootTransaction | None = None
        self._tenants: TenantRepository | None = None
        self._principals: PrincipalRepository | None = None
        self._memberships: MembershipRepository | None = None
        self._workspaces: WorkspaceRepository | None = None
        self._sources: SourceRepository | None = None
        self._source_versions: SourceVersionRepository | None = None
        self._evidence: EvidenceRepository | None = None

    @property
    def tenants(self) -> TenantRepository:
        """Return the tenant repository in the active transaction."""
        return self._require_active(self._tenants, name="tenant repository")

    @property
    def principals(self) -> PrincipalRepository:
        """Return the principal repository in the active transaction."""
        return self._require_active(self._principals, name="principal repository")

    @property
    def memberships(self) -> MembershipRepository:
        """Return the membership repository in the active transaction."""
        return self._require_active(self._memberships, name="membership repository")

    @property
    def workspaces(self) -> WorkspaceRepository:
        """Return the workspace repository in the active transaction."""
        return self._require_active(self._workspaces, name="workspace repository")

    @property
    def sources(self) -> SourceRepository:
        """Return the source repository in the active transaction."""
        return self._require_active(self._sources, name="source repository")

    @property
    def source_versions(self) -> SourceVersionRepository:
        """Return the source-version repository in the active transaction."""
        return self._require_active(self._source_versions, name="source version repository")

    @property
    def evidence(self) -> EvidenceRepository:
        """Return the evidence repository in the active transaction."""
        return self._require_active(self._evidence, name="evidence repository")

    def __enter__(self) -> PostgresCatalogUnitOfWork:
        """Checkout one pooled connection and compose scoped repositories."""
        connection: Connection | None = None
        try:
            connection = self._engine.connect()
            transaction = connection.begin()
        except SQLAlchemyError as error:
            if connection is not None:
                connection.close()
            raise CatalogPersistenceError() from error

        self._connection = connection
        self._transaction = transaction
        self._tenants = PostgresTenantRepository(connection)
        self._principals = PostgresPrincipalRepository(connection)
        self._memberships = PostgresMembershipRepository(connection)
        self._workspaces = PostgresWorkspaceRepository(connection)
        self._sources = PostgresSourceRepository(connection)
        self._source_versions = PostgresSourceVersionRepository(connection)
        self._evidence = PostgresEvidenceRepository(connection)
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
        self._tenants = None
        self._principals = None
        self._memberships = None
        self._workspaces = None
        self._sources = None
        self._source_versions = None
        self._evidence = None

    @staticmethod
    def _require_active[T](resource: T | None, *, name: str) -> T:
        """Return an active scoped resource or reject out-of-scope access."""
        if resource is None:
            raise RuntimeError(f"catalog {name} requires an active transaction")
        return resource


def _translate_persistence_error(error: SQLAlchemyError) -> Exception:
    """Translate database failures into stable application errors."""
    if isinstance(error, IntegrityError) and isinstance(error.orig, UniqueViolation):
        return CatalogConflictError()
    if isinstance(error, IntegrityError) and isinstance(error.orig, ForeignKeyViolation):
        return CatalogReferenceError()
    return CatalogPersistenceError()
