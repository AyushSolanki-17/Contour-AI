# Contour Active Work

**Status:** active execution queue
**Updated:** 2026-08-19
**Queue limit:** at most six tasks not marked `done`

This file is the small, reviewable working set for humans and coding agents. It
turns the ordered [backend roadmap](docs/development/roadmap.md) into bounded
implementation cards without making this file a second product backlog.

The current cards were promoted from the current Phase 0 planning material on
2026-08-19. They contain all context needed to execute these tasks. The parent
planning directory remains private intake material and does not need to be
re-read for work listed here. Frontend tasks from the cross-repository plan were
intentionally excluded because this repository owns backend work only.

## Sources of truth

Use this precedence when instructions disagree:

1. an explicit current user instruction;
2. [AGENTS.md](AGENTS.md) and the controlling engineering documents;
3. the ordered [backend roadmap](docs/development/roadmap.md); and
4. this queue, which controls only the currently approved execution slice.

Do not copy private research, strategy, or raw planning notes into a task card.
A card may narrow a roadmap item, but it may not silently expand or reorder it.

## Operating rules

1. A human or coordinating agent keeps no more than six cards not marked `done`
   here and promotes work only from the earliest incomplete roadmap step unless
   the user explicitly changes priority.
2. Before editing implementation files, an agent claims one `ready` card by
   setting its status to `in_progress`, its owner to a stable human or agent
   name, and its `Updated` date. The queue row and card fields must agree. An
   agent owns at most one active card.
3. `queued` means that a card is shaped but its dependencies are not complete.
   `blocked` is reserved for an attempted task that cannot progress. Record the
   concrete blocker and evidence instead of repeatedly retrying it.
4. Work stops at the card's scope and acceptance criteria. Record useful new
   ideas under `Follow-ups`; do not implement them, create more cards, or start
   the next task without an explicit coordinator or user decision.
5. When the acceptance checks pass, fill in every handoff field, set the card to
   `review`, and stop. A human or explicitly assigned reviewer either marks it
   `done` or returns it to `ready` with a specific unmet criterion. Reviews do
   not begin open-ended improvement cycles.
6. On approval, the reviewer adds a concise entry to
   [the completed-task log](docs/development/task-history.md). Completed cards
   may then be removed when the queue is refilled.
7. Update documentation in the same task when behavior or a contract changes.
   Update [README.md](README.md) when setup, usage, or public entry points
   change, and add notable behavior to [CHANGELOG.md](CHANGELOG.md) under
   `Unreleased`. The changelog is not a commit log or a substitute for the task
   history.

## Status vocabulary

| Status | Meaning | Who moves it next |
|---|---|---|
| `queued` | Defined, but waiting on listed dependencies | Coordinator after dependencies complete |
| `ready` | May be claimed now | Implementer |
| `in_progress` | Claimed by exactly one owner | Implementer |
| `review` | Acceptance evidence and handoff are ready | Reviewer |
| `blocked` | Attempted and stopped by a recorded condition | Coordinator or user |
| `done` | Independently accepted | Coordinator during archival/refill |

## Queue

| Order | Task | Status | Depends on | Owner |
|---:|---|---|---|---|
| 1 | `P0-01` — Python project and local quality foundation | `done` | — | /root |
| 2 | `P0-02` — Local PostgreSQL development runtime | `done` | — | /root |
| 3 | `P0-03` — Continuous-integration quality gate | `review` | `P0-01` | /root |
| 4 | `P0-04` — Settings, errors, logging, and health contracts | `review` | `P0-01`, `P0-02` | /root |
| 5 | `P0-05` — Migration baseline and clean-database test | `review` | `P0-01`, `P0-02` | /root |

`P0-01` and `P0-02` have disjoint intended scopes and may be assigned in
parallel. Before later tasks are assigned concurrently, the coordinator should
check their expected files and record any ownership split in the affected
cards.

---

## P0-01 — Python project and local quality foundation

- **Status:** `done`
- **Owner:** /root
- **Reviewer:** user
- **Updated:** 2026-08-19
- **Roadmap:** Phase 0.1 — repository and runtime foundation
- **Outcome:** A clean checkout has one installable Python project and one
  documented local command surface for formatting, linting, typing, and tests.
- **Scope:** Python version declaration; `src` package skeleton; project and
  development dependencies; reproducible dependency lock; minimal deterministic
  test; local quality commands.
