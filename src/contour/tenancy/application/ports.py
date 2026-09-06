"""Persistence contracts for provider-neutral principals and memberships."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from contour.idempotency import IdempotencyRepository
from contour.tenancy.domain.access import Membership, Principal, PrincipalId
from contour.tenancy.domain.tenant import Tenant, TenantId


class PrincipalRepository(Protocol):
    """Reads and writes verified principal identities within a transaction."""

    def get_principal(self, principal_id: PrincipalId) -> Principal | None:
        """Return one principal by provider-neutral identity, if present."""

    def save_principal(self, principal: Principal) -> None:
        """Persist one principal or reject an identity conflict."""


class MembershipRepository(Protocol):
    """Reads and writes uniform principal-to-tenant grants within a transaction."""

    def get_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> Membership | None:
        """Return one exact authority grant, if present."""

    def list_tenants(self, principal_id: PrincipalId) -> tuple[Tenant, ...]:
        """Return only tenants visible to a principal in deterministic order."""

    def save_membership(self, membership: Membership) -> None:
        """Persist one authority grant or reject a duplicate."""


class TenantRepository(Protocol):
    """Reads and writes tenant records within an application transaction."""

    def get_tenant(self, tenant_id: TenantId) -> Tenant | None:
        """Return one tenant by stable identity, if it exists."""

    def save_tenant(self, tenant: Tenant) -> None:
        """Persist a new tenant or reject a conflicting identity."""


@dataclass(frozen=True)
class TenantUnitOfWork:
    """Repositories sharing one transaction for tenancy operations."""

    tenants: TenantRepository
    principals: PrincipalRepository
    memberships: MembershipRepository
    idempotency: IdempotencyRepository


class TenantTransactionManager(Protocol):
    """Open an atomic tenancy operation, including its durable replay record."""

    def transaction(self) -> AbstractContextManager[TenantUnitOfWork]:
        """Commit on success and roll back all writes on failure."""
