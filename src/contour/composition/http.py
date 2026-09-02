"""Application composition roots for executable delivery adapters."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import Engine

from contour.api.app import AppLifespan, create_app
from contour.api.health import HealthService, ReadinessProbe
from contour.infrastructure.authentication.static_credentials import StaticCredentialVerifier
from contour.infrastructure.postgres.catalog_transaction import PostgresCatalogTransactionManager
from contour.infrastructure.postgres.engine import create_postgres_engine
from contour.infrastructure.postgres.readiness import PostgresReadinessProbe
from contour.observability.logging import configure_logging
from contour.settings import Settings
from contour.sources.application.registration import SourceCollectionService
from contour.tenancy.application.collections import TenantCollectionService
from contour.tenancy.domain.access import Principal, PrincipalId
from contour.workspaces.application.collections import WorkspaceCollectionService


def create_http_app(
    settings: Settings,
    readiness_probe: ReadinessProbe | None = None,
) -> FastAPI:
    """Construct process-scoped dependencies and bind them to FastAPI.

    Args:
        settings: Validated runtime settings.
        readiness_probe: Optional adapter override for tests or another runtime.

    Returns:
        A fully composed HTTP application.
    """
    configure_logging(secrets=settings.database.redaction_values)
    engine = create_postgres_engine(settings.database)
    probe = readiness_probe or PostgresReadinessProbe(engine)
    health_service = HealthService(probe)
    transactions = PostgresCatalogTransactionManager(engine)
    verifier = StaticCredentialVerifier(_configured_principals(settings.demo_credentials))
    return create_app(
        health_service=health_service,
        tenant_service=TenantCollectionService(transactions),
        workspace_service=WorkspaceCollectionService(transactions),
        source_service=SourceCollectionService(transactions, frozenset({"pep"})),
        credential_verifier=verifier,
        cursor_secret=settings.cursor_signing_secret,
        lifespan=_database_lifespan(engine),
    )


def _database_lifespan(engine: Engine) -> AppLifespan:
    """Create a FastAPI lifespan that releases the process connection pool."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        """Dispose the application-owned database pool during ASGI shutdown.

        Yields:
            Control to FastAPI while process-scoped dependencies are available.
        """
        try:
            yield
        finally:
            engine.dispose()

    return lifespan


def _configured_principals(credentials: dict[str, str]) -> dict[str, Principal]:
    """Convert validated opaque settings into domain principals at composition."""
    return {
        token: Principal(PrincipalId(*serialized_id.rsplit(":", 1)))
        for token, serialized_id in credentials.items()
    }


def create_app_from_environment() -> FastAPI:
    """Create the ASGI application from process environment settings.

    Returns:
        A fully composed HTTP application.

    Raises:
        ConfigurationError: If required environment configuration is invalid.
    """
    return create_http_app(Settings.from_environment())
