# Backend Testing Standard

**Status:** required engineering standard
**Updated:** 2026-08-19

Contour has two separate correctness obligations:

1. **Software correctness:** code follows its contracts under success and failure.
2. **Knowledge correctness:** derived and retrieved records remain accurate, evidence-backed, temporally eligible, and appropriately uncertain.

A green software suite does not prove knowledge quality.

## Test layers

### Unit and property tests

Cover identifiers, hashing, canonicalization, source locators, temporal values, state transitions, entity normalization, relationship construction, metric calculations, and run-manifest serialization. Use property tests for identities, intervals, ordering, and round trips where useful.

### Integration tests

Exercise real PostgreSQL repositories, migrations, artifact adapters, a pinned miniature source fixture, ingestion stages, index rebuilds, and worker restart/retry behavior. Ordinary integration tests make no live network or model calls.

### API contract tests

Verify request/response schemas, error shapes, pagination, idempotency, status transitions, and OpenAPI compatibility. Test the API as an external frontend would; do not rely only on Python object calls.

### Knowledge invariant tests

The blocking invariants in [knowledge model](../architecture/knowledge-model.md) must have direct tests. Include exact source-version citation, evidence locators, no destructive latest overwrite, stable identifiers, reversible merges, and rebuildable projections.

### End-to-end tests

From a clean database and artifact directory, load the pinned fixture, ingest and extract it, build search, query a known entity, resolve its relationship to exact evidence, and inspect the producing run. Keep the pull-request fixture small and deterministic.

### Regression tests

Every confirmed defect gains the smallest permanent test. Maintain explicit cases for overwritten versions, citations to the wrong revision, duplicate ingestion, worker interruption, corrupt artifacts, accidental entity merges, unsupported inputs, permission denial, and secrets in serialized errors.

### Evaluation and benchmarks

When behavior affects extraction, retrieval, ranking, or generation, measure the relevant quality separately from software tests. Report category-level failures, evidence-link accuracy, latency, resource use, model calls, and cost where applicable. Technology admission uses representative end-to-end results, not only microbenchmarks.

## Test data and external systems

- Prefer tiny hand-built cases plus pinned corpus-derived fixtures with license metadata.
- Unit and normal integration tests do not call live models or networks.
- Live-provider suites are explicit, costed, and record provider/model/configuration identity.
- Model output is untrusted and schema-validated before persistence or tool use.
- Retries do not hide nondeterminism or failed attempts.
- Secrets and private data never enter fixtures, snapshots, logs, prompts, or artifacts.

## Pull-request floor

Once the corresponding tooling exists, every backend change should pass formatting, linting, typing, unit/property tests, migration checks, local integration tests, API contract tests, the small end-to-end fixture, and documentation validation relevant to the change.

## Definition of done

A change is done when:

- its objective, scope, non-goals, and acceptance criteria are clear;
- it respects repository and module boundaries;
- success, empty, invalid, duplicate, retry, cancellation, and failure behavior are handled as applicable;
- relevant software and knowledge tests pass;
- migrations are forward-safe and rollback or recovery behavior is documented where relevant;
- secrets, trust boundaries, and external data flow were reviewed in proportion to risk;
- API and documentation describe actual rather than planned behavior; and
- a clean environment can reproduce the result.

An unsuccessful experiment can be complete when the result, evidence, and keep/defer/remove decision are documented. It must not silently enter the reference architecture.
