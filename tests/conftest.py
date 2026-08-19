"""Pytest selection safeguards for tests that need local infrastructure."""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Require an explicit opt-in before any test opens a database connection."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run tests that require the configured local PostgreSQL service",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Keep the default suite deterministic and independent of local services."""
    if config.getoption("--run-integration"):
        return

    skip_integration = pytest.mark.skip(
        reason="pass --run-integration to run local PostgreSQL tests"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
