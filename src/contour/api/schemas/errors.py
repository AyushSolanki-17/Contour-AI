"""Stable public HTTP error schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ErrorBody(BaseModel):
    """A safe machine-readable error exposed to API clients."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str


class ErrorResponse(BaseModel):
    """The common HTTP error envelope."""

    model_config = ConfigDict(frozen=True)

    error: ErrorBody
