# Backend Development Roadmap

**Status:** planned; Phase 0 is the active implementation scope
**Updated:** 2026-08-19

## Planning rule

Build one vertical source-to-evidence path before broadening the platform. Each step must leave a testable backend contract and preserve the invariants in the [knowledge model](../architecture/knowledge-model.md).

The bounded [active task queue](../../TASKS.md) turns the earliest incomplete
step into reviewable implementation cards. It is an execution view, not a second
roadmap; completion and ordering continue to be controlled here.

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

### 0.3 — Supported source ingestion

- implement a deterministic PEP source adapter and preflight validation;
- acquire or load a pinned fixture, compute content identity, and persist an immutable version;
- normalize content without losing exact source locators; and
- make repeated ingestion idempotent.

### 0.4 — Durable execution

- persist job requests and run attempts;
- execute acquisition, normalization, extraction, and indexing as observable stages;
- support retry, cancellation, duplicate delivery, and worker restart; and
- retain stage outputs, failures, configuration identity, and artifact digests.

### 0.5 — Extraction and search

- deterministically extract PEP identities, selected headers, and basic relationships;
- retain evidence and extractor identity for every derived record;
- build PostgreSQL full-text search over admitted source content and entities; and
- test known lookup, empty results, stale versions, and duplicate inputs.

### 0.6 — Service and API contracts

- implement workspace, source, ingestion, search, entity, relationship, evidence, and run services;
- expose versioned FastAPI routes with consistent validation, errors, pagination, and idempotency;
- publish an OpenAPI contract usable by separately deployed frontend repositories; and
- add API contract tests that exercise services without frontend code in this repository.

### 0.7 — Reproducibility and trust floor

- add deterministic fixtures and knowledge-invariant tests;
- verify artifact integrity, rebuildability, and migration behavior;
- redact secrets and unsafe payloads from errors, logs, traces, and fixtures;
- add minimal run correlation and stage metrics; and
- document local startup and the supported sample workflow.

### 0.8 — Phase 0 integration gate

Prove the complete acceptance path in [backend architecture](../architecture/backend.md): clean startup and migration, workspace creation, supported-source ingestion, interruption recovery, search, entity/relationship inspection, exact evidence resolution, and producing-run inspection.

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
