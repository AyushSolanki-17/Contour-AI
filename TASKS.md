# Contour Active Work

**Status:** one workspace/source contract card in review; one planned follow-up
**Updated:** 2026-08-27

This is the bounded execution queue for work promoted from the ordered
[backend roadmap](docs/development/roadmap.md). Claim exactly one `ready` card
before implementation; a reviewer accepts it, records the result in the
[completed-task log](docs/development/task-history.md), and then archives it.

## Active queue

### P0-13 — Establish the source-neutral workspace and source product boundary

Owner role: backend
Assignee: backend-api-agent
Reviewer: unassigned
Priority: P1
Status: review
Depends on: `P0-11` and `P0-11A` (accepted); owner contract checkpoint approved 2026-08-26
Product: `PROD-P0-01`

#### Goal

Give the browser its first real product capability through source-neutral
workspace and source application services plus a generated, versioned HTTP
contract, without extending reference-source-specific behavior.

#### Frozen observable contract

- Publish `PUT` and `GET /api/v1/workspaces/{workspace_id}` plus `PUT` and
  `GET /api/v1/workspaces/{workspace_id}/sources/{source_id}`. Identifiers are
  caller-stable opaque path values and responses return their canonical form.
- Workspace creation accepts a name. The initial trusted-local profile assigns
  the local operator; it does not publish authentication, authorization, or
  permission behavior in this card.
- Source registration accepts source type, canonical locator, scope, optional
  license, and data classification through a source-neutral schema. A supported
  reference adapter may be named as a capability value, but its number, URL,
  format, or parsing rules must not enter reusable services or public schemas.
- Repeating a `PUT` with the same identity and representation returns the same
  accepted resource without duplicate state. Reusing the identity with a
  different representation returns conflict without mutation.
- Source registration requires an existing workspace, and source inspection
  must not expose a source through a different workspace path.
- Use the common error envelope with stable invalid-request, not-found,
  conflict, unsupported-source, and dependency-unavailable codes and HTTP
  statuses. Validation details must be useful without leaking internals.
- Listing, pagination, ingestion, progress, normalization, extraction, search,
  authentication, and authorization are explicitly unpublished in this card.

#### Requirements

- Add source-neutral workspace/source application services over the accepted
  transaction and repository boundaries; routes translate and validate only.
- Generate `openapi/contour.openapi.json`; never edit the artifact by hand.
- Keep failure and retry behavior atomic, deterministic, and safe under repeat
  requests.
- Update only implementation-coupled public documentation and contract examples.

#### Verification budget

- Reuse the accepted catalog persistence coverage, source-neutral architecture
  guard, common error handling, OpenAPI drift check, and documentation checks.
- Add at most one API-contract test module and five permanent behavioral cases:
  success/open/replay, conflict and workspace scoping, invalid/unsupported
  input, dependency failure, and generated-contract shape.
- Extend an existing PostgreSQL catalog case only if the service behavior cannot
  be proven through existing persistence evidence; do not duplicate API behavior
  at the database layer.
- Add no dependency, runner, service, browser test, live network, or source-
  specific fixture. Report all test-file/case/runtime changes at handoff.

#### Acceptance criteria

- [x] A client can create/open a workspace and register/inspect its source using
      only the generated contract and stable errors.
- [x] Repeat requests are idempotent; identity conflicts and cross-workspace
      source access fail without partial durable state or information leakage.
- [x] Source-specific policy remains outside domain, reusable services, and
      public transport schemas.
- [x] The generated OpenAPI artifact passes drift checks and is ready for an
      intentional frontend snapshot update.
- [x] Focused service/API/persistence checks, `make quality`,
      `make openapi-check`, and `make docs` pass.

#### Verification evidence

- Focused workspace/source API, health/error, OpenAPI, architecture, and safe
  PostgreSQL failure checks: 16 passed.
- `make quality`: formatting, linting, strict typing, OpenAPI drift, and the
  default suite passed; 40 tests passed and 5 PostgreSQL integration tests were
  explicitly skipped in 0.33 seconds.
- `make openapi-check`, `make docs`, and `make precommit` passed. The generated
  contract SHA-256 is
  `c32bd92a6dbd8c9bb2bcdbc24c0fc1b10ec8534cd062159a1ba160038f5d483f`.
- Test delta: one API-contract module and five permanent behavioral cases added;
  the existing OpenAPI drift case was updated for composition only. No tests
  were consolidated or removed, and no dependency, service, fixture, runner, or
  default-suite category changed.
- The accepted catalog transaction/repository coverage was reused without
  adding overlapping PostgreSQL cases. Real PostgreSQL integration was not
  rerun because the local Docker daemon was unavailable; no migration,
  repository, table, or query changed in this card.

## Accepted predecessor evidence

### P0-11 — Persist acquired PEP content and immutable versions

Owner role: backend
Assignee: Codex
Priority: P1
Status: accepted
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

### P0-11A — Remove reference-source coupling from application services

Owner role: backend
Assignee: Codex
Priority: P1
Status: accepted
Depends on: `P0-11` (accepted)
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

## Planned follow-up

### P0-12 — Prove source-neutral normalization with the PEP fixture

Owner role: backend
Assignee: unassigned
Priority: P2
Status: planned
Depends on: `P0-13` acceptance; owner direction checkpoint
Product: `PROD-P0-01`

#### Goal

Prove a source-neutral normalization and locator-preservation contract using the
bounded PEP fixture as one replaceable conformance case, after the product
service boundary is accepted.

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

`P0-13` is the only assigned card. Its implementer returns it to `review` with
evidence; a separate reviewer accepts it before the contract can be synchronized
to the frontend. `P0-12` remains planned and unassigned until that acceptance
and a later owner checkpoint.

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
| `P0-11` | `done` | Artifact-first exact-byte persistence and immutable source-version admission accepted. |
| `P0-11A` | `done` | Source-neutral acquisition and persistence contracts accepted with reference-source policy isolated in infrastructure. |

Detailed acceptance evidence is retained in the
[completed-task log](docs/development/task-history.md) and Git history.
