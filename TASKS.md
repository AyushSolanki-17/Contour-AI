# Contour Active Work

**Status:** one active card; two ordered follow-ups
**Updated:** 2026-08-25

This is the bounded execution queue for work promoted from the ordered
[backend roadmap](docs/development/roadmap.md). Claim exactly one `ready` card
before implementation; a reviewer accepts it, records the result in the
[completed-task log](docs/development/task-history.md), and then archives it.

## Active queue

### P0-11 — Persist acquired PEP content and immutable versions

Owner role: backend
Assignee: Codex
Priority: P1
Status: review
Depends on: `P0-10` (accepted)
Product: `PROD-P0-01`

#### Goal

Turn an accepted PEP acquisition into a durable content-addressed artifact and
immutable source-version record without yet claiming normalization or worker
execution.

#### Requirements

- Persist the exact admitted bytes through a content-addressed artifact
  boundary and store the matching source-version manifest through the accepted
  catalog boundary.
- Retain the content digest, source identity, observation time, and available
  upstream revision metadata without fabricating unknown values.
- Make repeated persistence of the same admitted content idempotent, and reject
  conflicting content or metadata that would rewrite an accepted version.
- Define safe recovery for artifact-write or database failure so no accepted
  manifest points to missing or integrity-invalid content.
- Keep default tests offline and deterministic; exercise the relevant
  PostgreSQL and artifact round trips at their real boundaries.
- Do not add normalization, extraction, indexing, workers, or public product
  routes in this card.

#### Acceptance criteria

- [x] The pinned acquisition produces an integrity-verifiable artifact and one
      immutable source-version record with the same digest.
- [x] Repeating the same acquisition returns the accepted version without
      duplicate durable state or destructive overwrite.
- [x] Conflicting content, missing artifacts, checksum mismatch, and partial
      failure remain explicit and recoverable.
- [x] Focused unit and integration checks, `make quality`,
      `make openapi-check`, and `make docs` pass.

#### Verification evidence

- Focused offline unit and architecture checks: 19 passed.
- Real artifact/PostgreSQL integration and migration checks: 5 passed against
  isolated migrated databases; the local schema is at `20260825_05 (head)` and
  `alembic check` reports no upgrade operations.
- `make quality`: 34 passed, 5 explicitly skipped integration tests; formatting,
  linting, strict typing, default tests, and OpenAPI drift all passed.
- `make openapi-check`, `make docs`, and `make precommit` passed.

## Scheduled follow-ups

Keep `P0-11A` and `P0-12` planned until their dependencies are accepted.

### P0-11A — Remove reference-source coupling from application services

Owner role: backend
Assignee: Codex
Priority: P1
Status: review
Depends on: `P0-11` acceptance
Product: `PROD-P0-01`

#### Goal

Keep the PEP implementation as a replaceable reference adapter while making
source acquisition and immutable persistence generic product capabilities.

#### Requirements

- Remove PEP-specific types and policy from reusable application service
  boundaries, especially the durable persistence service.
- Define a source-neutral acquired-content contract carrying only source
  identity, exact bytes, content digest, observation time, and optional
  upstream metadata.
- Keep PEP number, canonical URL, HTML validation, and pinned fixture behavior
  inside the reference-source adapter or fixture boundary.
- Preserve artifact, immutable-version, idempotency, conflict, integrity, and
  recovery behavior.
- Update implementation-coupled documentation and tests to describe PEP as a
  reference source, not a product-level domain requirement.

#### Non-goals

- Do not implement normalization, extraction, indexing, workers, network
  acquisition, or public ingestion routes.
- Do not add a generic plugin framework, DI framework, or speculative provider
  registry.

#### Acceptance criteria

- [x] Generic application services and persistence results contain no PEP-
      specific types or validation rules.
- [x] The PEP fixture adapter still satisfies the generic acquisition boundary
      and existing PEP failure classifications remain covered.
- [x] Artifact/PostgreSQL invariants remain green, including idempotent retry
      and immutable conflict rejection.
- [x] Architecture checks prove source-specific code is outside generic domain
      and application policy.
- [x] Focused tests, `make quality`, `make openapi-check`, and `make docs` pass.

#### Verification evidence

- Focused source, artifact, and architecture checks: 15 passed.
- Real artifact/PostgreSQL integration and migration checks: 5 passed.
- Generic service boundary is covered by `test_application_services_remain_source_neutral`.

### P0-12 — Normalize PEP content without losing evidence locators

Owner role: backend
Assignee: unassigned
Priority: P1
Status: planned
Depends on: `P0-11A`
Product: `PROD-P0-01`

#### Goal

Produce a deterministic normalized reference-source artifact that later
extraction can use while retaining a verifiable path back to the exact
admitted source bytes.

#### Requirements

- Normalize the pinned supported PEP content deterministically and retain the
  source-version identity, transformation identity, and locator mapping needed
  to resolve normalized fields or spans to exact source evidence.
- Store normalized output as a rebuildable content-addressed artifact with its
  own integrity digest and explicit derivation from the raw version.
- Preserve structured-header and byte-span meaning where available, and keep
  absent or unknown source values explicit.
- Classify malformed input, unsupported structure, locator loss, and integrity
  mismatch without accepting partial normalized state.
- Keep default tests offline and deterministic.
- Do not add entity or relationship extraction, search indexing, workers, or
  public product routes in this card.

#### Acceptance criteria

- [ ] Repeated normalization of the same admitted bytes produces the same
      normalized digest and transformation metadata.
- [ ] Representative normalized headers and content resolve to exact locators
      in the immutable source version.
- [ ] Malformed input, locator loss, and corrupt derived artifacts fail rather
      than becoming accepted evidence.
- [ ] Focused invariant and integration checks, `make quality`,
      `make openapi-check`, and `make docs` pass.

## Promotion and handoff rule

For every scheduled follow-up, the coordinator first confirms the dependency is
accepted, then changes only that card to `ready`. An implementer claims exactly
that card, moves it to `review` with verification evidence, and leaves
acceptance and archival to a separate reviewer. The immediate backend order is
`P0-11`, then `P0-11A`, then `P0-12`; no later card is assigned while its
dependency remains unaccepted.

## Recently completed

| Task | Status | Context |
|---|---|---|
| `P0-01` | `done` | Python project and local quality foundation accepted. |
| `P0-02` | `done` | Local PostgreSQL development runtime accepted. |
| `P0-03` | `done` | Continuous-integration quality gate accepted. |
| `P0-04` | `done` | Settings, errors, logging, and health contracts accepted. |
| `P0-05` | `done` | Migration baseline and clean-database test accepted. |
| `P0-06` | `done` | Source, immutable-version, evidence, and unknown-time domain primitives accepted. |
| `P0-07` | `done` | Workspace, knowledge, job/run, and persistence-port domain foundation accepted. |
| `P0-08` | `done` | Durable source catalog and evidence persistence accepted after the half-null span regression was corrected. |
| `P0-09` | `done` | Evidence-backed knowledge records and durable job/run attempts accepted. |
| `P0-10` | `done` | Deterministic PEP preflight, pinned acquisition, stable identity, and safe failure classification accepted. |

Detailed acceptance evidence is retained in the
[completed-task log](docs/development/task-history.md) and Git history.
