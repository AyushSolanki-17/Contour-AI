"""The minimal Phase 0 FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from contour.adapters.postgres import PostgresReadinessProbe
from contour.application.errors import ApplicationError
from contour.application.health import HealthService, ReadinessProbe
from contour.config import Settings
from contour.logging import configure_logging


def create_app(settings: Settings, readiness_probe: ReadinessProbe | None = None) -> FastAPI:
    """Create the HTTP application with validated settings and health routes."""
    configure_logging(secrets=settings.database.redaction_values)
    health_service = HealthService(readiness_probe or PostgresReadinessProbe(settings.database))
    app = FastAPI(title="Contour", version="0.0.1")

    @app.exception_handler(ApplicationError)
    async def application_error_handler(_request: Request, error: ApplicationError) -> JSONResponse:
        status_code = 503 if error.code == "dependency.unavailable" else 500
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": error.code, "message": error.message}},
        )

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": health_service.liveness().status}

    @app.get("/health/ready")
    def ready() -> dict[str, str]:
        return {"status": health_service.readiness().status}

    return app


def create_app_from_environment() -> FastAPI:
    """ASGI factory that fails clearly when required configuration is invalid."""
    settings = Settings.from_environment()
    return create_app(settings)
