"""Contract drift coverage for the frontend-consumable OpenAPI artifact."""

from __future__ import annotations

import json
from pathlib import Path

from contour.api.app import create_app
from contour.services.health_service import HealthService


class AvailableProbe:
    def check(self) -> None:
        return None


def test_checked_in_openapi_matches_public_application_contract() -> None:
    contract_path = Path(__file__).resolve().parents[3] / "openapi" / "contour.openapi.json"
    checked_in_contract = json.loads(contract_path.read_text(encoding="utf-8"))

    app = create_app(health_service=HealthService(AvailableProbe()))

    assert checked_in_contract == app.openapi()
    assert set(checked_in_contract["paths"]) == {"/health/live", "/health/ready"}
