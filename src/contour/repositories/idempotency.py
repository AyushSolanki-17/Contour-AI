"""Durable idempotency records scoped to verified product access."""

from __future__ import annotations

from typing import Protocol

from contour.domain.access import Principal


class IdempotencyRepository(Protocol):
    """Stores replay-safe HTTP operation results in one transaction."""

    def get_response(
        self, principal: Principal, scope: str, route: str, key: str
    ) -> tuple[str, dict[str, str | None]] | None:
        """Return the request digest and original public response for one scoped key."""

    def save_response(
        self,
        principal: Principal,
        scope: str,
        route: str,
        key: str,
        payload_digest: str,
        response: dict[str, str | None],
    ) -> None:
        """Persist one accepted replay result atomically with its mutation."""
