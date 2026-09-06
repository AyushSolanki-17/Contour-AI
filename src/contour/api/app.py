"""FastAPI application assembly for Contour's public API."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any, cast

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from contour import __version__
from contour.api.dependencies import ApiDependencies
from contour.api.error_handler import register_exception_handlers
from contour.api.middleware import RequestContextMiddleware
from contour.api.routers import create_api_router

type AppLifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


def create_app(
    *,
    dependencies: ApiDependencies,
    lifespan: AppLifespan | None = None,
) -> FastAPI:
    """Create the API from one explicitly constructed dependency bundle.

    Args:
        dependencies: Process-scoped application services and delivery adapters.
        lifespan: Optional process-resource lifecycle owned by composition.

    Returns:
        A configured FastAPI application.
    """
    app = FastAPI(title="Contour", version=__version__, lifespan=lifespan)
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)
    app.include_router(create_api_router(dependencies))
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
