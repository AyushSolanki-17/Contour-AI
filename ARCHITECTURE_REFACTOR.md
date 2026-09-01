# Contour — Production-Grade Architecture Refactor

You are refactoring the `contour` Python codebase into a **production-grade, enterprise-scale architecture suitable for a large engineering team**.

This is not a cosmetic folder cleanup.

The objective is to establish a codebase with:

- strong module cohesion
- clear ownership
- explicit dependency direction
- well-defined domain boundaries
- application/use-case boundaries
- infrastructure isolation
- thin delivery adapters
- excellent testability
- predictable project navigation
- low accidental complexity
- long-term maintainability
- room for multiple interfaces such as HTTP, CLI, workers, and scheduled jobs

Do **not** interpret "enterprise" as "more abstractions."

Do **not** introduce complexity merely to make the architecture look sophisticated.

The desired result should be **boring, obvious, rigorous, and scalable**.

## Execution tracking

This tracker records verification of the existing modular-monolith implementation
and the cohesive cleanup that removes its superseded vocabulary. A checked item
has evidence in the responsibility map, source tree, or named verification
command below; it is not a statement of future intent.

- [x] 1. Core architectural principle — delivery adapters depend on services;
      services depend on domain values and capability-specific ports.
- [x] 2. No framework-shaped rewrite — the accepted conventional package
      boundaries remain the one architecture.
- [x] 3. Repository inventory — governing docs, configuration, migrations,
      OpenAPI, source tree, and architecture/contract/integration tests were
      inspected.
- [x] 4. Responsibility map — recorded in the inventory result below.
- [ ] 5. Module cohesion — catalog collections and PostgreSQL table/transaction
      modules still contain independently changing capability responsibilities.
- [x] 6. No junk drawers — the executable architecture check rejects ambiguous
      production module and package names.
- [x] 7. Business capabilities are discoverable through capability-named
      modules within the accepted boundaries.
- [x] 8. No global feature-folder proliferation — `services/`,
      `repositories/`, and `infrastructure/` retain strict ownership.
- [x] 9. Domain remains framework and infrastructure independent.
- [ ] 10. Services own transport-neutral use-case orchestration — split the
      remaining multi-capability catalog collection service.
- [x] 11. Ports exist only for durable persistence, artifacts, and transaction
      seams used by services.
- [x] 12. Infrastructure owns concrete PostgreSQL, filesystem, source, and
      credential implementations.
- [ ] 13. PostgreSQL implementations have one obvious owner under
      `infrastructure/postgres/`, but knowledge and execution table/transaction
      ownership still needs separation.
- [x] 14. `application/` and `services/` no longer form competing vocabularies.
- [x] 15. Repository contracts are distinct from infrastructure implementations.
- [ ] 16. HTTP routes are thin delivery adapters over services — move shared
      bearer-authentication extraction out of the catalog router.
- [x] 17. Pydantic schemas remain under `api/schemas/`.
- [ ] 18. Domain, application, infrastructure, and delivery errors have
      explicit translation boundaries — split the remaining combined
      knowledge/execution record errors.
- [ ] 19. Service-selected transaction boundaries and PostgreSQL-owned commit,
      rollback, and driver-error translation remain explicit — split the broad
      concrete record unit of work into its narrow capability views.
- [ ] 20. `settings.py` is the sole environment-reading configuration boundary
      — define a dedicated cursor-signing secret rather than reuse the database
      password.
- [x] 21. `bootstrap/http.py` is the explicit HTTP composition root.
- [x] 22. Architecture, unit, contract, and PostgreSQL integration suites are
      organized by the boundary they protect.
- [x] 23. The default suite and OpenAPI drift check preserve the published
      behavior during this structural cleanup.
- [x] 24. Obsolete product, generic-record, legacy `application/`, and
      `adapters/` paths have no remaining source-tree implementation.
- [x] 25. Repository hygiene rules and ignore entries cover generated runtime
      artifacts.
- [ ] 26. Capability and infrastructure module names now use one vocabulary —
      separate execution from the `knowledge` table module and generic `record`
      transaction/error names.
- [x] 27. Cohesion rather than file count governed the changes.
- [x] 28. No generic factory, manager, bus, container, or CRUD hierarchy was
      introduced.
- [x] 29. The resulting boundaries support independent delivery, persistence,
      and business-rule changes.
- [x] 30. The work proceeded as inventory, target confirmation, cohesive
      cleanup, and verification rather than a blind rewrite.
