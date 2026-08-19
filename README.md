# Contour

## Engineering definition

Contour is an open-source, evidence-backed knowledge and investigation platform for complex, evolving domains. It maintains persistent entities, claims, relationships, history, provenance, lineage, permissions, conflicts, and uncertainty so humans and AI applications can ask what is known, investigate why, analyze consequences, and support decisions. Its capabilities are evaluated for correctness, evidence attribution, temporal validity, uncertainty, latency, and cost so every technology must earn its place.

## In simple language

Contour helps people and AI assistants understand complicated information without losing its history or sources. You can ask what is currently known, why something is believed, how pieces are connected, what changed, or what might be affected by a decision. Contour shows the supporting and conflicting evidence and clearly marks what remains unknown. A person remains responsible for important decisions and can save an auditable investigation record. The system is built in public, with honest tests showing when simple rules, search, graphs, or AI work best.

## Repository scope

This is the primary Contour engineering repository. It contains the Python backend and core packages, database schemas and migrations, tests and evaluations, command-line tools, deployment configuration, and technical documentation tied to implemented behavior.

User-interface applications and other independently deployable components live in their own repositories. Private research, product and business strategy, competitive analysis, and future planning are intentionally kept outside this repository.

Contour is in early development. The project scope, backend architecture, knowledge model, development roadmap, and testing standard live in the [engineering documentation](docs/README.md). API reference and operational guidance will be added alongside the code they describe.

## Development status

Phase 0 is active. The Python package and its local quality tooling are
implemented; the source-to-evidence backend is not yet implemented.
See the bounded [active task queue](TASKS.md) to review or assign the next work,
and the [changelog](CHANGELOG.md) for notable delivered behavior.

## Local development

Contour currently supports Python 3.14. Create or use a Python 3.14 virtual
environment, then install the exact locked environment:

```shell
uv sync --locked --group dev
```

Run the full deterministic Python quality suite:

```shell
make quality
```

The individual checks are `make format`, `make lint`, `make typecheck`, and
`make test`. These commands do not require a running service, database, network
source, or model after the locked environment is installed.

Run the repository-wide checks used by CI with:

```shell
make docs
```

Gitleaks scans staged changes during pre-commit, while CI scans repository
history as a second line of defense.

Install the repository's commit-time checks once per clone:

```shell
make hooks
```

Run those checks manually with `make precommit`. They reject accidental private
keys, merge-conflict markers, invalid TOML, oversized added files, whitespace
errors, and Python lint/format drift.

## Local PostgreSQL

The Phase 0 local development database is a pinned, loopback-only PostgreSQL
Compose service. See [local PostgreSQL instructions](docs/development/local-postgresql.md)
for the verified configuration, start, readiness, connection, stop, and explicit
destructive-reset commands.

## Database migrations

After exporting the configured PostgreSQL variables and starting the local
database, apply the current schema revision with:

```shell
make migrate
make migration-current
```

The default test suite never opens a database connection. Run the separately
selected clean-database migration test against the disposable local development
database with:

```shell
make test-integration
```

See the [migration recovery guidance](docs/development/local-postgresql.md#database-migrations)
before recovering a failed local migration.

## Start the backend and check health

The backend requires the PostgreSQL variables in `.env`; no database password,
name, user, or port is invented at startup. After configuring and starting the
local database, start the loopback-only API server. The target loads the
development-only `.env` variables for this command:

```shell
make run
```

In a separate terminal, liveness confirms only that the process can respond;
readiness also proves PostgreSQL accepts a connection and query:

```shell
curl --fail http://127.0.0.1:8000/health/live
curl --fail http://127.0.0.1:8000/health/ready
```

When PostgreSQL is unavailable, `/health/ready` returns HTTP 503 with the
stable `dependency.unavailable` error code. It does not expose connection or
credential details.
