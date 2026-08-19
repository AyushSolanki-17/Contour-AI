"""Translate framework-independent application errors into HTTP responses."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from contour.api.schemas.errors import ErrorBody, ErrorResponse
from contour.application.errors import ApplicationError

_HTTP_STATUS_BY_ERROR_CODE = {
    "dependency.unavailable": HTTPStatus.SERVICE_UNAVAILABLE,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Install delivery-specific error translation.

    Args:
        app: FastAPI application that should handle application errors.
    """

    @app.exception_handler(ApplicationError)
    async def application_error_handler(_request: Request, error: ApplicationError) -> JSONResponse:
        """Translate a safe application error into its HTTP representation.

        Args:
            _request: Request that raised the error; intentionally unused.
            error: Framework-independent application error to translate.

        Returns:
            JSON response with a stable status and error envelope.
        """
        status_code = _HTTP_STATUS_BY_ERROR_CODE.get(
            error.code,
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
        response = ErrorResponse(error=ErrorBody(code=error.code, message=error.message))
        return JSONResponse(status_code=status_code, content=response.model_dump(mode="json"))
