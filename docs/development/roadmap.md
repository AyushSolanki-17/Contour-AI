# Backend Development Roadmap

**Status:** planned; Phase 0 is the active implementation scope
**Updated:** 2026-08-30

## Planning rule

Build one vertical source-to-evidence path before broadening the platform. Each step must leave a testable backend contract and preserve the invariants in the [knowledge model](../architecture/knowledge-model.md).

The supported sample corpus is a replaceable conformance workload, not a
product dependency. Establish source-neutral application services and the
versioned contract consumed by the browser before deepening sample-specific
normalization, extraction, or ecosystem coverage. A planned follow-up is not
implicitly authorized when its predecessor reaches review.

The bounded [active task queue](../../TASKS.md) turns the earliest incomplete
step into reviewable implementation cards. It is an execution view, not a second
roadmap; completion and ordering continue to be controlled here.

## Phase 0 ticket map

The IDs below are stable sequencing handles. Only cards materialized as
`ready` in `TASKS.md` are claimable; a reserved roadmap ID is not an
assignment.

| Roadmap step | Local ticket | State or promotion gate |
|---|---|---|
| 0.3 tenant-owned persistence | `P0-13A` | ready after the 2026-08-30 multi-tenant MVP checkpoint |
| 0.4 Principal/Membership service enforcement | `P0-13B` | planned after `P0-13A` acceptance |
| 0.5 authenticated Tenant/Workspace/Source contract | `P0-13` | planned after `P0-13B` acceptance and contract checkpoint |
| 0.6 normalization conformance | `P0-12` | planned after `P0-13` acceptance |
| 0.7 bounded real Reference Profile | `P0-14` | reserve; shape after `P0-12` acceptance and source-terms review |
| 0.8 durable execution | `P0-15` | reserve; shape after the admitted profile manifest exists |
| 0.9 execution API contract | `P0-17A` | reserve; shape after `P0-15` lifecycle behavior is frozen; acceptance unblocks frontend progress work |
| 0.10 extraction and search | `P0-16` | reserve; shape after the execution contract is accepted; may run while frontend progress work proceeds |
| 0.11 exploration API contract | `P0-17B` | reserve; shape after `P0-16` extraction/search behavior is frozen |
| 0.12–0.13 trust floor and backend integration | `P0-18` | reserve; shape after all Phase 0 contracts are published |

When a reserved ID is promoted, its card must name the observable user or
client outcome, dependency state, contract effect, failure behavior, non-goals,
and verification budget. Do not combine multiple rows merely to reach the
showcase sooner; do not split one behavior only to manufacture ticket volume.

## Phase 0 sequence

### 0.1 — Repository and runtime foundation

- establish one Python project, `src` package layout, locked development environment, formatting, linting, typing, tests, and CI;
- add local PostgreSQL and repeatable configuration without committed secrets;
- define structured settings, errors, logging, and health/readiness behavior; and
- add migration tooling and a clean-database test.

### 0.2 — Domain and persistence foundation

- implement typed identifiers and Phase 0 domain objects;
- define capability-specific repository and provider ports independently of FastAPI and PostgreSQL;
- create initial migrations for workspaces, sources, versions, evidence, entities, relationships, jobs, and runs; and
- enforce immutability, uniqueness, and evidence-reference invariants in both code and storage where practical.

### 0.3–0.5 — Tenant isolation and first product contract

- make Tenant the durable owner of every Workspace and every reachable Source,
  Version, Evidence, Entity, Relationship, Job, and Run;
- enforce provider-neutral Principal, Membership, and Access Context boundaries
  at every product-facing service before adding HTTP routes;
- expose source-neutral Tenant, Workspace, and Source use cases through
  application services;
- publish the authenticated versioned contract with stable validation, error,
  non-enumeration, tenant-bound pagination, and idempotency behavior;
- keep routes thin and synchronize the generated contract before frontend
  integration; and
- keep source-specific identifiers, URL rules, formats, and parsing outside
  reusable services and public schemas.

Two Principals with different Tenants must be unable to cross through direct or
nested IDs, relationship/evidence links, jobs/runs, cursors, idempotency keys,
search/index state, artifacts, logs, or errors. A route Tenant ID is a selector,
never authorization evidence. Enterprise SSO, invitations, custom roles, SCIM,
billing, and governance are not part of this gate.

### 0.6 — Reference-source ingestion

- use the deterministic PEP fixture only as the first replaceable adapter and
  conformance case;
