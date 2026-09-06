"""Version one product route registry."""

from __future__ import annotations

from fastapi import APIRouter

from contour.api.dependencies import ApiDependencies
from contour.api.routers.v1.sources import create_sources_router
from contour.api.routers.v1.tenants import create_tenants_router
from contour.api.routers.v1.workspaces import create_workspaces_router


def create_v1_router(dependencies: ApiDependencies) -> APIRouter:
    """Build the version one product API under its public URL prefix."""
    router = APIRouter(prefix="/api/v1", tags=["product"])
    router.include_router(
        create_tenants_router(dependencies.tenants, dependencies.credentials, dependencies.cursors)
    )
    router.include_router(
        create_workspaces_router(
            dependencies.tenants,
            dependencies.workspaces,
            dependencies.credentials,
            dependencies.cursors,
        )
    )
    router.include_router(
        create_sources_router(
            dependencies.tenants,
            dependencies.sources,
            dependencies.credentials,
            dependencies.cursors,
        )
    )
    return router
