"""FastAPI application assembly for the HTTP delivery adapter."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any, cast

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from contour import __version__
from contour.api.authentication import CredentialVerifier
from contour.api.cursor import CursorCodec
from contour.api.error_handler import register_exception_handlers
from contour.api.routes.catalog import create_catalog_router
from contour.api.routes.health import create_health_router
from contour.services.catalog_collections import CatalogCollectionService
from contour.services.health_service import HealthService

type AppLifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


def create_app(
    *,
    health_service: HealthService,
    catalog_service: CatalogCollectionService | None = None,
    credential_verifier: CredentialVerifier | None = None,
    cursor_secret: str = "contract-only-cursor-secret",
    lifespan: AppLifespan | None = None,
) -> FastAPI:
    """Create the HTTP adapter from constructed application services.

    Args:
        health_service: Framework-independent health use cases to expose.
        catalog_service: Optional authenticated catalog collection use cases.
        credential_verifier: Optional bearer-credential adapter for product routes.
        cursor_secret: Server-side secret used to bind collection cursor tokens.
        lifespan: Optional process-resource lifecycle owned by composition.

    Returns:
        A configured FastAPI application.
    """
    app = FastAPI(title="Contour", version=__version__, lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(create_health_router(health_service))
    if catalog_service is not None and credential_verifier is not None:
        app.include_router(
            create_catalog_router(catalog_service, credential_verifier, CursorCodec(cursor_secret))
        )
    app.openapi = _openapi_without_framework_validation_errors(app)  # type: ignore[method-assign]
    return app


def _openapi_without_framework_validation_errors(app: FastAPI) -> Callable[[], dict[str, Any]]:
    """Describe request validation through Contour's stable HTTP 422 envelope."""

    def render() -> dict[str, Any]:
        """Return and cache the generated schema with inaccurate HTTP 422 entries removed."""
        if app.openapi_schema is None:
            schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
            paths = cast(dict[str, dict[str, dict[str, Any]]], schema.get("paths", {}))
            for path_item in paths.values():
                for operation in path_item.values():
                    responses = cast(dict[str, dict[str, Any]], operation.get("responses", {}))
                    validation_response = responses.get("422")
                    if (
                        validation_response is not None
                        and validation_response.get("description") == "Validation Error"
                    ):
                        responses.pop("422")
            components = cast(dict[str, Any], schema.get("components", {}))
            schemas = cast(dict[str, Any], components.get("schemas", {}))
            schemas.pop("HTTPValidationError", None)
            schemas.pop("ValidationError", None)
            app.openapi_schema = schema
        return app.openapi_schema

    return render