- acquire or load a pinned fixture, compute content identity, and persist an immutable version;
- normalize through a source-neutral transformation contract without losing
  exact source locators; and
- make repeated ingestion idempotent.

The acquisition adapter was implemented before the first product contract. Do
not extend its normalization or extraction until the source-neutral
Tenant/Workspace/Source service and HTTP boundary above are accepted.

### 0.7 — Bounded real Reference Profile

- admit a versioned Reference Profile manifest that maps source-native records
  into generic Domain, Connector, Source, Version, Entity, Evidence,
  Relationship, and Event kinds;
- use one bounded public software-organization release as the first product
  demonstration, with the example organization named only inside source
  adapters, acquisition manifests, fixtures, and provenance;
- target seven to nine decision-bearing public source feeds covering project
  metadata, work items, changes, builds, releases, organizational guidance,
  product documentation/deprecations, public incidents/security notices, and
  official disclosures;
- record source terms or license, retrieval cutoff, checksums, rate limits,
  attribution, redistribution boundary, exact locators, and known missing
  private context before checking in any content; and
- keep default tests offline through pinned miniature inputs or repeatable
  manifests rather than live-network calls.

The profile proves a real source-to-evidence workflow. It does not declare nine
maintained connectors: several feeds may share one HTTP, repository, or document
connector capability, and every feed must change a visible question,
uncertainty, or evidence path.

### 0.8 — Durable execution

- persist job requests and run attempts;
- execute acquisition, normalization, extraction, and indexing as observable stages;
- support retry, cancellation, duplicate delivery, and worker restart; and
- retain stage outputs, failures, configuration identity, and artifact digests.

### 0.9 — Execution API contract

- publish only the accepted ingestion, Job, Run, retry, cancellation, and
  progress behavior needed by the browser;
- preserve verified Tenant/Workspace scope through requests, lifecycle state,
  polling or streaming if admitted, and stable errors; and
- synchronize the generated contract so frontend progress work may proceed
  while backend extraction/search continues.

### 0.10 — Extraction and search

- deterministically extract generic entities, exact evidence, and basic
  relationships from the small PEP conformance input and the bounded real
  Reference Profile;
- retain evidence and extractor identity for every derived record;
- build PostgreSQL full-text search over admitted source content and entities; and
- test known lookup, empty results, stale versions, and duplicate inputs.

### 0.11 — Exploration API contract

- publish search, Entity, Relationship, Evidence, Version, and Run inspection
  routes after extraction/search semantics are accepted;
- expose versioned FastAPI routes with consistent validation, errors, pagination, and idempotency;
- require verified Access Context and preserve Tenant scope through every
  cursor, identifier, retry, and response;
- publish an OpenAPI contract usable by separately deployed frontend repositories; and
- add API contract tests that exercise services without frontend code in this repository.

### 0.12 — Reproducibility and trust floor

- add deterministic fixtures and knowledge-invariant tests;
- verify artifact integrity, rebuildability, and migration behavior;
- redact secrets and unsafe payloads from errors, logs, traces, and fixtures;
- add minimal run correlation and stage metrics; and
- document local startup and the supported sample workflow.

### 0.13 — Phase 0 integration gate

Prove the complete acceptance path in [backend architecture](../architecture/backend.md): clean startup and migration, authenticated Tenant/Workspace creation, supported-Source ingestion, interruption recovery, search, Entity/Relationship inspection, exact Evidence resolution, and producing-Run inspection. Use two Principals and two Tenants and prove the second cannot enumerate or cross the first through any product path.

## Later capability order

After Phase 0 is accepted:

1. provenance-aware exploration and hybrid retrieval;
2. structured cited investigations with conflicts and unknowns;
3. bounded relationship traversal and possible-impact paths;
4. current/as-of state and change review;
5. guarded agentic investigations compared with deterministic and single-agent references;
6. governance for real private multi-user deployments;
7. data lineage and larger batch workloads;
8. measured scale optimizations and specialized infrastructure; and
9. user-facing evaluation and versioned domain packs.

## Technology admission

Do not add Neo4j, a dedicated vector store, Redis, Kafka, a warehouse, Rust, or an agent framework because it appears later in the roadmap. Admission requires a declared workload, a simple reference implementation, correctness parity, an end-to-end measurement, operational and security review, and a recorded keep/defer/remove decision.

## Backend completion contract

A roadmap item is complete only when its API or application contract works, migrations and failure behavior are covered, relevant tests and knowledge-quality checks pass, documentation describes actual behavior, and reproduction commands work from a clean environment.
