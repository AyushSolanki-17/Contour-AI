"""Application contracts for provider-neutral tenant access scopes."""

from __future__ import annotations

import pytest

from contour.errors import ResourceNotFoundError
from contour.tenancy.application.access import TenantAccessService
from contour.tenancy.domain.access import Membership, Principal, PrincipalId
from contour.tenancy.domain.tenant import Tenant, TenantId


class _Principals:
    """Small identity store used only to prove access-service behavior."""

    def __init__(self, records: dict[PrincipalId, Principal]) -> None:
        """Bind the store to its transaction-local records."""
        self._records = records

    def get_principal(self, principal_id: PrincipalId) -> Principal | None:
        """Return one stored principal, if present."""
        return self._records.get(principal_id)

    def save_principal(self, principal: Principal) -> None:
        """Store one previously unknown principal."""
        self._records[principal.id] = principal


class _Memberships:
    """Small membership store used only to prove tenant filtering."""

    def __init__(
        self,
        records: dict[tuple[PrincipalId, TenantId], Membership],
        tenants: dict[TenantId, Tenant],
    ) -> None:
        """Bind membership reads to transaction-local records."""
        self._records = records
        self._tenants = tenants

    def get_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> Membership | None:
        """Return one exact principal-to-tenant grant."""
        return self._records.get((principal_id, tenant_id))

    def list_tenants(self, principal_id: PrincipalId) -> tuple[Tenant, ...]:
        """Return only tenant records joined through the principal's grants."""
        return tuple(
            self._tenants[tenant_id]
            for stored_principal, tenant_id in sorted(
                self._records, key=lambda key: (key[1].namespace, key[1].value)
            )
            if stored_principal == principal_id
        )

    def save_membership(self, membership: Membership) -> None:
        """Store one new uniform authority grant."""
        self._records[(membership.principal_id, membership.tenant_id)] = membership


class _Tenants:
    """Small tenant store used only to prove atomic bootstrap inputs."""

    def __init__(self, records: dict[TenantId, Tenant]) -> None:
        """Bind the store to transaction-local tenant records."""
        self._records = records

    def save_tenant(self, tenant: Tenant) -> None:
        """Store the tenant that will receive the initiating membership."""
        self._records[tenant.id] = tenant


class _Transaction:
    """In-memory atomic boundary sufficient for access-service calls."""

    def __init__(self, manager: _Transactions) -> None:
        """Copy durable state before a potential write transaction."""
        self._manager = manager
        self._principal_records = manager.principal_records.copy()
        self._tenant_records = manager.tenant_records.copy()
        self._membership_records = manager.membership_records.copy()
        self.principals = _Principals(self._principal_records)
        self.tenants = _Tenants(self._tenant_records)
        self.memberships = _Memberships(self._membership_records, self._tenant_records)

    def __enter__(self) -> _Transaction:
        """Open the copied transaction state."""
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Publish all writes only when the operation succeeds."""
        if exc_type is None:
            self._manager.principal_records = self._principal_records
            self._manager.tenant_records = self._tenant_records
            self._manager.membership_records = self._membership_records


class _Transactions:
    """Creates isolated in-memory access transactions."""

    def __init__(self) -> None:
        """Initialize empty durable identity state."""
        self.principal_records: dict[PrincipalId, Principal] = {}
        self.tenant_records: dict[TenantId, Tenant] = {}
        self.membership_records: dict[tuple[PrincipalId, TenantId], Membership] = {}

    def transaction(self) -> _Transaction:
        """Return one fresh atomic transaction boundary."""
        return _Transaction(self)


def test_tenant_bootstrap_and_visibility_require_the_principals_own_membership() -> None:
    """Foreign and unknown tenant selectors share one non-enumerating outcome."""
    service = TenantAccessService(_Transactions())
    first = Principal(PrincipalId("TEST", "first"))
    second = Principal(PrincipalId("TEST", "second"))
    first_tenant = Tenant(TenantId("TENANT", "first"), "First")
    second_tenant = Tenant(TenantId("TENANT", "second"), "Second")

    first_access = service.bootstrap_tenant(
        principal=first, tenant=first_tenant, correlation_id="first-request"
    )
    service.bootstrap_tenant(
        principal=second, tenant=second_tenant, correlation_id="second-request"
    )

    assert first_access.tenant_id == first_tenant.id
    assert service.list_tenants(principal=first) == (first_tenant,)
    assert (
        service.open_tenant(
            principal=first, tenant_id=first_tenant.id, correlation_id="open-first"
        ).tenant_id
        == first_tenant.id
    )
    with pytest.raises(ResourceNotFoundError) as foreign:
        service.open_tenant(principal=first, tenant_id=second_tenant.id, correlation_id="foreign")
    with pytest.raises(ResourceNotFoundError) as unknown:
        service.open_tenant(
            principal=first,
            tenant_id=TenantId("TENANT", "missing"),
            correlation_id="unknown",
        )
    assert foreign.value.code == unknown.value.code == "resource.not_found"
