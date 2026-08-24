# Contour Active Work

**Status:** one active card; two ordered follow-ups
**Updated:** 2026-08-20

This is the bounded execution queue for work promoted from the ordered
[backend roadmap](docs/development/roadmap.md). Claim exactly one `ready` card
before implementation; a reviewer accepts it, records the result in the
[completed-task log](docs/development/task-history.md), and then archives it.

## Active queue

### P0-08 — Persist the source catalog and evidence core

Owner role: backend
Assignee: Codex
Reviewer: Codex (explicit user assignment)
Priority: P1
Status: review
Depends on: `P0-07` (accepted)
Product: `PROD-P0-01`

#### Goal

Make workspaces, sources, immutable source versions, and exact evidence durable
so later ingestion work has an authoritative catalog to write to and rebuild
from.

#### Requirements

- Add the initial schema and persistence behavior for workspaces, sources,
  source versions, and evidence locators.
- Enforce stable identity, uniqueness, immutable version content, and exactly
  one source version per evidence record where practical in both code and
  storage.
- Implement only the ports exercised by the catalog/evidence use cases with an
  explicit transaction boundary.
- Cover clean migration and representative round trips against an isolated
  PostgreSQL database.
- Do not add entity, relationship, job/run, API, acquisition, or indexing
  behavior in this card.

#### Acceptance criteria

- [x] A clean database migrates to the new schema and repeat migration remains
      safe.
- [x] Workspace, source, immutable version, and evidence records round-trip
      without losing namespace, digest, locator, or unknown-time meaning.
- [x] Duplicate identities, conflicting immutable content, and orphan evidence
      fail rather than silently overwrite accepted state.
- [x] Failed writes do not leave a partially accepted catalog change.
- [x] Relevant unit and opt-in PostgreSQL integration checks, `make quality`,
      `make openapi-check`, and `make docs` pass.
- [x] PostgreSQL rejects an evidence span when exactly one of `start_offset` or
      `end_offset` is null.

Verification: `make test-integration` (28 passed), `make quality` (25 passed,
3 opt-in integration checks skipped), `make docs`, `make openapi-check`, and
`make migration-check`.

Review result (2026-08-24): changes requested. The migrated
`ck_evidence_valid_span` constraint accepts a half-null span because a
PostgreSQL `CHECK` passes when its expression is unknown. A direct transaction
against the migrated schema inserted `start_offset = NULL, end_offset = 1`
successfully before rollback. This violates the domain's both-or-neither span
invariant and can make a later repository read fail while reconstructing the
locator. Correct the constraint through a new forward migration, synchronize
the Core metadata, and add an integration regression that writes directly at
the storage boundary; do not edit the accepted migration revision in place.

Reviewer verification: `make test-integration` (28 passed), `make quality`
(25 passed, 3 opt-in integration checks skipped), `make openapi-check`,
`make docs`, and the rolled-back direct PostgreSQL half-null insertion probe.

Review resolution (2026-08-24): added a forward migration that replaces the
nullable check expression with an explicit both-or-neither predicate,
synchronized the SQLAlchemy Core metadata, and added a direct PostgreSQL
integration regression for a half-null span.

## Scheduled follow-ups

These cards are deliberately `planned`, not simultaneously ready. Promote only
the first card whose dependency has been accepted, and keep one backend card
claimed at a time.

### P0-09 — Persist knowledge and execution records

Owner role: backend
Assignee: Codex
Priority: P1
Status: review
Depends on: `P0-08`
Product: `PROD-P0-01`

#### Goal

Make basic entities, evidence-backed relationships, durable jobs, and distinct
run attempts available to later extraction and worker slices without claiming
that either workflow already executes.

#### Requirements

- Add the initial schema and persistence behavior for entities, relationships,
  jobs, runs, and their required references.
- Preserve edge-level evidence and prevent a credited relationship from being
  stored without evidence or a complete derivation reference.
- Preserve the distinction between one requested job and multiple run attempts,
  including terminal failure and cancellation state.
- Exercise transaction rollback and invalid-reference behavior in isolated
  PostgreSQL integration checks.
- Do not add worker polling, retries, source acquisition, extraction, search, or
  HTTP routes in this card.

#### Acceptance criteria

- [x] Entities and relationships round-trip with stable identity and exact
      evidence references.
- [x] Jobs and run attempts retain explicit lifecycle, failure, cancellation,
      and retry meaning without relying on process memory.
- [x] Orphan evidence, invalid endpoints, invalid transitions, and partial
      writes are rejected safely.
- [x] Relevant unit and opt-in PostgreSQL integration checks, `make quality`,
      `make openapi-check`, and `make docs` pass.

Verification: `make test-integration` (29 passed), `make quality` (25 passed,
4 opt-in integration checks skipped), `make migration-check`, `make docs`, and
`make openapi-check` pass. The local development schema is at `20260824_04`.

### P0-10 — Establish deterministic PEP preflight and acquisition

Owner role: backend
Assignee: unassigned
Priority: P1
Status: planned
Depends on: `P0-09`
Product: `PROD-P0-01`

#### Goal

Prove a credential-free, deterministic supported-source boundary that can
validate and acquire the pinned Phase 0 PEP fixture before durable orchestration
and extraction are introduced.

#### Requirements

- Define the supported PEP source configuration and reject unsupported or
  malformed scope before a job starts.
- Acquire or load a pinned public fixture through the source boundary and
  produce stable content identity plus available upstream revision metadata.
- Classify validation, unavailable-source, timeout, malformed-content, and
  integrity failures without exposing unsafe payloads.
- Keep default tests offline and deterministic; live-network checks, if any,
  must be explicit and non-default.
- Do not add normalization, extraction, indexing, worker execution, or public
  product routes in this card.

#### Acceptance criteria

- [ ] The same admitted fixture produces the same content identity and source
      metadata across repeated runs.
- [ ] Unsupported scope and malformed or integrity-invalid content fail before
      accepted knowledge state is written.
- [ ] Failure categories are actionable to later retry policy and do not leak
      source payloads or credentials.
- [ ] Focused offline tests, `make quality`, `make openapi-check`, and
      `make docs` pass.

## Promotion and handoff rule

For every scheduled follow-up, the coordinator first confirms the dependency is
accepted, then changes only that card to `ready`. An implementer claims exactly
that card, moves it to `review` with verification evidence, and leaves
acceptance and archival to a separate reviewer.

## Recently completed

| Task | Status | Context |
|---|---|---|
| `P0-01` | `done` | Python project and local quality foundation accepted. |
| `P0-02` | `done` | Local PostgreSQL development runtime accepted. |
| `P0-03` | `done` | Continuous-integration quality gate accepted. |
| `P0-04` | `done` | Settings, errors, logging, and health contracts accepted. |
| `P0-05` | `done` | Migration baseline and clean-database test accepted. |

Detailed acceptance evidence is retained in the
[completed-task log](docs/development/task-history.md) and Git history.
