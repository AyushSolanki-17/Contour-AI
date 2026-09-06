"""Real database contracts for capability-scoped collection transactions."""

from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from psycopg import sql

from contour.composition.http import create_http_app
from contour.errors.catalog import CatalogPersistenceError
from contour.infrastructure.postgres.idempotency_repository import PostgresIdempotencyRepository
from contour.settings import Settings

pytestmark = pytest.mark.integration


@pytest.fixture
def collection_database(monkeypatch: pytest.MonkeyPatch) -> Iterator[Settings]:
    """Migrate one isolated database and remove only that database after the test."""
    settings = Settings.from_environment()
    database = f"contour_collections_test_{uuid4().hex}"
    maintenance_dsn = settings.database.dsn.rsplit("/", 1)[0] + "/postgres"
    with psycopg.connect(maintenance_dsn, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
        try:
            monkeypatch.setenv("CONTOUR_POSTGRES_DB", database)
            monkeypatch.setenv("CONTOUR_DEMO_CREDENTIALS", '{"test-token":"TEST:collections"}')
            command.upgrade(Config("alembic.ini"), "head")
            yield Settings.from_environment()
        finally:
            connection.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (database,),
            )
            connection.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(database)))


def test_composed_routes_replay_and_rollback_capability_writes(
    collection_database: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each mutation and replay record commit together through production HTTP wiring."""
    headers = {"Authorization": "Bearer test-token", "Idempotency-Key": "same-key"}
    app = create_http_app(collection_database)
    with TestClient(app) as client:
        assert client.get("/health/ready").status_code == 200
        tenant_path = "/api/v1/tenants"
        tenant = client.post(tenant_path, headers=headers, json={"name": "Engineering"})
        assert tenant.status_code == 201
        workspace_path = f"{tenant_path}/{tenant.json()['id']}/workspaces"
        workspace = client.post(workspace_path, headers=headers, json={"name": "Research"})
        assert workspace.status_code == 201
        source_path = f"{workspace_path}/{workspace.json()['id']}/sources"
        source_payload = {
            "connector_kind": "pep",
            "canonical_locator": "https://peps.python.org/pep-0723/",
            "scope": "public",
            "license": None,
            "data_classification": "public",
        }
        source = client.post(source_path, headers=headers, json=source_payload)
        assert source.status_code == 201
        requests = (
            (tenant_path, {"name": "Engineering"}, tenant),
            (workspace_path, {"name": "Research"}, workspace),
            (source_path, source_payload, source),
        )
        for path, payload, created in requests:
            replay = client.post(path, headers=headers, json=payload)
            assert replay.status_code == 200
            assert replay.json() == created.json()
            changed = (
                {**payload, "scope": "changed"} if path == source_path else {"name": "changed"}
            )
            conflict = client.post(path, headers=headers, json=changed)
            assert conflict.status_code == 409
            assert conflict.json()["error"]["code"] == "request.idempotency_conflict"

        def fail_replay_write(*_args: object, **_kwargs: object) -> None:
            raise CatalogPersistenceError()

        monkeypatch.setattr(PostgresIdempotencyRepository, "save_result", fail_replay_write)
        for path, payload, created in requests:
            candidate = (
                {**payload, "canonical_locator": "https://peps.python.org/pep-0722/"}
                if path == source_path
                else {"name": "Uncommitted"}
            )
            failed = client.post(
                path,
                headers={**headers, "Idempotency-Key": "failed-write"},
                json=candidate,
            )
            assert failed.status_code == 500
            assert failed.json()["error"]["code"] == "catalog.persistence_failed"
            assert client.get(path, headers=headers).json()["items"] == [created.json()]
