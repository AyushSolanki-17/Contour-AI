"""Tests for the typed, secret-safe runtime settings boundary."""

from __future__ import annotations

import pytest

from contour.application.errors import ConfigurationError
from contour.config import Settings


def valid_environment() -> dict[str, str]:
    return {
        "CONTOUR_POSTGRES_DB": "contour_test",
        "CONTOUR_POSTGRES_USER": "contour",
        "CONTOUR_POSTGRES_PASSWORD": "not-for-logs",
        "CONTOUR_POSTGRES_PORT": "5432",
    }


def test_settings_load_required_database_configuration() -> None:
    settings = Settings.from_environment(valid_environment())

    assert settings.database.host == "127.0.0.1"
    assert settings.database.port == 5432
    assert settings.database.dsn == "postgresql://contour:not-for-logs@127.0.0.1:5432/contour_test"


def test_settings_reject_missing_required_configuration() -> None:
    environment = valid_environment()
    del environment["CONTOUR_POSTGRES_PASSWORD"]

    with pytest.raises(ConfigurationError, match="CONTOUR_POSTGRES_PASSWORD"):
        Settings.from_environment(environment)


@pytest.mark.parametrize("port", ["invalid", "0", "65536"])
def test_settings_reject_invalid_database_port(port: str) -> None:
    environment = valid_environment()
    environment["CONTOUR_POSTGRES_PORT"] = port

    with pytest.raises(ConfigurationError, match="CONTOUR_POSTGRES_PORT"):
        Settings.from_environment(environment)


def test_settings_representation_does_not_expose_database_password() -> None:
    settings = Settings.from_environment(valid_environment())

    assert "not-for-logs" not in repr(settings)