- [x] 31. PostgreSQL integration and migration verification — the local Compose
      database passed the selected suite and reports no metadata drift at head.
- [x] 32. Architecture documentation describes the resulting code and placement
      rules.
- [x] 33. The final navigation questions are answered in the responsibility map.
- [ ] 34. Final quality bar — default, PostgreSQL integration, migration, API,
      architecture, documentation, and pre-commit checks pass, pending the
      remaining cohesion and configuration corrections above.
- [x] 35. The batch is stable under the available deterministic checks.

---

# 1. Core architectural principle

`contour` is the actual application and core package.

HTTP is only one delivery mechanism.

A future CLI, worker, background job, scheduler, or another interface should be able to invoke the same application capabilities without depending on HTTP.

Conceptually:

```text
                         DELIVERY
              ┌────────────┼────────────┐
              │            │            │
             HTTP         CLI         Worker
              │            │            │
              └────────────┼────────────┘
                           │
                           ▼
                    APPLICATION
                  use cases/workflows
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
                  DOMAIN        PORTS
               business rules   contracts
                    │             ▲
                    │             │
                    └──────┬──────┘
                           │
                           ▼
                    INFRASTRUCTURE
              PostgreSQL / filesystem /
               external integrations

```

The exact package layout may differ if the existing code reveals a better structure.

This diagram expresses **dependency direction**, not a requirement that every request must pass through every box.

---

# 2. Do NOT blindly impose a framework architecture

Do not simply create:

```text
controllers/
services/
repositories/
models/
utils/
helpers/
factories/
managers/

```

because that is a familiar enterprise pattern.

Do not blindly apply textbook Clean Architecture, Hexagonal Architecture, Onion Architecture, DDD, CQRS, or any other methodology.

Use architectural principles, not architectural fashion.

The existing business domain should determine the boundaries.

---

# 3. First task: understand the existing system

Before changing code, inspect the entire relevant repository.

Read:

