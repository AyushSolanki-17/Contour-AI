"""Failure contracts for shared PostgreSQL transaction lifecycle mechanics."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError

from contour.errors import RecordPersistenceError
from contour.infrastructure.postgres.transaction_scope import PostgresTransactionScope


def test_connection_failure_does_not_leak_database_details() -> None:
    """Transaction startup exposes only a stable application error."""
    engine = Mock(spec=Engine)
    engine.connect.side_effect = OperationalError(
        "SELECT secret",
        {"password": "must-not-leak"},
        OSError("database host detail"),
    )

    with pytest.raises(RecordPersistenceError) as captured:
        PostgresTransactionScope(engine).open()

    assert captured.value.code == "records.persistence_failed"
    assert "must-not-leak" not in str(captured.value)
    assert "database host detail" not in str(captured.value)
