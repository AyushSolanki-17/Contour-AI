"""FastAPI application assembly for the HTTP delivery adapter."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI

from contour import __version__
from contour.api.error_handler import register_exception_handlers
from contour.api.routes.health import create_health_router
from contour.services.health_service import HealthService

type AppLifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


def create_app(
    *,
    health_service: HealthService,
    lifespan: AppLifespan | None = None,
) -> FastAPI:
    """Create the HTTP adapter from constructed application services.

    Args:
        health_service: Framework-independent health use cases to expose.
        lifespan: Optional process-resource lifecycle owned by composition.

    Returns:
        A configured FastAPI application.
    """
    app = FastAPI(title="Contour", version=__version__, lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(create_health_router(health_service))
    return app
