# Contour Active Work

**Status:** one principal-membership card in review; two dependency-gated follow-ups
**Updated:** 2026-08-31

This is the bounded execution queue for work promoted from the ordered
[backend roadmap](docs/development/roadmap.md). Claim exactly one `ready` card
before implementation; a reviewer accepts it, records the result in the
[completed-task log](docs/development/task-history.md), and then archives it.

## Accepted predecessor

`P0-13A` was accepted after review of merged implementation PR #10 and the
verification handoff in PR #12. The product owner authorized `P0-13B` to begin
on 2026-08-30.

### P0-13A — Establish tenant-owned persistence boundaries

Owner role: backend
Assignee: Codex
Priority: P0
Status: accepted
Depends on: `P0-11` and `P0-11A` (accepted); 2026-08-30 owner direction checkpoint accepted
Product: `PROD-P0-01`
Contract: no new HTTP routes; the generated OpenAPI artifact must remain health-only

#### Current handoff

Accepted after review of the merged tenant-ownership implementation and its
green quality, PostgreSQL persistence, migration, and secret-scan checks.

#### Goal

Make a Tenant the durable ownership and security boundary before any product
data is exposed through HTTP. Every Workspace and every record reachable from
it must belong to exactly one Tenant, and the database must reject cross-tenant
associations even when an application caller supplies valid foreign IDs.

#### Requirements

- Add a generic Tenant domain/persistence boundary and make every Workspace
  belong to exactly one Tenant; Tenant and Workspace remain distinct because a
  Tenant is the security owner while a Workspace is a context partition.
- Extend durable ownership through Source, Source Version, Evidence, Entity,
  Relationship, Job, and Run records. A record must be traceable to one Tenant
  through its Workspace without relying on an optional convention.
- Close current association gaps: evidence attachments, relationship endpoints,
  producing jobs/runs, and future-derived records must not link objects owned by
  different Workspaces or Tenants.
- Add a forward migration that handles a populated pre-tenant database
  deterministically and atomically, documents its compatibility/recovery
  behavior, and never leaves nullable or ambiguous ownership.
- Keep generic identities, repositories, migrations, and architecture checks
  free of Reference Profile, Connector-vendor, PEP, or organization-specific
  policy.
- Preserve all accepted health behavior and the source-neutral acquisition and
  artifact contracts.

#### Non-goals

- Do not add Principal, Membership, authentication middleware, product HTTP
  routes, frontend behavior, invitations, roles, SSO, billing, or governance.
- Do not add normalization, extraction, indexing, workers, ingestion progress,
  live-network acquisition, or source-specific behavior.

#### Verification budget

- Reuse the existing source-neutral architecture check, OpenAPI drift checks,
  PostgreSQL catalog/record integration modules, clean-migration test, and
  existing transaction boundaries.
- Add no more than one new tenant-isolation integration module and six permanent
  behaviors: Tenant/Workspace ownership, ownership propagation, cross-workspace
  relationship rejection, cross-tenant evidence rejection, populated-database
  migration, and atomic failure/recovery. Six cases are justified because this
  card changes both the security boundary and the durable schema.
- Extend existing table/architecture checks in place. Add no auth/provider,
  HTTP, runner, service, network, or fixture dependency.
- Report cases and modules added, consolidated, or removed and any default-suite
  runtime change at handoff.

#### Acceptance criteria

- [x] Every Workspace has exactly one durable Tenant owner, and every existing
      Phase 0 record has an unambiguous ownership path through that Workspace.
- [x] PostgreSQL rejects cross-workspace and cross-tenant evidence,
      relationship, job, and run associations atomically.
- [x] A database at the prior migration head, including representative existing
      rows, upgrades without data loss or ambiguous ownership and has a
      documented recovery path.
- [x] Source-neutral architecture and accepted acquisition/artifact behavior do
      not regress.
- [x] The generated OpenAPI artifact remains health-only and passes drift,
      focused PostgreSQL, migration, quality, and documentation checks.

