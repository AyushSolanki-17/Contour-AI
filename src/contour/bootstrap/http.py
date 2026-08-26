"""Application composition roots for executable delivery adapters."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import Engine

from contour.api.app import AppLifespan, create_app
from contour.infrastructure.postgres.catalog_transaction import PostgresCatalogTransactionManager
from contour.infrastructure.postgres.engine import create_postgres_engine
from contour.infrastructure.postgres.readiness import PostgresReadinessProbe
from contour.infrastructure.source.pep import PepSourceRegistrationPolicy
from contour.observability.logging import configure_logging
from contour.services.health_service import HealthService, ReadinessProbe
from contour.services.workspace_source_service import WorkspaceSourceService
from contour.settings import Settings


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
    workspace_source_service = WorkspaceSourceService(
        PostgresCatalogTransactionManager(engine),
        (PepSourceRegistrationPolicy(),),
        local_owner="local-operator",
    )
    return create_app(
        health_service=health_service,
        workspace_source_service=workspace_source_service,
        lifespan=_database_lifespan(engine),
    )


def _database_lifespan(engine: Engine) -> AppLifespan:
    """Create a FastAPI lifespan that releases the process connection pool."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            engine.dispose()

    return lifespan


def create_app_from_environment() -> FastAPI:
    """Create the ASGI application from process environment settings.

    Returns:
        A fully composed HTTP application.

    Raises:
        ConfigurationError: If required environment configuration is invalid.
    """
    return create_http_app(Settings.from_environment())
