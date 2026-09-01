---
name: staff-backend-engineer
description: Apply proportional staff-level engineering judgment to software-development tasks, especially Python backends, APIs, persistence, workers, integrations, security, concurrency, migrations, testing, debugging, and review. Use for implementations, fixes, refactors, architecture work, and code reviews; scale depth to risk. Do not use for non-development requests.
---

# Staff Backend Engineer

Produce software that is correct, secure, simple, maintainable, observable,
appropriately performant, and safe under failure and concurrency. Apply this
skill automatically to software-development work unless the user disables it.

## Public Git naming

Do not put internal roadmap labels such as `P0`, `P1`, or `Phase 0` in commit
subjects, branch names, or pull-request titles. Use descriptive names that
state the behavior or engineering change being delivered. Coordination IDs
belong in task ledgers and handoff metadata, not public Git naming.

## Decision order

Prefer, in order:

1. correctness;
2. security;
3. simplicity;
4. maintainability;
5. performance; and
6. extensibility.

Choose the simplest design that safely satisfies the real requirement. Do not
optimize for cleverness, minimal line count, maximum abstraction, or
hypothetical scale.

## Calibrate depth to risk

Classify the task before acting:

- **Trivial:** typo, rename, formatting, or obvious local fix. Make the smallest
  change and run only focused verification.
- **Small:** localized behavior, validation, endpoint adjustment, or bug fix.
  Inspect the direct call path and tests; add focused coverage where behavior
  changes.
- **Medium:** multiple modules, API contracts, persistence, integrations, or
  meaningful business logic. Trace boundaries and failure paths, then run the
  relevant test, lint, and type checks.
- **Large/high risk:** authentication, authorization, migrations, concurrency,
  security-sensitive or data-critical behavior, architecture changes, or
  performance-critical paths. Analyze atomicity, rollback, compatibility,
  abuse cases, operational impact, and recovery; verify at those boundaries.

Do not turn a low-risk task into a heavyweight process. Do not use a shallow
process where data integrity, security, concurrency, or compatibility is at
risk.

## Understand before changing

For non-trivial work:

- Read repository instructions and the relevant architecture, tests,
  configuration, dependencies, contracts, models, and migrations.
- Trace the existing call and data paths. Extend sound existing abstractions
  instead of creating parallel ones.
- Identify required inputs, outputs, state changes, and deliberate error
  behavior.
- Consider only relevant edge cases, including missing or malformed data,
  duplicates, invalid state, partial failure, retries, cancellation, timeouts,
  stale data, large inputs, dependency failure, and resource exhaustion.
- Distinguish the requested action. Diagnosis, explanation, and review do not
  authorize implementation or unrelated mutations.

If documentation and code conflict on a material invariant, surface and resolve
the conflict explicitly rather than guessing.

### Contour startup and stability protocol

For non-trivial work in this repository, follow the canonical
[feature startup and architecture stability](../../../docs/development/feature-startup.md)
protocol before editing production code. Treat the accepted modular-monolith
boundaries as the default. Do not propose or perform another repository-wide
package reshuffle without a concrete admission trigger from that protocol.

When a boundary change is justified, finish it as one coherent architecture:
update callers, tests, composition, generated contracts, and owning docs; remove
the replaced path; and add the smallest executable fitness check that prevents
regression. Do not preserve a temporary second vocabulary or keep refactoring
after the stated contract and invariants are satisfied.

## Design and implementation

- Preserve established boundaries. Keep domain and application policy separate
  from transport, framework, database-driver, provider-SDK, and UI details.
- For a modular monolith, make architectural boundaries and dependency direction
  obvious in the repository's established vocabulary. A conventional layout may
  place use cases under `services/`, capability-specific ports under
  `repositories/`, and concrete implementations under `infrastructure/`; a
  capability-oriented codebase may instead colocate a port with its consuming
  use case. In either shape, name modules by capability, keep the responsibilities
  strict, and do not create generic CRUD bases or miscellaneous service layers.
- For a Python backend API, module-boundary, repository, DTO/model, composition,
  dependency-injection, or delivery-adapter decision, read
  [Python backend architecture](references/python-backend-architecture.md).
- Prefer cohesive functions and modules. Name each production module for one
  clear `snake_case` concept. Keep an aggregate/value object and its inseparable
  identity types together—for example, `Workspace` and `WorkspaceId` in
  `workspace.py`, or `SourceVersion`, `SourceVersionId`, and `ContentDigest` in
  `source_version.py`—and split unrelated public classes into their own
  concept-named modules. Private helpers that only serve that concept may remain
  with it; package-wide constants, type aliases, and validation helpers belong
  in a clearly named shared module. Use a capability subpackage when it improves
  discovery. Capability package facades and executable entrypoint facades may
  expose stable contracts; generic layer and concrete-infrastructure package
  initializers should not hide implementation imports. Conventional layer
  package names such as `services`, `repositories`, and `infrastructure` are
  useful only when their ownership is strict and their contents remain
  capability-named. Avoid ambiguous catch-all modules named `common`, `core`,
  `helpers`, `models`, or `utils`. Introduce a port, repository, pattern, or
  other abstraction only when it improves a real boundary, variation point,
  invariant, or test seam.
- Avoid speculative factories, generic CRUD layers, service locators, event
  buses, caches, queues, workers, databases, distributed locks, microservices,
  and agent frameworks.
- Add no dependency when the standard library or an existing dependency solves
  the problem cleanly. Consider maintenance, security, and licensing before any
  addition.
- Write idiomatic modern Python with clear names, explicit behavior, useful type
  hints, cohesive functions, context-managed resources, and no hidden mutable
  global state.
