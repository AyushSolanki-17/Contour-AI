"""Translate framework-independent application errors into HTTP responses."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from contour.api.schemas.error import ErrorBody, ErrorDetail, ErrorResponse
from contour.errors import ApplicationError

_HTTP_STATUS_BY_ERROR_CODE = {
    "dependency.unavailable": HTTPStatus.SERVICE_UNAVAILABLE,
    "request.idempotency_conflict": HTTPStatus.CONFLICT,
    "source.already_registered": HTTPStatus.CONFLICT,
    "resource.not_found": HTTPStatus.NOT_FOUND,
    "source.unsupported_connector": HTTPStatus.UNPROCESSABLE_ENTITY,
    "auth.unauthenticated": HTTPStatus.UNAUTHORIZED,
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
        headers = {"WWW-Authenticate": "Bearer"} if error.code == "auth.unauthenticated" else None
        return JSONResponse(
            status_code=status_code,
            content=response.model_dump(mode="json", exclude_none=True),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        _request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        """Return safe field-level details through the common error envelope."""
        details = tuple(
            ErrorDetail(
                field=".".join(str(component) for component in item["loc"]),
                message=str(item["msg"]),
            )
            for item in error.errors()
        )
        response = ErrorResponse(
            error=ErrorBody(
                code="request.invalid",
                message="The request is invalid.",
                details=details,
            )
        )
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            content=response.model_dump(mode="json", exclude_none=True),
        )
