"""Durable operation-replay records scoped to verified application access."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from json import dumps
from typing import Protocol

from contour.errors.application import ApplicationError
from contour.tenancy.domain.access import Principal


class IdempotencyRepository(Protocol):
    """Stores replay-safe application operation results in one transaction."""

    def get_result(
        self, principal: Principal, scope: str, operation: str, key: str
    ) -> tuple[str, dict[str, str | None]] | None:
        """Return the input digest and accepted result for one scoped key."""

    def save_result(
        self,
        principal: Principal,
        scope: str,
        operation: str,
        key: str,
        payload_digest: str,
        result: dict[str, str | None],
    ) -> None:
        """Persist one accepted operation result atomically with its mutation."""


class IdempotencyConflictError(ApplicationError):
    """Raised when an operation key is reused with different input."""

    def __init__(self) -> None:
        """Create a conflict that does not disclose the original input."""
        super().__init__(
            code="request.idempotency_conflict",
            message="The idempotency key was already used for a different request.",
        )


def request_digest(payload: Mapping[str, str | None]) -> str:
    """Hash canonical request JSON without changing the durable replay format."""
    return sha256(dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
