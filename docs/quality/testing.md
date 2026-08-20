# Backend Testing Standard

**Status:** required engineering standard
**Updated:** 2026-08-20

Contour has two separate correctness obligations:

1. **Software correctness:** code follows its contracts under success and failure.
2. **Knowledge correctness:** derived and retrieved records remain accurate, evidence-backed, temporally eligible, and appropriately uncertain.

A green software suite does not prove knowledge quality.

## Test admission and proportionality

Test count and line coverage are not delivery goals. Admit a permanent test
only when it protects a named behavior, external contract, knowledge invariant,
security property, failure mode, or confirmed regression that is not already
covered at a cheaper layer.

Before adding a test:

1. identify the realistic regression and the observable failure it would cause;
2. find existing coverage and extend or parameterize it when that stays clear;
3. choose the lowest-cost layer that can prove the behavior with useful
   fidelity; and
4. remove overlapping assertions that would fail for the same reason.

Do not add tests merely because a file, class, method, branch, DTO field, or
directory exists. Avoid tests of framework/library behavior, private call
structure, constant values, generated boilerplate, or mocks that only repeat
the implementation. A new module does not require a new test file. Prefer one
representative success case and one case per materially distinct failure class;
parameterize equivalent boundary inputs instead of copying test bodies.

Match the verification budget to risk:

- documentation-only, formatting, and behavior-preserving structural changes
  normally need relevant static/documentation checks and existing tests, not
  new behavioral tests;
- small behavior changes need focused contract or regression coverage;
- persistence, API, integration, or knowledge changes need the affected
  boundary test plus only the lower-level tests required to locate failures; and
- security, concurrency, migration, and blocking knowledge invariants require
  direct tests at the strongest practical boundary.

Consolidate or delete a test when its protected contract disappears, another
test subsumes it, or its maintenance and runtime cost exceed its regression
signal. Do not retain tests as historical artifacts.

## Test layers

The layers below are options selected by affected risk, not a requirement to
duplicate every behavior at every layer.

The filesystem exposes the selected verification boundary rather than mirroring
every production module:

```text
tests/
  architecture/             dependency direction and structural safeguards
  unit/                     external-service-free domain, service, and infrastructure logic
  contract/api/             public HTTP and OpenAPI behavior
  integration/postgres/     real schema, repository, and transaction behavior
  tooling/                  repository-owned quality scripts
  conftest.py               repository-wide test selection only
```

Add `knowledge/`, `end_to_end/`, or `evaluation/` only when those suites contain
real admitted checks. Shared fixtures remain at the narrowest directory that
uses them. Do not create a test file merely to mirror a production file; group
tests by the contract or failure boundary they protect.

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

Every backend change passes the available fast deterministic floor: formatting,
linting, typing, the default service-free test suite, and relevant documentation
validation. Run migration, PostgreSQL integration, API contract, knowledge
invariant, end-to-end, evaluation, or benchmark suites only when the change can
affect that boundary or when its acceptance contract explicitly requires them.
Record any relevant suite that could not run; do not run or expand unrelated
suites merely to increase test counts.

The dedicated CI PostgreSQL job runs `make test-integration` for migration or
persistence changes against an ephemeral service. Locally, these checks remain
explicitly selected so the default suite never mutates a developer database.

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
