"""PostgreSQL transactions for tenant operations."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine

from contour.infrastructure.postgres.access_repository import (
    PostgresMembershipRepository,
    PostgresPrincipalRepository,
)
from contour.infrastructure.postgres.idempotency_repository import PostgresIdempotencyRepository
from contour.infrastructure.postgres.tenant_repository import PostgresTenantRepository
from contour.infrastructure.postgres.transaction_scope import (
    PostgresTransactionScope,
    translate_catalog_error,
)
from contour.tenancy.application.ports import TenantUnitOfWork


class PostgresTenantTransactionManager:
    """Bind only the repositories required by tenant operations."""

    def __init__(self, engine: Engine) -> None:
        """Retain the process-owned pool; each operation checks out its own connection."""
        self._engine = engine

    @contextmanager
    def transaction(self) -> Iterator[TenantUnitOfWork]:
        """Commit all operation writes together or roll back on failure."""
        scope = PostgresTransactionScope(self._engine, translate_error=translate_catalog_error)
        with scope.transaction() as connection:
            yield TenantUnitOfWork(
                tenants=PostgresTenantRepository(connection),
                principals=PostgresPrincipalRepository(connection),
                memberships=PostgresMembershipRepository(connection),
                idempotency=PostgresIdempotencyRepository(connection),
            )
