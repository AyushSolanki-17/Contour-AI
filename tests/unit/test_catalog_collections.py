"""Application contracts for durable catalog collection orchestration."""

from __future__ import annotations

import hashlib
import json

import pytest

from contour.sources.application.errors import CatalogConflictError, IdempotencyConflictError
from contour.tenancy.application.collections import TenantCollectionService
from contour.tenancy.domain.access import Principal, PrincipalId


class _AbsentPrincipal:
    """Principal repository view for the transaction that loses the race."""

    def get_principal(self, _principal_id: object) -> None:
        """Report that the principal was not visible before the competing commit."""

    def save_principal(self, _principal: object) -> None:
        """Accept the attempted principal write until transaction completion."""


class _AcceptWrite:
    """Repository view that accepts a write before the simulated commit conflict."""

    def save_tenant(self, _tenant: object) -> None:
        """Accept the attempted tenant write."""

    def save_membership(self, _membership: object) -> None:
        """Accept the attempted membership write."""


class _ReplayRecords:
    """Operation-replay view with an optional committed winner."""

    def __init__(self, replay: tuple[str, dict[str, str | None]] | None) -> None:
        """Bind the replay returned by this transaction."""
        self._replay = replay

    def get_result(self, *_arguments: object) -> tuple[str, dict[str, str | None]] | None:
        """Return the configured concurrent winner, if present."""
        return self._replay

    def save_result(self, *_arguments: object) -> None:
        """Accept the attempted replay write until transaction completion."""


class _Transaction:
    """Minimal catalog transaction for an idempotency-race regression."""

    def __init__(
        self,
        replay: tuple[str, dict[str, str | None]] | None,
        *,
        conflict_on_exit: bool,
    ) -> None:
        """Compose the repository views needed by tenant creation."""
        self.principals = _AbsentPrincipal()
        self.tenants = _AcceptWrite()
        self.memberships = _AcceptWrite()
        self.idempotency = _ReplayRecords(replay)
        self._conflict_on_exit = conflict_on_exit

    def __enter__(self) -> _Transaction:
        """Return the already composed transaction view."""
        return self

    def __exit__(self, *_arguments: object) -> None:
        """Simulate a competing transaction winning the first commit."""
        if self._conflict_on_exit:
            raise CatalogConflictError()


class _Transactions:
    """Return a losing mutation followed by a committed replay read."""

    def __init__(self, replay: tuple[str, dict[str, str | None]]) -> None:
        """Retain the concurrent winner returned after the conflict."""
        self._replay = replay
        self._calls = 0

    def transaction(self) -> _Transaction:
        """Return the conflict scope first and winner-read scope second."""
        self._calls += 1
        return _Transaction(
            None if self._calls == 1 else self._replay,
            conflict_on_exit=self._calls == 1,
        )


def _digest(name: str) -> str:
    """Return the service's canonical digest for a tenant-creation input."""
    payload = json.dumps({"name": name}, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def test_concurrent_idempotency_loser_replays_the_committed_tenant() -> None:
    """An identical racing request returns the durable winner instead of a conflict."""
    winner = {
        "id": "TENANT:committed",
        "name": "Engineering",
    }
    service = TenantCollectionService(_Transactions((_digest("Engineering"), winner)))  # type: ignore[arg-type]

    tenant, replayed = service.create_tenant(
        Principal(PrincipalId("TEST", "principal")), "Engineering", "same-key"
    )

    assert replayed
    assert str(tenant.id) == "TENANT:committed"
    assert tenant.name == "Engineering"


def test_concurrent_idempotency_loser_rejects_a_different_payload() -> None:
    """A racing request cannot replay a winner accepted for different input."""
    winner = {"id": "TENANT:committed", "name": "Other"}
    service = TenantCollectionService(_Transactions((_digest("Other"), winner)))  # type: ignore[arg-type]

    with pytest.raises(IdempotencyConflictError):
        service.create_tenant(
            Principal(PrincipalId("TEST", "principal")), "Engineering", "same-key"
        )
