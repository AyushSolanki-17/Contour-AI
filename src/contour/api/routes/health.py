"""HTTP controllers for process health resources."""

from __future__ import annotations

from fastapi import APIRouter

from contour.api.health import HealthService
from contour.api.schemas.error import ErrorResponse
from contour.api.schemas.health import HealthResponse


def create_health_router(health_service: HealthService) -> APIRouter:
    """Bind health use cases to HTTP without constructing dependencies.

    Args:
        health_service: Application service used by the health endpoints.

    Returns:
        A router containing liveness and readiness endpoints.
    """
    router = APIRouter(prefix="/health", tags=["health"])

    @router.get("/live", response_model=HealthResponse)
    def live() -> HealthResponse:
        """Return process liveness without checking external dependencies.

        Returns:
            HTTP response model reporting the live state.
        """
        status = health_service.liveness()
        return HealthResponse(status=status.status)

    @router.get(
        "/ready",
        response_model=HealthResponse,
        responses={503: {"model": ErrorResponse}},
    )
    def ready() -> HealthResponse:
        """Return readiness after checking required dependencies.

        Returns:
            HTTP response model reporting the ready state.

        Raises:
            DependencyUnavailableError: Translated globally into HTTP 503.
        """
        status = health_service.readiness()
        return HealthResponse(status=status.status)

    return router
