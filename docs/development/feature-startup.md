# Feature Startup and Architecture Stability

**Status:** required design protocol for non-trivial implementation
**Updated:** 2026-09-01

Contour has an accepted modular-monolith architecture. Feature work starts by
placing behavior in that architecture, not by reopening the package layout.
This protocol keeps the codebase adaptable without turning architecture into a
recurring refactoring project.

## Startup phase

Before editing production code for a non-trivial feature or fix:

1. State the observable contract, invariant, failure mode, or operational need.
2. Name the owning business capability and trace its current route or worker,
   service, port, infrastructure implementation, transaction, schema, and tests.
3. Use the placement table below to identify the smallest set of owners that
   must change. An empty box is valid; every request does not need every layer.
4. Search for an existing concept, use case, port, adapter, error, and
   transaction boundary before introducing another name or abstraction.
5. Identify compatibility, tenant isolation, idempotency, concurrency,
   migration, rollback, secret, and external-failure implications that are
   relevant to this change. Do not manufacture concerns that the path cannot
   encounter.
6. Select the cheapest tests that can fail for the real regression, then make
   one vertical increment through the required owners.

Implementation is ready to start when the capability owner, dependency
direction, transaction boundary, public contract impact, and verification plan
are explicit. A separate design document is unnecessary when those answers are
small and obvious.

## Placement table

| Responsibility | Owner |
|---|---|
| Business identity, state transition, or invariant | `<capability>/domain/<concept>.py` |
| Transport-neutral use case, sequencing, policy, or safe application error | `<capability>/application/<use_case>.py`; explicit cross-capability atomic workflows under `workflows/` |
| Persistence behavior required by a use case | `<capability>/application/ports.py` or an existing behavior-specific port |
| PostgreSQL query, row mapping, constraint, or transaction implementation | `infrastructure/postgres/` |
| Artifact, source, authentication, or provider implementation | `infrastructure/<technology-or-capability>/` |
| HTTP parsing, authentication extraction, schema, cursor, response, or status mapping | `api/` |
| Future CLI command, output formatting, and exit-code mapping | `cli/` |
| Dependency construction and process resource lifetime | `composition/<executable>.py` |
| Durable schema transition | a new immutable Alembic revision plus matching Core metadata |

HTTP, a future CLI, workers, and scheduled jobs are peer delivery adapters.
They call services directly and never call one another. PostgreSQL and provider
implementations satisfy ports and are constructed only by composition code.

## Adding a route, use case, or connector

For an admitted source-refresh endpoint, put the route in
`api/routers/v1/sources.py` and any new request/response schema in
`api/schemas/v1/sources.py`. The existing router receives source and tenant use
cases explicitly. Add the source-refresh use case under `sources/application/`,
extending an existing cohesive module when appropriate. Receive verified access,
keep source policy there, and add only required persistence behavior to
`sources/application/ports.py`. Implement Core queries in the existing source
repository or a new concept-owned adapter if it has an independent reason to
change. Wire dependencies in `composition/http.py`. There is no registration
framework to learn and no refresh behavior is implemented merely by this example.

Extend HTTP contract tests for input, output and errors, source unit tests for
new policy, and PostgreSQL integration tests for changed atomicity or
constraints. Run `make openapi` and `make openapi-check` for intentional
public contract changes. Current collection routes expose creation and listing;
this organization does not add item lookup, refresh, or execution APIs.

A new tenant endpoint follows the same path in `api/routers/v1/tenants.py`,
`api/schemas/v1/tenants.py` and `tenancy/application/`. A new capability starts
with its actual domain and use case, not empty folders or generic CRUD classes.
Add ports only for required I/O or consistency boundaries. Architecture checks
discover capability domain/application directories automatically.

A new source connector belongs under `infrastructure/source/`. Keep native
configuration, validation, acquisition and provider-error translation together
while they form one cohesive adapter. Return the existing source-neutral
`AcquiredContent` value and reuse `SourcePersistenceService` for artifact-first
admission. Add a pinned offline conformance fixture and explicit composition
when that connector becomes an executable path. PEP preflight currently expects
native `SOURCE:PEP` identities, while HTTP registration uses opaque IDs;
registration-to-acquisition orchestration is still planned work and must define
that mapping before claiming an end-to-end ingestion endpoint.

## Architecture-change admission gate

Do not start another repository-wide architecture refactor by default. Change
an accepted boundary only when at least one concrete trigger exists:

- the current owner would require a forbidden dependency;
- one module has acquired independent responsibilities with different reasons
  to change and a smaller split makes ownership clearer;
- duplicate abstractions or names cause two competing paths for the same work;
- a second real delivery or infrastructure implementation cannot use the
  existing contract without transport or vendor leakage;
- measured reliability, security, operability, or performance evidence shows
  that the existing boundary is inadequate; or
- an accepted product requirement changes the deployment, consistency, or
  ownership model.

File count, line count alone, personal naming preference, architectural fashion,
and hypothetical future scale are not admission evidence. A new abstraction
must solve the demonstrated problem more clearly than extending the existing
code.

An admitted architecture change must be completed in one coherent sequence:

1. record the requirement, simpler alternative, dependency direction, failure
   and security implications, compatibility or migration path, and removal or
   rollback path in the owning architecture section;
2. change callers, implementation, tests, executable wiring, generated
   contracts, and documentation together;
3. remove replaced modules and internal compatibility wrappers;
4. add or strengthen an executable fitness check for the regression that made
   the change necessary; and
5. finish with one architecture and one vocabulary.

After that sequence passes review, the resulting boundary is the new default.
Ordinary feature work extends it; agents must not repeatedly propose equivalent
layer-first versus feature-first reshuffles without new admission evidence.

## Vertical increment and stop rule

Keep each batch runnable and reviewable. After a meaningful batch, inspect the
diff and run its focused formatting, lint, typing, tests, architecture checks,
migration checks, OpenAPI drift check, and documentation checks. Continue only
after the batch is stable.

Stop expanding the change when the stated contract and invariants pass at the
correct boundaries. Do not add adjacent frameworks, generalized bases, future
packages, duplicate DTOs, or cleanup unrelated to the traced path. Follow-up
work needs its own accepted requirement; “while we are refactoring” is not one.
