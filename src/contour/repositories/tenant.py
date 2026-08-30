"""Persistence contract for durable tenant ownership records."""

from __future__ import annotations

from typing import Protocol

from contour.domain.tenant import Tenant, TenantId


class TenantRepository(Protocol):
    """Reads and writes tenant records within an application transaction."""

    def get_tenant(self, tenant_id: TenantId) -> Tenant | None:
        """Return one tenant by stable identity, if it exists."""

    def save_tenant(self, tenant: Tenant) -> None:
        """Persist a new tenant or reject a conflicting identity."""