- [`AGENTS.md`](http://AGENTS.md)
- [`README.md`](http://README.md)
- [`TASKS.md`](http://TASKS.md)
- `pyproject.toml`
- `Makefile`
- architecture documentation
- development documentation
- testing documentation
- existing architecture tests
- all Python files under `src/contour`
- relevant tests
- migrations
- API/OpenAPI definitions

Understand:

- domain concepts
- application workflows
- persistence model
- PostgreSQL boundaries
- external integrations
- artifact storage
- API behavior
- configuration
- bootstrap
- transaction management
- tenant isolation
- access control
- idempotency
- error handling
- current dependency graph

Do not make architectural decisions based only on filenames.

Inspect the implementation.

---

# 4. Create an internal responsibility map

Before refactoring, determine for every meaningful module:

```text
module
→ responsibility
→ dependencies
→ consumers
→ business capability
→ proposed final location

```

Identify:

- modules with multiple unrelated responsibilities
- modules that are cohesive but large
- duplicate abstractions
- redundant layers
- dead code
- compatibility wrappers
- misplaced business logic
- infrastructure leaking into domain/application
- API logic leaking into application/domain
- persistence logic leaking outside infrastructure
- concepts split across too many tiny files
- concepts incorrectly combined into large files

Do not use line count as the primary criterion.

## Inventory result

The following map is the implementation baseline used for this refactor. It
groups modules only where they have the same capability, dependencies, and
consumers; it does not create a second package layout.

| Capability | Domain ownership | Service and port ownership | Concrete implementation | Delivery and consumers | Transaction boundary |
|---|---|---|---|---|---|
| Access and tenancy | `domain/access.py`, `domain/tenant.py`, `domain/workspace.py` | `services/access_service.py`, catalog ports for principal, membership, tenant, and workspace | PostgreSQL access, tenant, and workspace repositories | Catalog routes and all tenant-scoped services | Catalog unit of work |
| Catalog collections | `domain/source.py` | `services/catalog_collections.py`, catalog and idempotency ports | PostgreSQL catalog transaction and source/idempotency repositories | `api/routes/catalog.py`, `api/schemas/catalog.py`, HTTP bootstrap | Catalog unit of work |
| Immutable source admission | `domain/acquired_content.py`, `domain/source_version.py`, `domain/evidence.py` | `services/source_persistence.py`, `services/catalog_service.py`, artifact/source-version/evidence ports | Filesystem artifact store, PostgreSQL catalog repositories, PEP source adapter | Worker/CLI-ready service contract; current PEP tests | Artifact write followed by catalog unit of work |
| Knowledge records | `domain/entity.py`, `domain/relationship.py` | `services/knowledge_persistence.py`, knowledge transaction and record ports | PostgreSQL record transaction with entity and relationship repositories | Integration tests; future worker and API | Knowledge transaction view |
| Execution records | `domain/job.py`, `domain/run.py` | `services/execution_persistence.py`, execution transaction and record ports | PostgreSQL record transaction with job and run repositories | Integration tests; future worker and API | Execution transaction view |
| Health and runtime | no durable business model | `services/health_service.py` and readiness port | PostgreSQL readiness probe | Health route, HTTP app, and bootstrap | none |
| Process configuration and observability | no business policy | no service dependency | `settings.py`, `observability/logging.py` | `bootstrap/http.py` only for construction and lifecycle | process lifecycle |

The only discovered duplicate architecture vocabulary was the empty legacy
`application/` and `adapters/` skeleton. It was removed. The former generic
product and records service/route/port names were already consolidated into
catalog, knowledge, execution, and delivery-specific authentication modules;
searches confirm no production caller retains those superseded paths. The
shared PostgreSQL record transaction remains intentional: it owns one cohesive
connection/rollback/error-translation mechanism while exposing separate narrow
knowledge and execution transaction views to services.

---

# 5. Module cohesion is mandatory

A file should contain **meaningfully related content**.

The standard is not:

> one class = one file

and not:

> one file must be under N lines

Instead:

> A module should have one strong conceptual purpose and a small, understandable public surface.

Split a file when it contains multiple meaningful responsibilities or independent reasons to change.

Do NOT split a file merely because it is large.

Keep related code together when separating it would create meaningless fragmentation.

For example, this can be good:

```text
sources/
    source.py

```

if it contains a cohesive source domain concept.

This can be bad:

```text
sources/
    source_model.py
    source_validator.py
    source_factory.py
    source_builder.py
    source_types.py
    source_constants.py

```

when those pieces have no meaningful independent identity.

---

# 6. Avoid meaningless "junk drawer" modules

Avoid creating or preserving generic modules such as:

```text
utils.py
helpers.py
common.py
misc.py
manager.py
base.py
shared.py
constants.py
types.py

```

unless their contents form a genuinely coherent concept.

Prefer domain-specific names.

Bad:

```python
utils.validate_source(...)

```

Better:

```python
sources.validation.validate_source(...)

```

if validation is actually a meaningful source-domain concept.

---

# 7. Organize around business capabilities

Where the existing domain supports it, organize around meaningful business capabilities/bounded contexts.

Potential examples include:

```text
catalog
sources
knowledge
workspaces
tenancy
access
records
execution

```

Do not blindly use these names.

Determine the actual boundaries from the codebase.

A developer should be able to answer:

> "Where does source registration live?"

without searching five architectural layers.

---

# 8. Prefer feature cohesion over global layer proliferation

Do not automatically structure the entire project as:

```text
domain/
application/
repositories/
services/
adapters/
infrastructure/
api/

```

if that causes every feature to be scattered across the entire tree.

Where useful, prefer a structure conceptually similar to:

```text
contour/
├── catalog/
│   ├── domain/
│   ├── application/
│   └── ...
│
├── sources/
│   ├── domain/
│   ├── application/
│   └── ...
│
├── workspaces/
│   ├── domain/
│   ├── application/
│   └── ...
│
├── tenancy/
│   ├── domain/
│   └── application/
│
├── knowledge/
│   ├── domain/
│   └── application/
│
├── interfaces/
│   ├── http/
│   └── cli/
│
├── infrastructure/
│   └── postgres/
│
├── bootstrap/
│
└── observability/

```

However, do NOT force this exact structure.

Use the structure that best represents the actual domain.

---

# 9. Domain layer

The domain contains business concepts and business invariants.

Domain code must not depend on:

- FastAPI
- Starlette
- HTTP
- PostgreSQL
- SQLAlchemy/asyncpg/psycopg implementation details
- filesystem implementations
- environment variables
- application bootstrap
- concrete infrastructure repositories

The domain should not be shaped purely around database tables.

Keep actual business behavior with the business concept that owns it.

Use:

- entities
- value objects
- domain policies
- domain services
- domain errors

only where they represent real concepts.

Do not introduce DDD patterns for decoration.

---

# 10. Application layer

The application layer represents meaningful use cases and workflows.

It owns:

- orchestration
- application-level decisions
- use-case sequencing
- transaction boundaries where appropriate
- coordination of domain behavior
- calls through infrastructure ports/contracts

It must not contain:

- HTTP request handling
- HTTP response construction
- SQL queries
- PostgreSQL implementation details
- framework-specific delivery logic

Avoid giant classes such as:

```text
CatalogService
ProductService
WorkspaceService

```

that eventually become dumping grounds for the entire application.

But also do not create one file/class for every trivial CRUD operation.

Use cohesive use cases based on actual complexity.

---

# 11. Ports and interfaces

Use interfaces/ports when they provide a meaningful architectural boundary.

Examples:

- persistence
- artifact storage
- external source acquisition
- transaction abstraction
- clock/time source
- external services

Do NOT create interfaces merely because "enterprise architecture requires interfaces."

Do not create:

```text
IFoo
    ↓
Foo

```

when there is no meaningful substitution, boundary, or testing value.

Prefer a small number of strong contracts over dozens of ceremonial interfaces.

---

# 12. Infrastructure

Infrastructure owns implementation details.

Examples:

```text
PostgreSQL
filesystem
external source clients
artifact storage
database connections
transactions
persistence implementations

```

Infrastructure implementations should implement the contracts required by the application/domain.

Do not let infrastructure concerns leak into business logic.

---

# 13. PostgreSQL organization

The current project contains overlapping concepts such as:

```text
adapters/
infrastructure/
repositories/
postgres/
catalog_postgres.py
postgres_catalog.py
postgres_source.py
*_repository.py

```

Resolve this duplication.

There should be one obvious place where PostgreSQL implementations live.

A reasonable conceptual structure is:

```text
infrastructure/
└── postgres/
    ├── repositories/
    │   ├── catalog.py
    │   ├── sources.py
    │   ├── workspaces.py
    │   └── ...
    ├── tables/
    ├── transactions/
    └── database.py

```

Adapt this to the real system.

Do not split database operations into meaningless files such as:

```text
source_insert.py
source_select.py
source_update.py
source_delete.py

```

unless there is an unusually strong reason.

---

# 14. Resolve `services` vs `application`

The existing project has both:

```text
application/
services/

```

Determine whether these represent different architectural responsibilities.

If not, consolidate them.

Do not preserve duplicate architectural vocabularies.

A service should not simply forward to another service.

A repository should not simply forward to another repository.

An adapter should not simply wrap another adapter without a meaningful boundary.

Remove accidental indirection.

---

# 15. Resolve `repositories` vs `infrastructure`

Determine which repository files are:

1. contracts/ports
2. concrete persistence implementations

Separate those concepts clearly.

The application should depend on the contract.

The concrete PostgreSQL implementation belongs in infrastructure.

Do not maintain multiple repository implementations of the same responsibility unless they are genuinely required.

---

# 16. API is a delivery adapter

HTTP/API must remain thin.

Routes should primarily:

1. parse/validate input
2. resolve dependencies
3. invoke an application use case
4. map the result to an HTTP response
5. translate application/domain errors into HTTP semantics

Business workflows must not live in routes.

The application must not require an HTTP request to execute.

A future CLI should be able to invoke the same use case.

Conceptually:

```text
HTTP ──────┐
           ├──> Application
CLI ───────┤
           │
Worker ────┘

```

not:

```text
CLI → HTTP → Application

```

---

# 17. API schemas are delivery models

Do not leak API/Pydantic/HTTP schemas into the domain merely for convenience.

HTTP request/response models belong to the delivery boundary.

Translate between API representations and application/domain representations when necessary.

Avoid excessive DTO mapping where the types are genuinely identical and the boundary does not benefit from it.

Use judgment.

---

# 18. Errors

Establish clear error ownership.

Errors should conceptually belong to:

```text
domain
application
infrastructure
delivery/API

```

Do not have domain exceptions inherit from HTTP exceptions.

Do not scatter arbitrary:

```text
*_error.py
*_errors.py

```

modules throughout the tree.

Consolidate related errors where appropriate.

Error translation should happen at architectural boundaries.

---

# 19. Transactions

Transactions are an architectural concern and must have explicit ownership.

Inspect the existing:

```text
catalog transactions
records transactions
database transactions

```

and determine whether these abstractions are genuinely necessary.

Avoid hidden transaction behavior.

Ensure application workflows have clear transaction boundaries.

Do not let individual repository methods accidentally define inconsistent transaction semantics if the workflow requires atomicity.

Preserve existing correctness around:

- tenant isolation
- idempotency
- consistency
- atomic operations

---

# 20. Configuration

Establish one clear configuration boundary.

Avoid arbitrary modules reading environment variables directly.

Separate, where useful:

```text
configuration definition
configuration loading
application bootstrap

```

Do not maintain redundant [`config.py`](http://config.py), [`settings.py`](http://settings.py), environment helpers, and bootstrap configuration layers unless each has a clear responsibility.

---

# 21. Bootstrap / composition root

Dependency construction should happen in bootstrap/composition-root code.

Bootstrap may assemble:

```text
configuration
database
repositories
external integrations
application use cases
HTTP application
CLI

```

Application/domain modules should not construct concrete infrastructure dependencies themselves.

Avoid hidden global service locators.

---

# 22. Tests must follow architecture

Refactor tests so they represent actual architectural boundaries.

A reasonable conceptual structure is:

```text
tests/
├── unit/
│   ├── domain/
│   └── application/
├── integration/
│   ├── postgres/
│   └── external_sources/
├── contract/
│   └── api/
└── architecture/

```

Adapt it to the final architecture.

Architecture tests should enforce real dependency rules.

For example:

```text
domain
  ✗ infrastructure
  ✗ HTTP/API

application
  ✗ HTTP/API
  ✗ concrete PostgreSQL implementation

delivery/API
  ✓ application

infrastructure
  ✓ implements application/domain contracts

```

Do not weaken architecture tests just to make the refactor pass.

---

# 23. Preserve behavior

This is primarily a structural refactor.

Preserve existing behavior including:

- API contract
- OpenAPI contract
- persistence semantics
- migrations
- tenant isolation
- access control
- idempotency
- source acquisition
- artifact behavior
- error semantics
- configuration behavior
- transaction behavior

Do not introduce unrelated product changes.

If an existing design prevents proper architectural separation, make the smallest necessary change and document it.

---

# 24. Remove duplicate and obsolete code

The final architecture must not contain two competing architectures.

Do not leave:

```text
old services/
new application/
old repositories/
new repositories/
compatibility wrappers everywhere

```

after the refactor.

When code has been replaced:

- update all callers
- remove the old implementation
- remove obsolete exports
- remove dead imports
- remove compatibility wrappers when no longer necessary
- remove empty directories/packages

The final tree should tell one coherent story.

---

# 25. Generated files and repository hygiene

Do not keep generated runtime artifacts in source control.

Remove/ignore:

```text
__pycache__/
*.pyc
venv/
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/

```

as appropriate for the repository.

Ensure `.gitignore` is correct.

Do not treat generated artifacts as architecture.

---

# 26. Naming consistency

Use one consistent naming convention.

Avoid inconsistent patterns such as:

```text
catalog_postgres.py
postgres_catalog.py
postgres_source.py
source_repository.py

```

Choose naming based on package ownership.

Prefer names that tell a developer what responsibility the module owns.

Avoid generic names where a domain-specific name is possible.

---

# 27. Do not optimize for file count

The objective is NOT:

```text
fewer files

```

and NOT:

```text
more files

```

The objective is:

```text
high cohesion
low coupling
clear ownership

```

A 500-line cohesive module may be perfectly acceptable.

A 100-line module containing five unrelated responsibilities is not.

A 20-line module may be correct if it represents an important architectural boundary.

A 5-line module may be unnecessary fragmentation.

Use engineering judgment.

---

# 28. Do not optimize for layer count

The objective is NOT:

```text
maximum layers

```

and NOT:

```text
minimum layers

```

For every boundary, ask:

> What architectural problem does this boundary solve?

If the answer is unclear, remove it.

Do not introduce:

- generic factories
- abstract factories
- service locators
- generic managers
- command buses
- mediator layers
- event buses
- CQRS
- unnecessary unit-of-work abstractions
- dependency injection frameworks
- excessive DTOs
- generic repositories

unless the existing system has a concrete requirement for them.

---

# 29. Enterprise engineering standards

The final architecture should optimize for the concerns that matter in a serious production system:

### Maintainability

A new engineer should understand where functionality belongs without studying the entire repository.

### Independent change

Changing PostgreSQL implementation should not require changing business rules.

Changing HTTP should not require changing application logic.

Changing a business rule should not require touching API infrastructure unnecessarily.

### Testability

Business behavior should be testable without PostgreSQL or HTTP.

### Reliability

Transactions, idempotency, tenant isolation, and error handling must have explicit ownership.

### Extensibility

Adding another delivery mechanism should not require duplicating business logic.

### Observability

Logging/observability should remain outside domain logic wherever practical.

### Operational clarity

Bootstrap and infrastructure configuration should have obvious ownership.

### Team scalability

Multiple engineers should be able to work on different capabilities without constantly modifying giant central modules.

---

# 30. Refactoring process

Perform the refactor incrementally.

## Phase 1 — Inventory

Inspect the codebase and establish the actual architecture.

Do not modify files yet.

## Phase 2 — Target architecture

Define:

```text
business capability
→ domain ownership
→ application ownership
→ infrastructure ownership
→ delivery ownership

```

## Phase 3 — Foundations

Fix:

- dependency direction
- configuration
- bootstrap
- duplicate abstractions
- repository boundaries
- infrastructure boundaries

## Phase 4 — Feature refactoring

Refactor one cohesive capability at a time.

For each capability:

```text
inspect
→ move
→ split/merge where justified
→ update imports
→ update tests
→ run tests
→ run architecture checks

```

## Phase 5 — Delivery adapters

Make HTTP/API thin.

Prepare the architecture for a future CLI without implementing speculative CLI functionality.

## Phase 6 — Cleanup

Remove obsolete:

- services
- repositories
- adapters
- wrappers
- dead code
- empty packages
- duplicate implementations

## Phase 7 — Documentation

Update architecture documentation to describe the architecture that actually exists.

---

# 31. Verification after every meaningful refactor

Use the project's actual tooling from:

- [`AGENTS.md`](http://AGENTS.md)
- `pyproject.toml`
- `Makefile`

Run appropriate:

```text
tests
lint
format
type checking
architecture tests
integration tests
OpenAPI checks

```

At minimum, ensure:

```text
pytest

```

passes unless the repository specifies a different test command.

Verify:

- package imports
- application startup
- API startup
- OpenAPI generation
- migrations
- PostgreSQL integration
- tenant isolation
- idempotency
- architecture tests

Do not solve failures by weakening tests or adding unnecessary compatibility layers.

---

# 32. Documentation requirement

Update architecture documentation to explain:

1. `contour` as the core application
2. domain ownership
3. application/use-case ownership
4. infrastructure ownership
5. API as a delivery adapter
6. future CLI as another delivery adapter
7. dependency direction
8. transaction ownership
9. persistence boundaries
10. error boundaries
11. bootstrap/composition
12. where developers should put new functionality

Documentation must describe the actual resulting code.

---

# 33. Final architectural test

Before declaring completion, pretend you are a senior engineer joining this project today.

You should be able to answer immediately:

```text
Where are business rules?

Where are use cases?

Where is PostgreSQL?

Where are external integrations?

Where are HTTP routes?

Where would CLI code live?

Where are persistence contracts?

Where are persistence implementations?

Where are transactions?

Where are domain errors?

Where are application errors?

Where is dependency wiring?

Where do I add a new business capability?

```

If the answer requires following excessive indirection, simplify.

If unrelated responsibilities are mixed together, split them.

If the same concept exists in multiple architectural locations, consolidate it.

---

# 34. Final quality bar

The final Contour architecture should feel:

- cohesive
- obvious
- boring
- disciplined
- production-ready
- scalable to a large codebase
- scalable to a large engineering team
- easy to test
- easy to reason about
- difficult to accidentally misuse

It should NOT feel:

- over-engineered
- framework-driven
- ceremony-heavy
- fragmented
- full of generic abstractions
- dependent on HTTP
- dependent on PostgreSQL
- organized purely around technical class types

The goal is not to demonstrate architectural knowledge.

The goal is to create a codebase where **the architecture makes the correct thing easy and the incorrect dependency difficult**.

---

# 35. Important execution rule

Do not attempt a massive blind rewrite.

Make changes in coherent, verifiable batches.

After each batch:

1. inspect the diff
2. run relevant tests
3. run architecture checks
4. fix imports/dependencies
5. verify behavior
6. continue only when the previous step is stable

Do not stop after merely moving files.

The refactor is complete only when the implementation, tests, imports, architecture checks, and documentation all agree with the new architecture.

Start by inspecting the repository thoroughly and determining the actual responsibility/dependency map before making structural changes.
