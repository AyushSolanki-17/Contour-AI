"""Contract drift coverage for the frontend-consumable OpenAPI artifact."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from contour.api.app import create_app
from contour.api.cursor import CursorCodec
from contour.api.dependencies import ApiDependencies
from contour.api.health import HealthService
from contour.infrastructure.authentication.static_credentials import StaticCredentialVerifier
from contour.sources.application.ports import SourceTransactionManager
from contour.sources.application.registration import SourceCollectionService
from contour.tenancy.application.collections import TenantCollectionService
from contour.tenancy.application.ports import TenantTransactionManager
from contour.workspaces.application.collections import WorkspaceCollectionService
from contour.workspaces.application.ports import WorkspaceTransactionManager


class AvailableProbe:
    def check(self) -> None:
        return None


def test_checked_in_openapi_matches_public_application_contract() -> None:
    contract_path = Path(__file__).resolve().parents[3] / "openapi" / "contour.openapi.json"
    checked_in_contract = json.loads(contract_path.read_text(encoding="utf-8"))

    app = create_app(
        dependencies=ApiDependencies(
            health=HealthService(AvailableProbe()),
            tenants=TenantCollectionService(cast(TenantTransactionManager, object())),
            workspaces=WorkspaceCollectionService(cast(WorkspaceTransactionManager, object())),
            sources=SourceCollectionService(
                cast(SourceTransactionManager, object()), frozenset({"pep"})
            ),
            credentials=StaticCredentialVerifier({}),
            cursors=CursorCodec("contract-only-cursor-secret"),
        ),
    )

    assert checked_in_contract == app.openapi()
    assert set(checked_in_contract["paths"]) == {
        "/health/live",
        "/health/ready",
        "/api/v1/tenants",
        "/api/v1/tenants/{tenant_id}/workspaces",
        "/api/v1/tenants/{tenant_id}/workspaces/{workspace_id}/sources",
    }