- **Non-goals:** API behavior, domain models, PostgreSQL, migrations, provider
  SDKs, deployment, and speculative package abstractions.
- **Dependencies:** none.

### Acceptance checklist

- [x] The supported Python version and dependency workflow are explicit.
- [x] A clean environment can install from the committed project definition and
      lock without resolving unpinned transitive versions.
- [x] The package imports from the `src` layout without path manipulation.
- [x] One documented command surface runs formatting checks, linting, static
      typing, and deterministic tests.
- [x] The initial tests prove the package and toolchain work without network or
      service dependencies.
- [x] `README.md` contains only setup and verification commands that were run
      successfully.
- [x] `CHANGELOG.md` records the new developer-facing foundation.

### Handoff

- **Summary:** Added the installable Python 3.14 `contour` package, committed
  dependency lock, deterministic quality command surface, and pre-commit
  checks for formatting, linting, unsafe files, and common repository mistakes.
- **Files changed:** `pyproject.toml`, `uv.lock`, `Makefile`,
  `src/contour/__init__.py`, `tests/test_package.py`, `.gitignore`, `README.md`,
  `CHANGELOG.md`, `AGENTS.md`, `.pre-commit-config.yaml`, and this queue.
- **Verification and results:** `uv sync --locked --group dev && make quality`
  passed (Ruff format and lint, strict mypy, and 1 pytest); `make precommit`,
  `uv lock --check`, and `git diff --check` passed. `make hooks` installed the
  pre-commit hook.
- **Decisions/assumptions:** Python 3.14 is the sole supported runtime because
  the supplied environment is 3.14.4. `uv` is the dependency workflow, and the
  full lock (including hashes) is committed.
- **Risks or blockers:** none recorded
- **Follow-ups (not started):** none.

---

## P0-02 — Local PostgreSQL development runtime

- **Status:** `done`
- **Owner:** /root
- **Reviewer:** user
- **Updated:** 2026-08-19
- **Roadmap:** Phase 0.1 — repository and runtime foundation
- **Outcome:** A developer can start and stop the declared PostgreSQL version
  locally with repeatable, non-secret configuration and a meaningful readiness
  check.
- **Scope:** Local container/service definition; pinned PostgreSQL version;
  development-only credentials through ignored or example configuration;
  durable local volume; health/readiness probe; operating documentation.
- **Non-goals:** Application repositories, schema design, migrations, production
  deployment, high availability, backups, or hosted credentials.
- **Dependencies:** none. Coordinate public environment-variable names with
  `P0-04`; do not implement Python settings in this card.

### Acceptance checklist

- [x] The PostgreSQL image or package version is pinned explicitly.
- [x] Tracked files contain no real credentials, and the local credential flow
      is documented.
- [x] Start, readiness, connection, stop, and clean-reset commands are
      documented and were exercised.
- [x] Normal stop/start preserves local data; clean reset is an explicit,
      separately documented destructive action.
- [x] Configuration is narrow enough for local development and does not imply a
      production deployment contract.
- [x] `README.md` links to the working local database instructions.
- [x] `CHANGELOG.md` records the new developer-facing runtime.

### Handoff

- **Summary:** Added a pinned, loopback-only local PostgreSQL Compose service
  with an ignored development configuration, readiness probe, persistent named
  volume, and explicit destructive reset procedure.
- **Files changed:** `compose.yaml`, `.env.example`, `Makefile`,
  `docs/development/local-postgresql.md`, `README.md`, `CHANGELOG.md`, and this
  queue.
- **Verification and results:** `docker compose config --quiet`, `make quality`,
  `make precommit`, and `git diff --check` passed. The Docker lifecycle was
  exercised: `make db-up`, `make db-ready`, in-container `psql` connection,
  `make db-stop`, a restart that retained one inserted row, `docker compose down
  --volumes --remove-orphans`, then a fresh start confirming the test table was
  absent.
- **Decisions/assumptions:** The explicitly pinned `postgres:17.2-alpine3.21`
  image is sufficient for this local-only runtime. `.env` is ignored and starts
  from a tracked non-secret template; the service binds only to `127.0.0.1`.
- **Risks or blockers:** none recorded
- **Follow-ups (not started):** Application connection settings belong to
  `P0-04`; schema and migration work remain outside this card.

---

## P0-03 — Continuous-integration quality gate

