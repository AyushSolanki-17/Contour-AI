# Contour Agent Instructions

These instructions apply to the entire repository.

## Engineering skill

For every software-development task, read and apply
`.agents/skills/staff-backend-engineer/SKILL.md` unless the user explicitly
disables it. Scale the workflow and verification depth to the task's actual
risk; do not turn trivial changes into heavyweight exercises.

## Required context

Before backend implementation, read in order:

1. `docs/project-scope.md`;
2. `docs/architecture/backend.md`;
3. `docs/architecture/knowledge-model.md`;
4. `docs/development/roadmap.md`; and
5. `docs/quality/testing.md`.

Use `README.md` for the public summary. The documents above control implementation scope and semantics. If they conflict with code, report the conflict and resolve it explicitly rather than guessing.

## Current objective

Phase 0 is active. Build the smallest complete Python backend path from workspace and supported source through durable ingestion, basic extraction/search, exact evidence, and run inspection. Follow the ordered roadmap unless the task explicitly changes priority.

## Execution workflow

For roadmap-driven work without a more specific user request, use
[`TASKS.md`](TASKS.md) as the bounded execution queue. The roadmap remains the
source of sequencing and scope; the queue contains only the current bounded
slice.

- Claim one `ready` card before implementation and keep its owner, status, and
  handoff current.
- Work on at most one card at a time. Do not start dependent or follow-up work
  without an explicit user or coordinator decision.
- Stop with the card in `review` when its checks pass, or `blocked` with concrete
  evidence when it cannot progress. Do not self-requeue or run unbounded
  improvement loops.
- A human or explicitly assigned reviewer accepts the task, records it in
  `docs/development/task-history.md`, and controls queue refill or reordering.
- An explicit user request may supersede the queue. Do not add it to the queue
  unless the user or coordinator asks for that bookkeeping.

## Repository boundary

- This repository owns Python backend, API, persistence, workers, evaluation, tests, deployment configuration, and implementation-coupled docs.
- Do not add frontend application code; frontend repositories consume versioned API contracts.
- Do not copy private research, business strategy, competitor material, or raw plans from outside this Git worktree.
- Never commit credentials, private datasets, provider payloads, or generated artifacts containing sensitive data.

## Architecture rules

- Keep domain and application code independent of FastAPI, PostgreSQL clients, provider SDKs, and frontend types.
- Routes translate and validate; application services orchestrate; adapters perform infrastructure work.
- PostgreSQL and content-addressed artifacts hold durable state. Do not rely on process memory for job correctness.
- Preserve immutable source versions, exact evidence, provenance, namespaced identity, and explicit unknowns.
- Treat indexes and caches as rebuildable projections.
- Keep vendor-specific and future technology choices behind behavior-focused ports.
- Do not introduce microservices, Kafka, Neo4j, a dedicated vector store, Redis, a warehouse, Rust, or agent frameworks during Phase 0 without an approved scope change and admission evidence.

## Implementation discipline

- Work in small vertical increments that leave a runnable, tested contract.
- Prefer deterministic behavior and the simplest implementation that satisfies the current requirement.
- Give every production function, method, and API endpoint a concise
  Google-style docstring that explains its contract rather than restating its
  name. Document arguments, returns, and raised errors when they are meaningful.
- Use inline comments only for non-obvious intent, constraints, or tradeoffs.
  For a genuinely complex multi-stage algorithm, label the major flow as
  `Step 1`, `Step 2`, and nested stages as `Step 2.A`, `Step 2.B`; do not
  narrate straightforward statements.
- Make retries and duplicate requests explicit and idempotent where required.
- Fail unsupported or invalid states clearly; never fabricate defaults or convert failures into empty success.
- Add migrations for schema changes and tests for migration and persistence invariants.
- Preserve unrelated user changes and avoid speculative abstractions for later phases.

## Verification

Follow `docs/quality/testing.md`. Every permanent test must protect a named
contract, invariant, failure mode, security property, or confirmed regression;
do not create tests per file/class or duplicate the same behavior across layers.
Every bug fix needs the smallest useful regression test. Knowledge-affecting
changes require direct invariant and quality checks in addition to ordinary
software tests. Live networks and models stay out of default test suites.

Before handing work back, run the relevant formatting, linting, typing, tests, migration checks, and documentation/link checks available in the repository. State what was run and any checks that could not run.

## Documentation

Update docs when a contract or accepted architecture changes. Mark planned and implemented behavior accurately. Architecture decisions that add dependencies or alter boundaries must include the requirement, simpler alternative, failure/security implications, migration or removal path, and verification evidence.

Integrate new guidance into the existing section that owns the subject. Create
a nearby named section only when no suitable section exists; do not append
miscellaneous notes to the top or bottom of a document. Preserve each file's
role, hierarchy, chronology, and source-of-truth status, and link to controlling
guidance instead of duplicating it across files.

Keep public entry points and setup instructions in `README.md` accurate. Record
notable behavior under `Unreleased` in `CHANGELOG.md`; do not use the changelog
as a task log.

## Git hygiene

- Make a Conventional Commit only after a cohesive, verified change is ready;
  avoid both speculative micro-commits and unrelated large bundles.
- Stage explicit files, inspect the staged diff, and never commit credentials,
  private datasets, generated environments, local artifacts, or other secrets.
- Run the repository pre-commit checks and the relevant verification suite before
  committing. Do not commit known failing checks without explicit user approval.
