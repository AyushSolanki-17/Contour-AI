"""Top-level HTTP router registry."""

from __future__ import annotations

from fastapi import APIRouter

from contour.api.dependencies import ApiDependencies
from contour.api.routers.health import create_health_router
from contour.api.routers.v1.router import create_v1_router


def create_api_router(dependencies: ApiDependencies) -> APIRouter:
    """Build the complete HTTP route tree from constructed dependencies."""
    router = APIRouter()
    router.include_router(create_health_router(dependencies.health))
    router.include_router(create_v1_router(dependencies))
    return router
