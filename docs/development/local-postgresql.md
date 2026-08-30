# Local PostgreSQL

**Status:** implemented local-development runtime
**Updated:** 2026-08-19

Contour's Phase 0 development database is a single local Docker Compose service.
It is not a production deployment, and it does not create application schemas or
configure application settings.

## Prerequisites

- Docker Engine with the Docker Compose plugin;
- a free local TCP port (the example uses `5432`); and
- the repository's pinned [`compose.yaml`](../../compose.yaml).

## Configure and start

Create an ignored local configuration file from the tracked example, then set a
development-only password:

```shell
cp .env.example .env
```

The same variables are the backend's required database configuration. The
optional `CONTOUR_POSTGRES_HOST` defaults to `127.0.0.1`; keep it aligned with
the loopback-only Compose listener for local use.

Start PostgreSQL in the background:

```shell
make db-up
```

The service uses `postgres:17.2-alpine3.21`, exposes its port only on
`127.0.0.1`, and stores data in the named `contour-postgres-data` Docker volume.

## Verify and connect

Wait for the database readiness probe to succeed:

```shell
make db-ready
```

Open a `psql` session inside the container:

```shell
make db-psql
```

## Database migrations

Export the configured variables to the shell, then apply the tracked migration
head and confirm the recorded revision:

```shell
set -a
. ./.env
set +a
make migrate
make migration-current
make migration-check
```

`make migrate` is safe to re-run: it only applies revisions not already
recorded in the database. The current Phase 0 schema creates `tenants`,
tenant-owned `workspaces` and `sources`, immutable `source_versions`, exact
`evidence`, evidence-backed entities and relationships, and durable jobs with
distinct run attempts. Composite foreign keys prevent evidence, relationship,
and run links from crossing the persisted Tenant/Workspace ownership tuple. It
does not yet implement membership enforcement, acquisition, extraction, or
indexing.

`make migration-check` compares the SQLAlchemy Core metadata registry with the
connected database and fails when a schema change has no matching migration.
Metadata is comparison and query input only: Contour application startup never
calls `create_all()`, `drop_all()`, or Alembic. Schema changes are explicit
operator/release actions.

### Author a schema change

First update the capability-owned Core table metadata under
`infrastructure/postgres/tables/`, then generate a candidate revision against a
database already migrated to the current head:

```shell
uv run alembic revision --autogenerate -m "describe the schema change"
```

Review the generated file before committing it. Verify identifiers, types,
nullability, indexes, constraints, server defaults, lock impact, and recovery;
write renames, backfills, and other data migrations explicitly because
autogeneration cannot infer their intent. Then run:

```shell
make test-integration
make migration-check
```

The dedicated CI PostgreSQL job repeats the isolated migration and drift checks.
Future production deployment automation must run `alembic upgrade head` as a
separate release step before starting code that requires the new schema; it must
not move that responsibility into API or worker startup.

If a migration fails, retain the error output and inspect the current revision
with `make migration-current`. Do not use a destructive reset as ordinary
recovery. For a disposable local development database only, use the explicit
reset below, then run `make db-up`, `make db-ready`, and `make migrate` to
restore a clean state. Production migration orchestration and automatic
downgrade are not implemented.

The tenant-ownership revision assigns every row from the prior schema to the
single explicit `LEGACY:default` tenant inside its transaction. This preserves
existing Workspace, Source, Version, Evidence, Entity, Relationship, Job, and
Run rows without guessing a more specific owner. If that revision fails, fix
the reported database condition and retry `make migrate`; PostgreSQL rolls back
the revision's DDL and backfill together. Do not downgrade it, because removing
the ownership columns weakens the durable security boundary.

The clean-database migration integration test is deliberately opt-in because it
creates and drops an isolated database on the configured local PostgreSQL
server:

```shell
make test-integration
```

## Stop and restart

Stop the container while preserving the named volume:

```shell
make db-stop
```

Starting it again with `make db-up` reuses the same local data volume.

## Clean reset (destructive)

The following command permanently deletes this Compose project's local database
volume. Do not run it when data must be retained:

```shell
docker compose down --volumes --remove-orphans
```

After a reset, run `make db-up` and `make db-ready` to create a fresh database.
