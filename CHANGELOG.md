# Changelog

Notable changes to Contour are recorded here. Entries describe user-visible,
operator-visible, or developer-facing behavior; task bookkeeping and ordinary
refactors belong in the task history and Git history instead.

The format follows Keep a Changelog conventions. Until the first release, new
entries remain under `Unreleased`. A release moves them under a version and ISO
date without rewriting what was actually delivered.

## Unreleased

### Added

- Durable PostgreSQL catalog persistence for workspaces, sources, immutable
  source versions, and exact evidence locators, including atomic admission and
  isolated clean-database integration coverage.
- Conventional `services`, `repositories`, and `infrastructure` packages with
  strict dependency rules, capability-specific ports, SQLAlchemy Core PostgreSQL
  implementations, explicit composition, pooled resources, safe persistence
  errors, and executable architecture safeguards.
- Framework-independent, immutable Phase 0 source/version/evidence identity
  primitives with exact locators and explicit unknown temporal values.
- A bounded repository-native task queue with explicit ownership, acceptance,
  review, archival, and human/agent handoff rules.
- Installable Python 3.14 backend package foundation with a locked development
  environment and deterministic format, lint, type, and test commands.
- Local pinned PostgreSQL Compose runtime with a loopback-only listener,
  persistent development volume, readiness probe, and documented reset flow.
- GitHub Actions quality gate for locked Python checks, documentation links, and
  repository-history secret scanning with Gitleaks.
- Gitleaks pre-commit scanning for staged secrets before they enter Git history.
- Validated PostgreSQL runtime settings, redacted application logging, and a
  minimal FastAPI health contract with separate liveness and database-aware
  readiness endpoints.
- Alembic migration baseline, repeatable local migration commands, and an
  explicitly selected clean-database PostgreSQL integration test.
- Alembic-only durable schema evolution with metadata-drift checks, an
  application-startup guard, and isolated PostgreSQL migration verification in
  continuous integration.
- Explicit backend composition-root, router/controller, Pydantic API-schema,
  application-service, adapter, package-namespace, and proportional-testing
  boundaries, with enforced Google-style production docstrings.
- Generated frontend-consumable OpenAPI artifact with deterministic drift
  verification in the backend quality floor.
