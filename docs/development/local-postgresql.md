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