#### Verification evidence

- `make db-up` and `make db-ready` started and verified PostgreSQL; the tracked
  forward migration upgraded the local database to `20260830_06 (head)`.
- With the repository's local database configuration exported, `make
  test-integration` passed: 49 tests, including the populated-database migration
  and three tenant-isolation contracts.
- `make migration-check` reported no new upgrade operations. `make quality`
  passed formatting, linting, strict typing, default tests (41 passed, 8
  integration tests skipped), and OpenAPI drift. `make docs` and `make
  precommit` passed.
- Test delta: one tenant-isolation PostgreSQL module added with three behavioral
  cases (ownership propagation, cross-owner association rejection, and atomic
  rollback); the existing migration module adds populated-database migration
  coverage. No tests were consolidated or removed. The default suite completed
  in 0.37 seconds; no dependency, runner, or fixture category changed.

## Active queue

### P0-13B — Enforce principal membership and tenant-scoped services

Owner role: backend
Assignee: Codex
Priority: P0
Status: review
Depends on: `P0-13A` (accepted)
Product: `PROD-P0-01`
Contract: transport-neutral application boundary; no new HTTP routes

#### Goal

Require every product use case to execute with an authenticated Principal and
a verified Membership for exactly one Tenant, so tenant isolation is enforced
above persistence before HTTP routes are published.

#### Requirements

- Define provider-neutral Principal, Membership, and Access Context contracts.
  A client-supplied Tenant ID is a selector, never proof of access.
- Creating a Tenant atomically creates the initiating Principal's Membership.
  Listing or opening Tenants returns only memberships visible to that Principal.
- Refactor existing Workspace, catalog-admission, knowledge-record, artifact,
  and future execution service/repository entry points to require verified
  Tenant scope; unsafe unscoped lookup must not remain available to delivery
  code.
- Return one non-enumerating inaccessible/not-found application outcome for a
  foreign Tenant or foreign nested ID. Do not expose whether the object exists.
- Define the portable scope that later job/run payloads, cursors, idempotency,
  search, artifacts, logs, and traces must carry without implementing those
  later features in this card.
- Keep membership capabilities deliberately uniform in the MVP. The data model
  may support later policy evolution, but no custom role semantics are accepted
  here.

#### Non-goals

- No FastAPI auth middleware, bearer-token parsing, login UI, invitations,
  membership administration, SSO/OIDC provider SDK, SCIM, RBAC/ABAC, billing,
  quotas, or audit console.
- No new product routes, normalization, ingestion, or search behavior.

#### Verification budget

- Reuse tenant-persistence integration evidence and existing application/
  repository contract tests.
- Add at most one access-context module and five permanent behaviors: Tenant
  bootstrap, visible-Tenant listing, authorized nested operation, foreign-ID
  non-enumeration, and cross-tenant mutation/link rejection. Parameterize
  existing service families instead of repeating each at multiple layers.
- Add no identity-provider, HTTP, network, browser, or test-runner dependency.

#### Acceptance criteria

- [x] Two Principals can own separate Tenants and can observe only their own
      Tenant, Workspace, Source, Evidence, Entity, Relationship, Job, and Run
      state through application services.
- [x] Foreign and guessed nested IDs produce the same safe inaccessible result
      as an unknown ID and cause no durable mutation.
- [x] No product-facing service or repository entry point can be invoked without
      a verified Access Context.
- [x] Logs/errors from the focused checks include safe correlation scope but no
      credential, source content, or foreign-object detail.
- [x] Focused service, persistence, architecture, quality, documentation, and
      unchanged health-contract checks pass.

#### Verification evidence

- `make quality` passed: formatting, linting, strict typing, default tests
  (37 passed, 8 integration tests skipped), and unchanged health-only OpenAPI
  drift verification.
- `make docs` and `make precommit` passed. `uv run python -m compileall -q src
  tests migrations` and integration-suite collection both passed.
- Local `make db-up` could not start PostgreSQL because the Docker daemon socket
  was unavailable. Pull-request CI subsequently passed its isolated PostgreSQL
  migration and persistence suite (45 passed).
- Test delta: one focused unit module adds the bootstrap, visible-Tenant, and
  non-enumerating foreign/unknown selector behaviors; existing catalog,
  immutable-source, knowledge/execution, tenant-isolation, and migration cases
  now carry Access Context. No tests were removed or consolidated. The default
  suite completed in 0.26 seconds.

### P0-13 — Publish the authenticated tenant/workspace/source contract

Owner role: backend
Assignee: unassigned
Priority: P1
Status: planned
Depends on: `P0-13B` accepted; owner contract checkpoint
Product: `PROD-P0-01`
Contract: frozen planned six-route `/api/v1` collection contract below; current generated artifact remains health-only until implementation

#### Goal

Give the browser its first real product capability through an authenticated,
source-neutral Tenant, Workspace, and Source HTTP contract.

#### Frozen observable contract

The card publishes exactly six collection routes:

- `POST /api/v1/tenants` creates a Tenant from `name`, atomically grants the
  authenticated Principal its initial Membership, and returns `201` with stable
  `id` and `name`.
- `GET /api/v1/tenants` lists only the authenticated Principal's Tenants.
- `POST /api/v1/tenants/{tenant_id}/workspaces` creates a Workspace from `name`
  and returns `201` with stable `id`, `tenant_id`, and `name`.
- `GET /api/v1/tenants/{tenant_id}/workspaces` lists only Workspaces in that
  accessible Tenant.
- `POST /api/v1/tenants/{tenant_id}/workspaces/{workspace_id}/sources`
  registers a Source from generic `connector_kind`, `canonical_locator`,
  `scope`, nullable `license`, and `data_classification`, returning those fields
  plus stable Tenant, Workspace, and Source IDs.
- `GET /api/v1/tenants/{tenant_id}/workspaces/{workspace_id}/sources` returns
  the same complete Source representation.

Collection reads use deterministic ordering and optional opaque `cursor` and
`limit`; `limit` defaults to 50 and cannot exceed 100. A cursor is bound to the
authenticated Principal, Tenant, route, and query shape and cannot be replayed
across Tenants. Source-native identifiers remain provenance, not route shape.

All three `POST` routes require a 1–128 character visible-ASCII
`Idempotency-Key`. The first accepted request returns `201`; the same scoped key
and payload returns `200` with the original representation; a different payload
returns `409 request.idempotency_conflict`. Scope includes authenticated
Principal, Tenant where present, method, and route family, so the same literal
key in another Tenant cannot collide or replay data. Duplicate Connector kind
plus canonical locator within one Workspace returns
`409 source.already_registered`; unknown Connector kinds return
`422 source.unsupported_connector`. Idempotency is durable across concurrent
requests and restart, and failed requests leave no reservation or partial data.

`GET /health/live` and `GET /health/ready` remain unauthenticated. Every
`/api/v1` route requires a valid bearer credential verified by a provider-
neutral adapter; missing, invalid, or expired credentials return
`401 auth.unauthenticated`. The local/demo adapter reads configured opaque
credentials outside source control and never exposes them to a browser bundle.
An inaccessible or mismatched Tenant, Workspace, or Source returns the same
`404 resource.not_found` envelope as an unknown ID. Validation is `422`,
conflicts are `409`, and infrastructure failure remains redacted
`503 dependency.unavailable` in the existing error envelope.

#### Non-goals

- No password/login endpoint, invitation flow, membership-management route,
  SSO/OIDC vendor integration, custom roles, ABAC, billing, quota, audit UI,
  ingestion, normalization, search, or source-specific schema.
- Do not publish individual-resource endpoints or adjacent APIs not listed
  above.

#### Verification budget

- Reuse access-context/service tests, PostgreSQL migration coverage, common
  error envelope, source-neutral architecture check, and OpenAPI drift checks.
- Add at most one API-contract module and six permanent behaviors: auth/health
  boundary, Tenant create/list, Workspace create/list, Source create/list,
  scoped idempotency/cursor behavior, and parameterized foreign-ID/validation/
  dependency failures. Six cases are justified by the combined public-contract
  and tenant-isolation risk.
- Add no hosted identity provider, browser runner, live-network dependency, or
  source-specific fixture. Extend persistence coverage in place if needed.

#### Acceptance criteria

- [ ] An authenticated client can create/list its Tenant, create/list a
      Workspace, and register/list a Source using only the generated contract.
- [ ] A second Principal and Tenant cannot discover or operate on the first
      Tenant through list results, guessed IDs, cursors, or idempotency keys.
- [ ] Ordering, limit, cursor, idempotency, duplicate, validation, unsupported,
      redaction, and restart/concurrency behavior match the frozen contract.
- [ ] Health stays public, every product route is authenticated, and no secret
      is committed, logged, serialized, or exposed to the browser.
- [ ] The generated OpenAPI artifact passes drift checks and is ready for an
      intentional frontend snapshot update.
- [ ] Focused service, API, PostgreSQL, quality, documentation, and contract
      checks pass.

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

- Define normalized content and transformation results without PEP-specific
  types or policy in domain and reusable application services.
- Normalize the pinned supported PEP fixture deterministically in its adapter
  and retain the source-version identity, transformation identity, and locator
  mapping needed to resolve normalized fields or spans to exact source
  evidence.
- Store normalized output as a rebuildable content-addressed artifact with its
  own integrity digest and explicit derivation from the raw version.
- Preserve structured-header and byte-span meaning where available, and keep
  absent or unknown source values explicit.
- Classify malformed input, unsupported structure, locator loss, and integrity
  mismatch without accepting partial normalized state.
- Keep default tests offline and deterministic.
- Do not add entity or relationship extraction, search indexing, workers, or
  public product routes in this card.
- Do not broaden to additional PEPs or another source ecosystem; the fixture is
  a contract proof, not a product commitment.

#### Acceptance criteria

- [ ] Repeated normalization of the same admitted bytes produces the same
      normalized digest and transformation metadata.
- [ ] Representative normalized headers and content resolve to exact locators
      in the immutable source version.
- [ ] Malformed input, locator loss, and corrupt derived artifacts fail rather
      than becoming accepted evidence.
- [ ] Focused invariant and integration checks, `make quality`,
      `make openapi-check`, and `make docs` pass.

#### Verification budget

- Reuse the acquired-content determinism, artifact-integrity, source-neutral
  architecture, and PostgreSQL catalog cases.
- Add at most one normalization-focused module and four permanent behaviors:
  deterministic success, locator preservation, malformed/unsupported input,
  and corrupt or integrity-mismatched derived output.
- Keep all default checks offline; add no runner, service, live-network input,
  broad fixture family, or duplicate persistence assertion.
- Report test files/cases and default-suite runtime changes at handoff.

## Promotion and handoff rule

The coordinator first synchronizes the local and private ledgers and gives the
owner a checkpoint stating what is accepted, what remains in review, the one
next proposed card, why it is next, and what remains deferred. A planned card
stays unassigned; there are no dependency-gated reserve assignments.

The owner replaced the earlier single-user assumption with a multi-tenant MVP
requirement on 2026-08-30. `P0-13A` is accepted, and the owner explicitly
authorized `P0-13B` as the one active card. `P0-13` and `P0-12` remain planned
and unassigned in that order. An implementer moves the active card to `review`
with evidence, and acceptance and queue refill remain a reviewer/coordinator
decision unless the owner explicitly directs otherwise.

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
| `P0-13A` | `done` | Tenant-owned durable persistence with composite foreign-key isolation and populated-database migration accepted. |

Detailed acceptance evidence is retained in the
[completed-task log](docs/development/task-history.md) and Git history.
