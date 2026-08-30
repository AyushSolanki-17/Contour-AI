"""Stable public HTTP error schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    """One safe field-level reason that an API request was rejected."""

    model_config = ConfigDict(frozen=True)

    field: str
    message: str


class ErrorBody(BaseModel):
    """A safe machine-readable error exposed to API clients."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    details: tuple[ErrorDetail, ...] | None = None


class ErrorResponse(BaseModel):
    """The common HTTP error envelope."""

    model_config = ConfigDict(frozen=True)

    error: ErrorBody
