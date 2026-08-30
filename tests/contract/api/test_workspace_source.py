"""Public contract coverage for trusted-local workspace and source operations."""

from __future__ import annotations

from types import TracebackType
from typing import Self

from fastapi.testclient import TestClient

from contour.api.app import create_app
from contour.domain.source import Source, SourceId
from contour.domain.tenant import Tenant, TenantId
from contour.domain.workspace import Workspace, WorkspaceId
from contour.infrastructure.source.pep import PepSourceRegistrationPolicy
from contour.repositories.catalog_transaction import CatalogUnitOfWork
from contour.repositories.evidence import EvidenceRepository
from contour.repositories.source import SourceRepository
from contour.repositories.source_version import SourceVersionRepository
from contour.repositories.tenant import TenantRepository
from contour.repositories.workspace import WorkspaceRepository
from contour.services.catalog_errors import CatalogConflictError, CatalogPersistenceError
from contour.services.health_service import HealthService
from contour.services.workspace_source_service import WorkspaceSourceService

_WORKSPACE_ID = "WORKSPACE:maintainers"
_OTHER_WORKSPACE_ID = "WORKSPACE:reviewers"
_SOURCE_ID = "SOURCE:PEP:723"
_SOURCE_BODY = {
    "source_type": "pep",
    "canonical_locator": "https://peps.python.org/pep-0723/",
    "scope": "public",
    "license": "PSF-2.0",
    "data_classification": "public",
}


class AvailableProbe:
    def check(self) -> None:
        return None


class MemoryWorkspaceRepository:
    def __init__(self, records: dict[WorkspaceId, Workspace]) -> None:
        self._records = records

    def get_workspace(self, workspace_id: WorkspaceId) -> Workspace | None:
        return self._records.get(workspace_id)

    def save_workspace(self, workspace: Workspace) -> None:
        if workspace.id in self._records:
            raise CatalogConflictError()
        self._records[workspace.id] = workspace


class MemoryTenantRepository:
    """Stores trusted-local tenant records for one test transaction."""

    def __init__(self, records: dict[TenantId, Tenant]) -> None:
        """Bind the repository to copied transaction state."""
        self._records = records

    def get_tenant(self, tenant_id: TenantId) -> Tenant | None:
        """Return a stored tenant, if present."""
        return self._records.get(tenant_id)

    def save_tenant(self, tenant: Tenant) -> None:
        """Store one new tenant or reject its duplicate identity."""
        if tenant.id in self._records:
            raise CatalogConflictError()
        self._records[tenant.id] = tenant


class MemorySourceRepository:
    def __init__(self, records: dict[SourceId, Source]) -> None:
        self._records = records

    def get_source(self, source_id: SourceId) -> Source | None:
        return self._records.get(source_id)

    def save_source(self, source: Source) -> None:
        if source.id in self._records:
            raise CatalogConflictError()
        self._records[source.id] = source


class MemoryTransaction:
    def __init__(self, manager: MemoryTransactionManager) -> None:
        self._manager = manager
        self._tenant_records = manager.tenant_records.copy()
        self._workspace_records = manager.workspace_records.copy()
        self._source_records = manager.source_records.copy()
        self._workspaces = MemoryWorkspaceRepository(self._workspace_records)
        self._tenants = MemoryTenantRepository(self._tenant_records)
        self._sources = MemorySourceRepository(self._source_records)

    @property
    def tenants(self) -> TenantRepository:
        """Return the tenant repository for this test transaction."""
        return self._tenants

    @property
    def workspaces(self) -> WorkspaceRepository:
        return self._workspaces

    @property
    def sources(self) -> SourceRepository:
        return self._sources

    @property
    def source_versions(self) -> SourceVersionRepository:
        raise AssertionError("product API must not access source versions")

    @property
    def evidence(self) -> EvidenceRepository:
        raise AssertionError("product API must not access evidence")

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self._manager.tenant_records = self._tenant_records
            self._manager.workspace_records = self._workspace_records
            self._manager.source_records = self._source_records


class MemoryTransactionManager:
    def __init__(self) -> None:
        self.tenant_records: dict[TenantId, Tenant] = {}
        self.workspace_records: dict[WorkspaceId, Workspace] = {}
        self.source_records: dict[SourceId, Source] = {}

    def transaction(self) -> MemoryTransaction:
        return MemoryTransaction(self)


class BrokenTransactionManager:
    def transaction(self) -> CatalogUnitOfWork:
        raise CatalogPersistenceError()


def _client(manager: MemoryTransactionManager | BrokenTransactionManager) -> TestClient:
    service = WorkspaceSourceService(
        manager,
        (PepSourceRegistrationPolicy(),),
        local_tenant=Tenant(TenantId("TENANT:LOCAL", "default"), "Trusted local tenant"),
        local_owner="local-operator",
    )
    return TestClient(
        create_app(
            health_service=HealthService(AvailableProbe()),
            workspace_source_service=service,
        )
    )


