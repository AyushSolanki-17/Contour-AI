"""Contract drift coverage for the frontend-consumable OpenAPI artifact."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from contour.api.app import create_app
from contour.infrastructure.authentication.static_credentials import StaticCredentialVerifier
from contour.repositories.catalog_transaction import CatalogTransactionManager
from contour.services.health_service import HealthService
from contour.services.source_collections import SourceCollectionService
from contour.services.tenant_collections import TenantCollectionService
from contour.services.workspace_collections import WorkspaceCollectionService


class AvailableProbe:
    def check(self) -> None:
        return None


def test_checked_in_openapi_matches_public_application_contract() -> None:
    contract_path = Path(__file__).resolve().parents[3] / "openapi" / "contour.openapi.json"
    checked_in_contract = json.loads(contract_path.read_text(encoding="utf-8"))

    app = create_app(
        health_service=HealthService(AvailableProbe()),
        tenant_service=TenantCollectionService(cast(CatalogTransactionManager, object())),
        workspace_service=WorkspaceCollectionService(cast(CatalogTransactionManager, object())),
        source_service=SourceCollectionService(
            cast(CatalogTransactionManager, object()), frozenset({"pep"})
        ),
        credential_verifier=StaticCredentialVerifier({}),
    )

    assert checked_in_contract == app.openapi()
    assert set(checked_in_contract["paths"]) == {
        "/health/live",
        "/health/ready",
        "/api/v1/tenants",
        "/api/v1/tenants/{tenant_id}/workspaces",
        "/api/v1/tenants/{tenant_id}/workspaces/{workspace_id}/sources",
    }
