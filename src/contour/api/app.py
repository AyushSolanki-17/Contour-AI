"""FastAPI application assembly for the HTTP delivery adapter."""

from __future__ import annotations

from fastapi import FastAPI

from contour import __version__
from contour.api.errors import register_exception_handlers
from contour.api.routes.health import create_health_router
from contour.application.health import HealthService


def create_app(*, health_service: HealthService) -> FastAPI:
    """Create the HTTP adapter from constructed application services.

    Args:
        health_service: Framework-independent health use cases to expose.

    Returns:
        A configured FastAPI application.
    """
    app = FastAPI(title="Contour", version=__version__)
    register_exception_handlers(app)
    app.include_router(create_health_router(health_service))
    return app
