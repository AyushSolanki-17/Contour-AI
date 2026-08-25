# Contour Active Work

**Status:** one active card; one ordered follow-up
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
Status: in-progress
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

- [ ] The pinned acquisition produces an integrity-verifiable artifact and one
      immutable source-version record with the same digest.
- [ ] Repeating the same acquisition returns the accepted version without
      duplicate durable state or destructive overwrite.
- [ ] Conflicting content, missing artifacts, checksum mismatch, and partial
      failure remain explicit and recoverable.
- [ ] Focused unit and integration checks, `make quality`,
      `make openapi-check`, and `make docs` pass.

## Scheduled follow-up

Keep `P0-12` planned until `P0-11` is separately accepted.

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
`P0-11`, then `P0-12`; no later card is assigned while its dependency remains
unaccepted.

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
