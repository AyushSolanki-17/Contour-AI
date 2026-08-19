"""Application composition roots for executable delivery adapters."""

from __future__ import annotations

from fastapi import FastAPI

from contour.adapters.postgres import PostgresReadinessProbe
from contour.api.app import create_app
from contour.application.health import HealthService, ReadinessProbe
from contour.config import Settings
from contour.logging import configure_logging


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
    probe = (
        readiness_probe
        if readiness_probe is not None
        else PostgresReadinessProbe(settings.database)
    )
    health_service = HealthService(probe)
    return create_app(health_service=health_service)


def create_app_from_environment() -> FastAPI:
    """Create the ASGI application from process environment settings.

    Returns:
        A fully composed HTTP application.

    Raises:
        ConfigurationError: If required environment configuration is invalid.
    """
    return create_http_app(Settings.from_environment())