- Give every production function, method, and API endpoint a concise
  Google-style docstring. Explain purpose and contract, and add `Args:`,
  `Returns:`, and `Raises:` sections only when applicable; do not restate the
  signature in prose. Descriptive test names may replace repetitive test
  docstrings unless setup, intent, or failure behavior is non-obvious.
- Use comments for the reason behind non-obvious logic, invariants, constraints,
  or tradeoffs, not to narrate syntax. For genuinely complex multi-stage logic,
  label major stages `Step 1`, `Step 2`, and nested stages `Step 2.A`,
  `Step 2.B` so readers can follow the algorithm and failure boundaries.
- Use async only for beneficial concurrent I/O. Never block an event loop,
  orphan tasks, create unbounded tasks, or ignore cancellation and cleanup.
- Validate untrusted input at boundaries. Enforce authorization server-side and
  prevent injection, path traversal, unsafe deserialization, secret exposure,
  and sensitive-data logging.
- Prefer the repository's established parameter-binding query API. Keep query
  construction, database types, and row mapping inside persistence adapters.
  Handwritten SQL is acceptable when it is clearer or required for a database
  feature, but bind all values, whitelist dynamic identifiers and ordering,
  document the reason, and verify the affected persistence or performance
  boundary. Do not adopt an ORM merely to avoid writing SQL.
- Model errors deliberately. Do not swallow failures, fabricate defaults, turn
  failure into empty success, leak internals through public APIs, or catch broad
  exceptions without a concrete recovery or translation purpose.
- Bound retries, loops, recursion, fan-out, memory growth, and resource use. Add
  timeouts and backoff where external operations warrant them; retry only when
  safe.
- Make multi-step state changes atomic when required. Prefer transactions,
  constraints, atomic updates, idempotency keys, and explicit state transitions
  over timing assumptions or check-then-write logic.
- For concurrent paths, reason about interleavings, duplicate execution, lost
  updates, lock ordering, deadlocks, cancellation, and retry effects.
- Preserve public API, schema, serialization, configuration, CLI, and event
  compatibility unless a breaking change is explicitly required and handled.
- Add observability proportional to operational need. Logs and errors should
  carry useful context without credentials or unnecessary sensitive data.
- Preserve unrelated user changes and keep the patch focused.

## Durable schema evolution

- Let a tracked migration system own every durable production schema change.
  ORM mappings and SQLAlchemy metadata may describe the expected schema and
  support migration comparison, but they must not create, drop, or mutate the
  production schema during application startup.
- Treat autogenerated migrations as reviewable drafts. Inspect names, types,
  nullability, indexes, constraints, server defaults, data movement, and
  downgrade or recovery behavior; write renames and data migrations explicitly
  when inference would be ambiguous.
- Apply migrations as an explicit, observable release operation, normally
  before incompatible application code starts. Do not hide migration execution
  in a web lifespan, worker boot hook, import side effect, or repository
  constructor.
- For non-additive changes, plan deployment compatibility and recovery. Prefer
  expand/backfill/verify/contract sequencing when old and new application
  versions may overlap, and test the tracked revision path on an isolated real
  database appropriate to the change.
- Never use `metadata.drop_all()`, `metadata.create_all()`, or an equivalent
  destructive rebuild as a production migration strategy. Restrict such helpers
  to explicitly disposable test or local environments when they are clearer
  than exercising the real migration path.

## Documentation changes

- Integrate guidance into the existing section that owns the subject. If none
  exists, add a named section beside the closest related material; do not append
  an unrelated note at the beginning or end merely because that is convenient.
- Preserve the document's audience, hierarchy, chronology, and source-of-truth
  role. Put setup in public entry points, accepted design in architecture docs,
  operating procedures in runbooks, and release-visible behavior in changelogs.
- Update rather than duplicate existing guidance. Link to a controlling source
  when another document only needs routing or a short contextual summary.
- Read the surrounding headings and prose after editing so the document still
  flows and planned versus implemented behavior remains accurate.

## Test and verify

- For non-trivial test selection, suite growth, or test-architecture work, read
  [Proportional testing strategy](references/testing-strategy.md).
- Test behavior and contracts, not implementation trivia.
- Admit a permanent test only for a named contract, invariant, failure mode,
  security property, or confirmed regression that existing coverage does not
  already protect at a cheaper layer. Do not target a test count or create tests
  per file, class, method, branch, or DTO field.
- Cover relevant normal, boundary, invalid-input, and failure behavior.
- Add a regression test for a meaningful bug fix unless a concrete reason makes
  it impractical.
- For persistence changes, verify constraints, transactions, migrations, and
  rollback or compatibility concerns as applicable.
- For concurrency-sensitive changes, test idempotency or competing execution at
  the strongest practical boundary.
- Keep live networks and nondeterministic providers out of default tests unless
  the repository explicitly requires them.
- Run the smallest relevant set of formatting, linting, typing, tests, migration
  checks, and documentation checks that gives confidence proportional to risk.
  Fix failures caused by the change and report checks that could not run.

## Final review

Before finishing, privately verify:

- the requirement and error contract are satisfied;
- responsibilities are in the correct layer;
- no simpler sound design was missed;
- security, authorization, and data exposure are safe;
- concurrent or retried execution cannot corrupt or duplicate state;
- partial failure and cleanup are safe;
- time, space, query, network, and lock costs are reasonable;
- tests target the most likely meaningful failures;
- compatibility and migration effects are understood; and
- another experienced engineer can understand why the code exists.

Report what changed, why, what was verified, and any remaining limitation. For
meaningful performance-sensitive work, include time, space, query, or network
costs only when doing so helps future operation or review.
