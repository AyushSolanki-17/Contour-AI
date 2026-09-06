# Mapping Layer-First Projects to Contour

**Status:** developer orientation; the [backend architecture](../architecture/backend.md)
remains the controlling design

Developers familiar with a global `services/`, `repositories/`, and
`resources/` layout will find the same responsibilities in Contour. Contour
groups them by business capability first, so the code for Sources, Tenancy, and
Workspaces stays discoverable without mixing unrelated business areas.

## Responsibility mapping

| Layer-first layout | Contour owner | Example |
|---|---|---|
| HTTP resources/controllers | `api/routers/` | `api/routers/v1/sources.py` |
| Request and response DTOs | `api/schemas/` | `api/schemas/v1/sources.py` |
| Business services | `<capability>/application/` | `sources/application/collections.py` |
| Repository interfaces | `<capability>/application/ports.py` | `sources/application/ports.py` |
| Repository implementations | `infrastructure/postgres/` | `infrastructure/postgres/source_repository.py` |
| Domain models | `<capability>/domain/` | `sources/domain/source.py` |
| Dependency-injection bootstrap | `composition/<executable>.py` | `composition/http.py` |

## Request flow

```text
HTTP request
  -> API router
  -> capability application service
  -> capability port
  -> PostgreSQL or other infrastructure adapter
  -> domain result
  -> HTTP response
```

For source collection operations, the concrete path is:

```text
api/routers/v1/sources.py
  -> SourceCollectionService in sources/application/collections.py
  -> SourceTransactionManager and SourceRepository contracts in application/ports.py
  -> PostgreSQL source transaction and repository adapters
```

## Application-package convention

The capability directory supplies the business subject. Application module names
therefore state the operation family rather than repeating it:

| Module | Owns |
|---|---|
| `collections.py` | Create/list use cases in a `*CollectionService`. |
| `access.py` | Scope and permission verification in a `*AccessService`. |
| `persistence.py` | Durable multi-step admission or recording in a `*PersistenceService`. |
| `ports.py` | Behavior-focused repository and transaction protocols. |

Business logic belongs in these application services. Ports state what durable
or external work is needed; infrastructure adapters implement that work without
owning business policy. Do not introduce one generic `services.py` file merely
to mirror a layer-first layout: distinct use cases remain separate when they
have different reasons to change.

## Cross-capability workflows

`workflows/` is reserved for an operation that coordinates multiple
capabilities. For example, `workflows/source_admission.py` can coordinate
workspace, source, source-version, and evidence behavior. It stays outside the
`sources` application package because no single capability owns the entire
transaction.
