# Contour Engineering Documentation

This directory contains the context needed to build and maintain the Contour backend. Documents distinguish planned behavior from implemented behavior; a plan is never evidence that a feature ships.

## Read first

1. [Project scope](project-scope.md) — product purpose, repository boundary, initial backend scope, and non-goals.
2. [Backend architecture](architecture/backend.md) — controlling Phase 0 topology, module boundaries, data ownership, and service contracts.
3. [Knowledge model](architecture/knowledge-model.md) — semantic objects and invariants that storage and APIs must preserve.
4. [Development roadmap](development/roadmap.md) — ordered backend work and acceptance gates.
5. [Testing standard](quality/testing.md) — verification layers and definition of done.

The [Contour vocabulary and data dictionary](understandings.md) defines the
implementation terms used across those documents and includes concrete examples.

For HTTP-facing changes, also read
[API contract synchronization](development/api-contracts.md).

Before non-trivial implementation, use the
[feature startup and architecture stability protocol](development/feature-startup.md)
to place the change, decide whether an architectural boundary actually needs to
move, and define the bounded verification plan.

Repository-wide instructions for coding agents live in [AGENTS.md](../AGENTS.md).

## Executing the roadmap

The repository-root [active task queue](../TASKS.md) holds a small bounded
working set derived from the roadmap, including dependencies, acceptance checks,
ownership, and handoff fields. Accepted cards move to the
[completed-task log](development/task-history.md), while notable delivered
behavior is recorded in the [changelog](../CHANGELOG.md).

The queue does not override the controlling documents or authorize copying
private planning material into the repository.

## Documentation boundary

Keep implementation scope, current architecture, accepted technical decisions, API and data-model contracts, setup instructions, testing standards, and reproducible evaluation protocols here.

Keep market and competitor research, commercial strategy, raw opportunity analysis, unpublished exploratory notes, and historical superseded plans outside the Git worktree. Private material must not be copied into this repository without an explicit publication review.

When implementation and documentation disagree, treat the discrepancy as work to resolve. Update a document's status or the implementation; do not silently describe planned behavior as current behavior.
