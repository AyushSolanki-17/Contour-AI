"""Failure contracts for catalog infrastructure boundaries."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError

from contour.infrastructure.postgres.catalog_transaction import (
    PostgresCatalogTransactionManager,
)
from contour.sources.application.errors import CatalogPersistenceError


def test_connection_failure_does_not_leak_database_details() -> None:
    """Connection errors cross into application code only through a safe contract."""
    engine = Mock(spec=Engine)
    engine.connect.side_effect = OperationalError(
        "SELECT secret",
        {"password": "must-not-leak"},
        OSError("database host detail"),
    )

    with pytest.raises(CatalogPersistenceError) as captured:
        with PostgresCatalogTransactionManager(engine).transaction():
            pass

    assert captured.value.code == "catalog.persistence_failed"
    assert "must-not-leak" not in str(captured.value)
    assert "database host detail" not in str(captured.value)
