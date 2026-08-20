"""Contract tests for process liveness and dependency readiness."""

from __future__ import annotations

from fastapi.testclient import TestClient

from contour.bootstrap import create_http_app
from contour.settings import Settings


class AvailableProbe:
    def check(self) -> None:
        return None


class UnavailableProbe:
    def check(self) -> None:
        raise OSError("database password must not be returned")


def settings() -> Settings:
    return Settings.from_environment(
        {
            "CONTOUR_POSTGRES_DB": "contour_test",
            "CONTOUR_POSTGRES_USER": "contour",
            "CONTOUR_POSTGRES_PASSWORD": "not-for-logs",
            "CONTOUR_POSTGRES_PORT": "5432",
        }
    )


def test_liveness_does_not_require_database_availability() -> None:
    client = TestClient(create_http_app(settings(), UnavailableProbe()))

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "live"}


def test_readiness_reports_available_required_dependency() -> None:
    client = TestClient(create_http_app(settings(), AvailableProbe()))

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_returns_stable_redacted_dependency_error() -> None:
    client = TestClient(create_http_app(settings(), UnavailableProbe()))

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "dependency.unavailable",
            "message": "A required dependency is unavailable.",
        }
    }
    assert "password" not in response.text
