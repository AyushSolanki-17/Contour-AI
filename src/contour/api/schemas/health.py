"""Public HTTP schemas for process health resources."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Health state returned by the HTTP delivery adapter."""

    model_config = ConfigDict(frozen=True)

    status: Literal["live", "ready"]
