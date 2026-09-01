"""HTTP contracts for authenticated tenant-scoped catalog collections."""

from __future__ import annotations

from typing import cast

from fastapi.testclient import TestClient

from contour.api.app import create_app
from contour.domain.access import AccessContext, Membership, Principal, PrincipalId
from contour.domain.source import Source, SourceId
from contour.domain.tenant import Tenant, TenantId
from contour.domain.workspace import Workspace, WorkspaceId
from contour.infrastructure.authentication.static_credentials import StaticCredentialVerifier
from contour.services.catalog_collections import CatalogCollectionService
from contour.services.catalog_errors import UnsupportedConnectorError
from contour.services.health_service import HealthService
from contour.services.resource_errors import ResourceNotFoundError

_PRINCIPAL = Principal(PrincipalId("TEST", "catalog-client"))
_AUTHORIZATION = {"Authorization": "Bearer catalog-token"}


class _Ready:
    """Side-effect-free readiness dependency for HTTP contract checks."""

    def check(self) -> None:
        """Report that the contract-test dependency is ready."""


class _Catalog:
    """Deterministic application boundary used to isolate HTTP behavior."""

    def __init__(self) -> None:
        """Initialize one visible tenant with empty nested collections."""
        self.tenant = Tenant(TenantId("TENANT", "visible"), "Visible tenant")
        self.workspaces: list[Workspace] = []
        self.sources: list[Source] = []
        self.replayed_keys: set[str] = set()

    def create_tenant(self, principal: Principal, name: str, key: str) -> tuple[Tenant, bool]:
        """Return a deterministic tenant and signal repeated request keys."""
        assert principal == _PRINCIPAL
        self.tenant = Tenant(self.tenant.id, name)
        replayed = key in self.replayed_keys
        self.replayed_keys.add(key)
        return self.tenant, replayed

    def list_tenants(self, principal: Principal) -> tuple[Tenant, ...]:
        """Return the one tenant visible to the authenticated principal."""
        assert principal == _PRINCIPAL
        return (self.tenant,)

    def open_tenant(
        self, principal: Principal, tenant_id: TenantId, correlation_id: str
    ) -> AccessContext:
        """Return verified access only for the visible tenant."""
        assert principal == _PRINCIPAL
        assert correlation_id
        if tenant_id != self.tenant.id:
            raise ResourceNotFoundError()
        return AccessContext(principal, Membership(principal.id, tenant_id), correlation_id)

    def create_workspace(
        self, access: AccessContext, name: str, key: str
    ) -> tuple[Workspace, bool]:
        """Create one nested workspace and signal repeated request keys."""
        workspace = Workspace(
            WorkspaceId("WORKSPACE", "created"), access.tenant_id, name, str(access.principal.id)
        )
        replayed = key in self.replayed_keys
        self.replayed_keys.add(key)
        if not replayed:
            self.workspaces.append(workspace)
        return workspace, replayed

    def list_workspaces(self, access: AccessContext) -> tuple[Workspace, ...]:
        """Return workspaces in the verified tenant."""
        assert access.tenant_id == self.tenant.id
        return tuple(self.workspaces)

    def create_source(
        self,
        *,
        access: AccessContext,
        workspace_id: WorkspaceId,
        connector_kind: str,
        canonical_locator: str,
        scope: str,
        license_name: str | None,
        data_classification: str,
        idempotency_key: str,
    ) -> tuple[Source, bool]:
        """Create one source or reject an unsupported connector kind."""
        if connector_kind != "pep":
            raise UnsupportedConnectorError()
        if workspace_id not in {workspace.id for workspace in self.workspaces}:
            raise ResourceNotFoundError()
        source = Source(
            SourceId("SOURCE", "created"),
            access.tenant_id,
            workspace_id,
            canonical_locator,
            connector_kind,
            scope,
            license_name,
            data_classification,
        )
        replayed = idempotency_key in self.replayed_keys
        self.replayed_keys.add(idempotency_key)
        if not replayed:
            self.sources.append(source)
        return source, replayed

    def list_sources(self, access: AccessContext, workspace_id: WorkspaceId) -> tuple[Source, ...]:
        """Return sources only for a visible workspace."""
        if workspace_id not in {workspace.id for workspace in self.workspaces}:
            raise ResourceNotFoundError()
        return tuple(source for source in self.sources if source.tenant_id == access.tenant_id)


def _client(service: _Catalog | None = None) -> tuple[TestClient, _Catalog]:
    """Create an assembled HTTP adapter over deterministic dependencies."""
    catalog = service or _Catalog()
    app = create_app(
        health_service=HealthService(_Ready()),
        catalog_service=cast(CatalogCollectionService, catalog),
        credential_verifier=StaticCredentialVerifier({"catalog-token": _PRINCIPAL}),
        cursor_secret="catalog-contract-secret",
    )
    return TestClient(app), catalog


def test_health_is_public_while_every_catalog_route_requires_authentication() -> None:
    """The delivery boundary authenticates product routes but never health probes."""
    client, _ = _client()

    assert client.get("/health/live").status_code == 200
    response = client.get("/api/v1/tenants")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth.unauthenticated"
    assert response.headers["www-authenticate"] == "Bearer"


