"""Provider-neutral identity, membership, and request access scope."""

from __future__ import annotations

from dataclasses import dataclass

from contour.domain.identifier_validation import require_identifier_value, require_namespace
from contour.domain.tenant import TenantId
from contour.domain.validation import require_text


@dataclass(frozen=True, slots=True)
class PrincipalId:
    """A stable provider-neutral authenticated subject identifier."""

    namespace: str
    value: str

    def __post_init__(self) -> None:
        """Reject malformed provider and subject identity components."""
        object.__setattr__(self, "namespace", require_namespace(self.namespace))
        object.__setattr__(self, "value", require_identifier_value(self.value, field_name="value"))

    def __str__(self) -> str:
        """Return the stable serialized principal identifier."""
        return f"{self.namespace}:{self.value}"


@dataclass(frozen=True, slots=True)
class Principal:
    """A verified authenticated subject without credential material."""

    id: PrincipalId

    def __post_init__(self) -> None:
        """Require a typed provider-neutral principal identity."""
        if not isinstance(self.id, PrincipalId):
            raise TypeError("id must be a PrincipalId")


@dataclass(frozen=True, slots=True)
class Membership:
    """A uniform authority grant from one principal to one tenant."""

    principal_id: PrincipalId
    tenant_id: TenantId

    def __post_init__(self) -> None:
        """Require typed principal and tenant ownership identities."""
        if not isinstance(self.principal_id, PrincipalId):
            raise TypeError("principal_id must be a PrincipalId")
        if not isinstance(self.tenant_id, TenantId):
            raise TypeError("tenant_id must be a TenantId")


@dataclass(frozen=True, slots=True)
class AccessContext:
    """Verified tenant scope carried by every product operation.

    This portable value deliberately excludes credentials and content. Future
    jobs, cursors, idempotency records, search, artifacts, logs, and traces
    carry its principal, tenant, and correlation identifiers.
    """

    principal: Principal
    membership: Membership
    correlation_id: str

    def __post_init__(self) -> None:
        """Require a membership that belongs to the authenticated principal."""
        if not isinstance(self.principal, Principal):
            raise TypeError("principal must be a Principal")
        if not isinstance(self.membership, Membership):
            raise TypeError("membership must be a Membership")
        if self.membership.principal_id != self.principal.id:
            raise ValueError("membership must belong to the principal")
        require_text(self.correlation_id, field_name="correlation_id")

    @property
    def tenant_id(self) -> TenantId:
        """Return the one verified tenant selected for this operation."""
        return self.membership.tenant_id

    def permits(self, tenant_id: TenantId) -> bool:
        """Return whether a tenant-owned record is inside this verified scope."""
        return self.tenant_id == tenant_id
