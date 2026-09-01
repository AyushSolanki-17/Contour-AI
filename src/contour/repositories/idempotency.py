"""Durable operation-replay records scoped to verified application access."""

from __future__ import annotations

from typing import Protocol

from contour.domain.access import Principal


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