def test_tenant_create_replay_and_list_preserve_the_public_representation() -> None:
    """Tenant creation returns 201 once, 200 on replay, and remains listable."""
    client, _ = _client()
    headers = {**_AUTHORIZATION, "Idempotency-Key": "tenant-key"}

    created = client.post("/api/v1/tenants", headers=headers, json={"name": "Engineering"})
    replayed = client.post("/api/v1/tenants", headers=headers, json={"name": "Engineering"})
    listed = client.get("/api/v1/tenants", headers=_AUTHORIZATION)

    assert created.status_code == 201
    assert replayed.status_code == 200
    assert replayed.json() == created.json()
    assert listed.json() == {"items": [created.json()], "cursor": None}


def test_workspace_create_and_list_remain_nested_under_verified_tenant_access() -> None:
    """Workspace routes translate the tenant selector into verified application scope."""
    client, catalog = _client()
    path = f"/api/v1/tenants/{catalog.tenant.id}/workspaces"

    created = client.post(
        path,
        headers={**_AUTHORIZATION, "Idempotency-Key": "workspace-key"},
        json={"name": "Python"},
    )
    listed = client.get(path, headers=_AUTHORIZATION)

    assert created.status_code == 201
    assert created.json()["tenant_id"] == str(catalog.tenant.id)
    assert listed.json() == {"items": [created.json()], "cursor": None}


def test_source_create_and_list_keep_connector_fields_at_the_delivery_boundary() -> None:
    """Source-neutral request fields round-trip through the public catalog contract."""
    client, catalog = _client()
    workspace_path = f"/api/v1/tenants/{catalog.tenant.id}/workspaces"
    workspace = client.post(
        workspace_path,
        headers={**_AUTHORIZATION, "Idempotency-Key": "workspace-key"},
        json={"name": "Python"},
    ).json()
    source_path = f"{workspace_path}/{workspace['id']}/sources"
    payload = {
        "connector_kind": "pep",
        "canonical_locator": "https://peps.python.org/pep-0723/",
        "scope": "public",
        "license": "PSF-2.0",
        "data_classification": "public",
    }

    created = client.post(
        source_path,
        headers={**_AUTHORIZATION, "Idempotency-Key": "source-key"},
        json=payload,
    )
    listed = client.get(source_path, headers=_AUTHORIZATION)

    assert created.status_code == 201
    assert created.json() | {
        "id": "ignored",
        "tenant_id": "ignored",
        "workspace_id": "ignored",
    } == (payload | {"id": "ignored", "tenant_id": "ignored", "workspace_id": "ignored"})
    assert listed.json() == {"items": [created.json()], "cursor": None}


def test_cursor_is_opaque_and_cannot_be_replayed_for_another_tenant() -> None:
    """Signed pagination state remains bound to principal, tenant, route, and query shape."""
    client, catalog = _client()
    catalog.workspaces = [
        Workspace(WorkspaceId("WORKSPACE", str(index)), catalog.tenant.id, str(index), "owner")
        for index in range(3)
    ]
    path = f"/api/v1/tenants/{catalog.tenant.id}/workspaces"

    first = client.get(path, headers=_AUTHORIZATION, params={"limit": 2})
    cursor = first.json()["cursor"]
    second = client.get(path, headers=_AUTHORIZATION, params={"limit": 2, "cursor": cursor})
    foreign = client.get(
        "/api/v1/tenants/TENANT:foreign/workspaces",
        headers=_AUTHORIZATION,
        params={"limit": 2, "cursor": cursor},
    )

    assert cursor and "WORKSPACE:1" not in cursor
    assert [item["id"] for item in second.json()["items"]] == ["WORKSPACE:2"]
    assert foreign.status_code == 404
    assert foreign.json()["error"]["code"] == "resource.not_found"


def test_validation_unsupported_connectors_and_unknown_resources_use_stable_errors() -> None:
    """Distinct client failure classes retain their documented HTTP semantics."""
    client, catalog = _client()
    invalid = client.post(
        "/api/v1/tenants",
        headers={**_AUTHORIZATION, "Idempotency-Key": "bad key"},
        json={"name": ""},
    )
    missing = client.get("/api/v1/tenants/TENANT:missing/workspaces", headers=_AUTHORIZATION)
    workspace_path = f"/api/v1/tenants/{catalog.tenant.id}/workspaces"
    workspace = client.post(
        workspace_path,
        headers={**_AUTHORIZATION, "Idempotency-Key": "workspace-key"},
        json={"name": "Python"},
    ).json()
    unsupported = client.post(
        f"{workspace_path}/{workspace['id']}/sources",
        headers={**_AUTHORIZATION, "Idempotency-Key": "source-key"},
        json={
            "connector_kind": "unknown",
            "canonical_locator": "https://example.invalid",
            "scope": "public",
            "license": None,
            "data_classification": "public",
        },
    )

    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "request.invalid"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "resource.not_found"
    assert unsupported.status_code == 422
    assert unsupported.json()["error"]["code"] == "source.unsupported_connector"