- **Status:** `review`
- **Owner:** /root
- **Reviewer:** unassigned
- **Updated:** 2026-08-19
- **Roadmap:** Phase 0.1 — repository and runtime foundation
- **Outcome:** Pull requests run the same deterministic quality checks
  documented for local development before they can merge.
- **Scope:** CI workflow; locked environment installation; format, lint, type,
  and unit-test gates; documentation-link validation; basic secret scanning;
  dependency caching only when it does not weaken lock enforcement.
- **Non-goals:** deployment, release automation, live-service tests, provider
  calls, broad platform matrices, and checks for capabilities not implemented
  yet.
- **Dependencies:** `P0-01` accepted.

### Acceptance checklist

- [x] CI triggers for pull requests.
- [x] CI installs the declared locked environment and invokes the same commands
      developers use locally.
- [x] Formatting, linting, typing, deterministic tests, documentation links,
      and secret scanning fail the workflow when they fail locally.
- [x] Jobs have bounded timeouts and least-privilege permissions.
- [x] No live network source, model, database, or secret is required after
      dependency installation.
- [x] The workflow syntax is validated and the available checks pass.
- [x] Contributor-facing commands in `README.md` remain accurate.

### Handoff

- **Summary:** Added a least-privilege GitHub Actions quality workflow and
  deterministic local documentation-link and basic secret checks it invokes.
- **Files changed:** `.github/workflows/ci.yml`, `scripts/check_docs_links.py`,
  `tests/test_quality_scripts.py`, `Makefile`, `README.md`, `CHANGELOG.md`,
  `docs/development/task-history.md`, and this queue.
- **Verification and results:** `make quality` passed (Ruff format and lint,
  strict mypy, and 2 pytest tests); `make docs`, `make precommit`, and `git
  diff --check` passed. Staged pre-commit checks validate the workflow YAML.
  `actionlint` is not installed locally; Gitleaks runs when CI is triggered.
- **Decisions/assumptions:** CI runs only for pull requests to avoid duplicate
  branch-push runs. The default branch must require the `quality` and
  `secret-scan` checks before merging; direct pushes are outside this workflow's
  protection model. The workflow uses only `contents: read` and
  `pull-requests: read`, a ten-minute timeout, a locked `uv` environment, and
  no service or provider calls after dependency installation. Gitleaks uses an
  immutable v3 action pin and scans repository history in a separate CI job;
  its PR commit lookup requires the narrow pull-request read permission.
- **Risks or blockers:** none recorded
- **Follow-ups (not started):** Configure default-branch protection to require
  the `quality` and `secret-scan` checks; do not add deployment or live-service
  jobs in this card.

---

## P0-04 — Settings, errors, logging, and health contracts

- **Status:** `review`
- **Owner:** /root
- **Reviewer:** unassigned
- **Updated:** 2026-08-19
- **Roadmap:** Phase 0.1 — repository and runtime foundation
- **Outcome:** The backend starts with validated configuration, exposes distinct
  liveness and readiness behavior, and reports structured, redacted failures.
- **Scope:** Typed settings boundary; environment parsing; structured application
  errors; logging configuration and secret redaction; minimal FastAPI entry
  point; liveness and database-aware readiness contracts; focused tests.
- **Non-goals:** business routes, authentication, domain models, repository
  implementation, tracing backend, or production observability stack.
- **Dependencies:** `P0-01` and `P0-02` accepted.

### Acceptance checklist

- [x] Missing or invalid required configuration fails clearly without fabricated
      defaults.
- [x] Secrets are accepted by reference/environment and are absent from error,
      representation, and log output tests.
- [x] Application errors have a stable internal shape independent of FastAPI;
      HTTP translation remains in the API layer.
- [x] Liveness proves the process can respond; readiness fails when required
      dependencies are unavailable and does not report an empty success.
- [x] Package dependency direction follows the backend architecture.
- [x] Tests cover valid configuration, invalid configuration, redaction,
      liveness, readiness success, and readiness failure.
- [x] Startup and health usage are documented and recorded in `CHANGELOG.md`.

### Handoff

- **Summary:** Added validated PostgreSQL environment settings, secret-safe
  logging, stable framework-independent application errors, and a minimal
  FastAPI liveness/readiness contract.
- **Files changed:** `pyproject.toml`, `uv.lock`, `.env.example`,
  `src/contour/config.py`, `src/contour/logging.py`,
  `src/contour/application/`, `src/contour/adapters/`, `src/contour/api/`,
  `tests/test_config.py`, `tests/test_logging.py`, `tests/test_health_api.py`,
  `README.md`, `docs/development/local-postgresql.md`, `CHANGELOG.md`, and
  this queue.