def test_client_can_create_open_and_exactly_replay_workspace_and_source() -> None:
    client = _client(MemoryTransactionManager())

    workspace = client.put(f"/api/v1/workspaces/{_WORKSPACE_ID}", json={"name": "Maintainers"})
    replayed_workspace = client.put(
        f"/api/v1/workspaces/{_WORKSPACE_ID}", json={"name": "Maintainers"}
    )
    source = client.put(
        f"/api/v1/workspaces/{_WORKSPACE_ID}/sources/{_SOURCE_ID}", json=_SOURCE_BODY
    )
    replayed_source = client.put(
        f"/api/v1/workspaces/{_WORKSPACE_ID}/sources/{_SOURCE_ID}", json=_SOURCE_BODY
    )

    assert workspace.status_code == replayed_workspace.status_code == 200
    assert (
        workspace.json()
        == replayed_workspace.json()
        == {
            "id": _WORKSPACE_ID,
            "name": "Maintainers",
            "owner": "local-operator",
        }
    )
    assert client.get(f"/api/v1/workspaces/{_WORKSPACE_ID}").json() == workspace.json()
    assert source.status_code == replayed_source.status_code == 200
    assert (
        source.json()
        == replayed_source.json()
        == {
            "id": _SOURCE_ID,
            "workspace_id": _WORKSPACE_ID,
            **_SOURCE_BODY,
        }
    )
    assert (
        client.get(f"/api/v1/workspaces/{_WORKSPACE_ID}/sources/{_SOURCE_ID}").json()
        == source.json()
    )


def test_identity_conflicts_do_not_mutate_and_cross_workspace_access_is_hidden() -> None:
    client = _client(MemoryTransactionManager())
    for workspace_id, name in ((_WORKSPACE_ID, "Maintainers"), (_OTHER_WORKSPACE_ID, "Reviewers")):
        assert (
            client.put(f"/api/v1/workspaces/{workspace_id}", json={"name": name}).status_code == 200
        )
    assert (
        client.put(
            f"/api/v1/workspaces/{_WORKSPACE_ID}/sources/{_SOURCE_ID}", json=_SOURCE_BODY
        ).status_code
        == 200
    )

    workspace_conflict = client.put(f"/api/v1/workspaces/{_WORKSPACE_ID}", json={"name": "Changed"})
    source_conflict = client.put(
        f"/api/v1/workspaces/{_WORKSPACE_ID}/sources/{_SOURCE_ID}",
        json=_SOURCE_BODY | {"license": "changed"},
    )
    scoped_missing = client.get(f"/api/v1/workspaces/{_OTHER_WORKSPACE_ID}/sources/{_SOURCE_ID}")
    absent = client.get(f"/api/v1/workspaces/{_OTHER_WORKSPACE_ID}/sources/SOURCE:PEP:9999")

    assert workspace_conflict.status_code == source_conflict.status_code == 409
    assert workspace_conflict.json()["error"]["code"] == "resource.conflict"
    assert source_conflict.json()["error"]["code"] == "resource.conflict"
    assert client.get(f"/api/v1/workspaces/{_WORKSPACE_ID}").json()["name"] == "Maintainers"
    assert (
        client.get(f"/api/v1/workspaces/{_WORKSPACE_ID}/sources/{_SOURCE_ID}").json()["license"]
        == "PSF-2.0"
    )
    assert scoped_missing.status_code == absent.status_code == 404
    assert scoped_missing.json() == absent.json()


def test_invalid_and_unsupported_inputs_use_stable_safe_errors() -> None:
    client = _client(MemoryTransactionManager())

    invalid_path = client.put("/api/v1/workspaces/not-canonical", json={"name": "Name"})
    invalid_body = client.put(f"/api/v1/workspaces/{_WORKSPACE_ID}", json={"name": ""})
    client.put(f"/api/v1/workspaces/{_WORKSPACE_ID}", json={"name": "Maintainers"})
    unsupported = client.put(
        f"/api/v1/workspaces/{_WORKSPACE_ID}/sources/SOURCE:OTHER:one",
        json=_SOURCE_BODY
        | {
            "source_type": "other",
            "canonical_locator": "https://example.invalid/source",
        },
    )

    assert invalid_path.status_code == invalid_body.status_code == 400
    assert invalid_path.json()["error"]["code"] == "request.invalid"
    assert invalid_path.json()["error"]["details"][0]["field"] == "path.workspace_id"
    assert invalid_body.json()["error"]["details"][0]["field"] == "body.name"
    assert unsupported.status_code == 422
    assert unsupported.json() == {
        "error": {
            "code": "source.unsupported",
            "message": "The source configuration is not supported.",
        }
    }


def test_catalog_dependency_failure_is_redacted_and_stable() -> None:
    client = _client(BrokenTransactionManager())

    response = client.put(f"/api/v1/workspaces/{_WORKSPACE_ID}", json={"name": "Maintainers"})

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "dependency.unavailable",
            "message": "A required dependency is unavailable.",
        }
    }
    assert "catalog" not in response.text


def test_openapi_publishes_only_the_bounded_workspace_source_contract() -> None:
    application = create_app(
        health_service=HealthService(AvailableProbe()),
        workspace_source_service=WorkspaceSourceService(
            MemoryTransactionManager(),
            (PepSourceRegistrationPolicy(),),
            local_tenant=Tenant(TenantId("TENANT:LOCAL", "default"), "Trusted local tenant"),
            local_owner="local-operator",
        ),
    )
    contract = application.openapi()
    product_paths = {path: value for path, value in contract["paths"].items() if "/api/v1" in path}

    assert set(product_paths) == {
        "/api/v1/workspaces/{workspace_id}",
        "/api/v1/workspaces/{workspace_id}/sources/{source_id}",
    }
    assert all(set(path_item) == {"get", "put"} for path_item in product_paths.values())
    assert "securitySchemes" not in contract.get("components", {})
    source_request = contract["components"]["schemas"]["SourcePutRequest"]
    assert "enum" not in source_request["properties"]["source_type"]
    assert "HTTPValidationError" not in contract["components"]["schemas"]
    assert set(product_paths["/api/v1/workspaces/{workspace_id}"]["put"]["responses"]) == {
        "200",
        "400",
        "409",
        "503",
    }
