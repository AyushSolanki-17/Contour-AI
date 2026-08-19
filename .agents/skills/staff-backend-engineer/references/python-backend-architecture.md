# Python Backend Architecture

Read this reference when creating or materially restructuring a Python backend,
API boundary, persistence path, dependency graph, or alternate delivery adapter.
Adapt names to the repository's established vocabulary; architecture is about
dependency direction and ownership, not a mandatory directory template.

## Default shape

Prefer a modular monolith with ports-and-adapters boundaries until independent
deployment is required by measured operational needs.

```text
delivery adapter -> application use case -> port -> infrastructure adapter
                         |
                         v
                   domain behavior
```

- Domain code owns entities, value objects, policies, and invariants. It does
  not import the web framework, ORM, database driver, provider SDK, or delivery
  schema.
- Application code owns use-case orchestration, transaction intent, commands,
  queries, results, and behavior-focused ports. It depends inward on domain
  semantics and not outward on transport or infrastructure.
- Delivery adapters own HTTP routers/controllers, CLI commands, MCP tools,
  worker handlers, validation, serialization, authentication extraction, and
  error/status translation.
- Infrastructure adapters implement application ports for databases, artifact
  stores, queues, source systems, and providers.
- A composition root imports concrete adapters and constructs the executable
  object graph. Keep it thin and separate from business behavior.

Group code by capability within these boundaries as the capability grows.
Avoid both a flat collection of unrelated files and empty architectural folders
created for hypothetical needs. A cohesive small use case can remain one
module; split it when commands, queries, ports, policies, or tests have distinct
reasons to change.

## Package and distribution boundary

For one product and deployment unit, prefer one top-level import namespace under
`src`, with delivery adapters as subpackages such as `product.api`,
`product.cli`, and `product.mcp`. `src` is a packaging layout root, not an
architectural layer. Avoid generic top-level packages such as `api` or `core`:
they obscure ownership and commonly become catch-alls.

Create another top-level package or Python distribution only for a demonstrated
independent reuse, versioning, ownership, dependency, or deployment boundary.
When that boundary exists, give it explicit project metadata and a declared
public contract rather than simulating separation with another directory.

## Controllers, services, and repositories

Treat an HTTP route/router as a controller: validate and translate input, invoke
one application use case, and translate the result. Do not put business rules,
raw SQL, transaction policy, or provider calls in it. A JSON API does not need a
server-rendered `views` layer.

An application service represents a use case, not a miscellaneous place for all
logic. Put entity-local invariants in the domain object and cross-component
workflow/transaction decisions in the application service. Avoid services that
only rename calls to generic repositories unless the boundary adds policy,
translation, or orchestration.

Define repository ports around domain/use-case behavior and expected
consistency. Prefer `get_workspace`, `add_immutable_version`, or
`find_admitted_documents` over a universal `BaseRepository[T].create/read/update/delete`.
Keep SQL, ORM query types, eager-loading strategy, and row mapping inside the
persistence adapter. Make query count and atomicity explicit for important use
cases.

Use a unit-of-work or transaction port when one use case must atomically change
multiple repositories. The application layer decides the transaction boundary;
the adapter owns driver-specific commit, rollback, isolation, and cleanup.

## Keep model roles distinct

Do not use one "model" class for every boundary just because fields overlap:

- Domain models are framework-independent typed objects that enforce domain
  meaning and valid state transitions.
- Application commands, queries, and results are transport-neutral typed values
  or dataclasses shaped for a use case.
- Pydantic request/response models belong at an untrusted API or configuration
  boundary and define validation, serialization, and OpenAPI behavior.
- ORM/table models belong to the persistence adapter and define storage mapping.
- Provider payload models belong to that provider adapter.

Translate explicitly where semantics or trust changes. Sharing a small immutable
value object is appropriate only when its meaning and constraints are genuinely
identical. Do not make domain objects inherit Pydantic or ORM base classes for
serialization convenience.

## Dependency injection and resource scopes

Dependency injection is the act of supplying dependencies, not necessarily a
container package. Default to constructor/function injection plus an explicit
composition root because the graph remains visible, type-checkable, and easy to
replace in tests.

Choose lifetime deliberately:

- Process scope: immutable settings, stateless services, thread-safe clients,
  and connection pools when the client documents safe sharing.
- Request/command/job scope: authorization context, correlation metadata,
  database session, unit of work, and transaction.
- Operation scope: cursors, streams, temporary files, and other short-lived
  context-managed resources.

Use an application lifespan or context manager to create and close process
resources. Inject a factory when a consumer needs a fresh scoped object. Never
make a database session or mutable request context a singleton. Do not hide
dependencies behind module globals or let application/domain code query a
container or service locator.

Framework dependency features are useful for delivery-specific request values
and scopes; they should adapt to, not construct policy inside, the core. Consider
a third-party DI container only after the real graph demonstrates enough scoped,
conditional, or plugin-driven wiring to improve on explicit composition.
Evaluate startup failure behavior, async cleanup, override/test ergonomics,
typing, framework coupling, maintenance cost, and removal path. Needing one
singleton is not sufficient evidence.

## Multiple delivery adapters

HTTP, CLI, MCP, workers, scheduled jobs, and tests should be peer adapters over
the same application contracts. Each adapter may have different schemas,
streaming, status/error representation, and authorization extraction. None
should call another adapter or reach directly into its Pydantic/ORM models.

Before calling a use case from a second adapter, verify that its input/output
and errors contain no HTTP assumptions. Move reusable orchestration inward;
leave presentation, protocol metadata, and resource lifecycle at the edge.

## Enforcement

For meaningful boundary work, add the lightest executable check that prevents
the likely regression: import-direction tests, API contract tests, repository
integration tests, transaction/failure tests, or an end-to-end path. Do not rely
on directory names alone to preserve the architecture, but do not add a
permanent architecture test before there is a realistic dependency regression
for it to catch.