- **Verification and results:** `uv run ruff format --check .`, `uv run ruff
  check .`, `uv run mypy`, and `uv run pytest` passed (12 tests). The suite
  emits one upstream Starlette `TestClient` deprecation warning only.
- **Decisions/assumptions:** The existing Compose variables are the public
  application database contract, with loopback host as the local-only default.
  Readiness opens a new PostgreSQL connection with a three-second connection
  timeout and runs `SELECT 1`; liveness deliberately does neither. API errors
  expose a stable code and safe message rather than adapter failures.
- **Risks or blockers:** none recorded
- **Follow-ups (not started):** Configure server log shipping and richer
  telemetry only when later Phase 0 work needs them.

---

## P0-05 — Migration baseline and clean-database test

- **Status:** `review`
- **Owner:** /root
- **Reviewer:** unassigned
- **Updated:** 2026-08-19
- **Roadmap:** Phase 0.1 — repository and runtime foundation
- **Outcome:** An empty supported PostgreSQL instance can reach the current
  schema revision repeatably, and the migration path has an automated test.
- **Scope:** Migration tool configuration; baseline revision containing only
  infrastructure needed by the migration system; upgrade/current checks;
  repeatability and clean-database integration test; recovery documentation.
- **Non-goals:** Phase 0.2 domain tables, speculative schemas, production
  migration orchestration, or destructive automatic downgrade.
- **Dependencies:** `P0-01` and `P0-02` accepted.

### Acceptance checklist

- [x] Migration configuration uses the public database configuration contract
      without committing credentials.
- [x] Applying all migrations to an empty supported PostgreSQL database succeeds
      and reports the expected current revision.
- [x] Re-running the upgrade is safe and leaves the database at the same
      revision.
- [x] A deterministic integration test creates an isolated empty database,
      migrates it, verifies revision state, and cleans up on success or failure.
- [x] Failure and recovery instructions are documented; destructive reset is
      never implicit in ordinary startup.
- [x] Default unit tests remain service-free, while the integration test is
      clearly selectable.
- [x] Migration commands and the developer-facing capability are reflected in
      `README.md` and `CHANGELOG.md`.

### Handoff

- **Summary:** Added an Alembic baseline revision and commands for repeatable
  local upgrades/current-revision inspection. Added an opt-in PostgreSQL
  integration test that creates, migrates, checks, and drops an isolated
  database.
- **Files changed:** `pyproject.toml`, `uv.lock`, `alembic.ini`, `migrations/`,
  `tests/conftest.py`, `tests/test_migrations_integration.py`, `Makefile`,
  `README.md`, `docs/development/local-postgresql.md`, `CHANGELOG.md`, and this
  queue.
- **Verification and results:** `make quality` passed (12 tests passed, 1
  intentionally skipped); `make docs`, `uv lock --check`, and `git diff --check`
  passed. With the local Compose PostgreSQL runtime, `make migrate`,
  `make migration-current`, a repeated `make migrate`, and `make
  test-integration` passed (13 tests), reporting revision `20260819_01`.
- **Decisions/assumptions:** The initial revision intentionally has no domain
  tables and records only migration state. Alembic reads the existing validated
  PostgreSQL environment contract through `Settings`; the integration test is
  opt-in and requires a local PostgreSQL user allowed to create/drop its
  isolated test database.
- **Risks or blockers:** none recorded
- **Follow-ups (not started):** First application/domain tables remain Phase
  0.2 work; production migration orchestration and downgrade policy remain out
  of scope.

## Queue refill checklist

The reviewer or coordinator runs this only after accepting or explicitly
reordering work:

- [ ] Record each accepted card in
      [the completed-task log](docs/development/task-history.md).
- [ ] Re-evaluate dependencies and move newly unblocked cards to `ready`.
- [ ] Remove archived `done` cards while preserving at most six cards not marked
      `done`.
- [ ] Promote only the next smallest backend slice from the controlling roadmap.
- [ ] Give every promoted card an outcome, non-goals, dependencies, objective
      acceptance checks, and a blank handoff.
- [ ] Check planned versus implemented wording in documentation.
- [ ] Confirm `README.md` and `CHANGELOG.md` match the accepted behavior.
- [ ] Assign agents only after checking likely file overlap.
