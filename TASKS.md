# Contour Active Work

**Status:** two review gates; three ordered follow-ups
**Updated:** 2026-08-24

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
Assignee: Codex
Priority: P1
Status: review
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

- [x] The same admitted fixture produces the same content identity and source
      metadata across repeated runs.
- [x] Unsupported scope and malformed or integrity-invalid content fail before
      accepted knowledge state is written.
- [x] Failure categories are actionable to later retry policy and do not leak
      source payloads or credentials.
- [x] Focused offline tests, `make quality`, `make openapi-check`, and
      `make docs` pass.

Verification: `uv run pytest tests/unit/test_pep_acquisition.py` (6 passed),
`make quality`, `make openapi-check`, and `make docs` pass.

### P0-11 — Persist acquired PEP content and immutable versions

Owner role: backend
Assignee: unassigned
Priority: P1
Status: planned
Depends on: `P0-10`
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

- [ ] The pinned acquisition produces an integrity-verifiable artifact and one
      immutable source-version record with the same digest.
- [ ] Repeating the same acquisition returns the accepted version without
      duplicate durable state or destructive overwrite.
- [ ] Conflicting content, missing artifacts, checksum mismatch, and partial
      failure remain explicit and recoverable.
- [ ] Focused unit and integration checks, `make quality`,
      `make openapi-check`, and `make docs` pass.

### P0-12 — Normalize PEP content without losing evidence locators

Owner role: backend
Assignee: unassigned
Priority: P1
Status: planned
Depends on: `P0-11`
Product: `PROD-P0-01`

#### Goal

Produce a deterministic normalized PEP artifact that later extraction can use
while retaining a verifiable path back to the exact admitted source bytes.

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
the independent review of `P0-08`, then `P0-09`, `P0-10`, `P0-11`, and `P0-12`;
no later card is assigned while its dependency remains unaccepted.

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

Detailed acceptance evidence is retained in the
[completed-task log](docs/development/task-history.md) and Git history.
