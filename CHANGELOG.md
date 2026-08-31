# Changelog

Notable changes to Contour are recorded here. Entries describe user-visible,
operator-visible, or developer-facing behavior; task bookkeeping and ordinary
refactors belong in the task history and Git history instead.

The format follows Keep a Changelog conventions. Until the first release, new
entries remain under `Unreleased`. A release moves them under a version and ISO
date without rewriting what was actually delivered.

## Unreleased

### Fixed

- Removed unpublished trusted-local workspace and source routes so the public
  contract remains health-only until authenticated tenant scoping is available.
- PostgreSQL now rejects exact-evidence spans that specify only one offset,
  matching the domain's both-or-neither locator invariant.

### Added

- Authenticated, tenant-scoped Tenant, Workspace, and Source collection routes
  with opaque configured local credentials, non-enumerating nested access,
  durable idempotency replay, and signed scope-bound pagination cursors.
- Provider-neutral Principal and uniform Membership persistence with verified,
  correlation-safe Access Contexts for tenant-scoped catalog, knowledge,
  execution, and immutable-source operations. Foreign and unknown Tenant
  selectors share the same non-enumerating application outcome.
- Durable Tenant ownership for Workspaces, Sources, immutable Versions,
  Evidence, Entities, Relationships, Jobs, and Runs. PostgreSQL composite
  foreign keys now reject cross-owner evidence, relationship, and run links;
  populated legacy schemas migrate atomically into the explicit
  `LEGACY:default` Tenant.
- Source-neutral acquired-content and persistence contracts keep PEP-specific
  validation in the reference source adapter while preserving generic artifact
  and immutable-version recovery behavior.
- Artifact-first persistence of exact admitted PEP bytes with atomic
  SHA-256-addressed filesystem storage, immutable PostgreSQL manifests,
  observation and optional upstream revision metadata, idempotent retries, and
  explicit repair of missing or corrupt artifacts.
- Offline deterministic PEP preflight and pinned-fixture acquisition with
  stable digests, revision metadata, and safe failure classification.
- Durable PostgreSQL entities, evidence-backed relationships, jobs, and
  independent run attempts, with lifecycle constraints, exact evidence
  attachments, atomic persistence, and isolated integration coverage.
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
