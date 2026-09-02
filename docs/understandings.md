# Contour Vocabulary and Data Dictionary

**Status:** living implementation glossary
**Updated:** 2026-08-30

This document defines Contour terms as they are used in code, schema, and
contracts. Update the existing entry when a term's meaning changes, and add a
new entry when implementation introduces a new durable concept. Planned terms
are explicitly marked; they do not describe shipped behavior.

## Catalog and evidence

| Term | Meaning in Contour | Example |
|---|---|---|
| **Domain** *(planned boundary)* | A namespaced vocabulary, mapping, policy, and evaluation boundary for one bounded problem. It extends generic Contour semantics without replacing them. | A release-context Domain registers release and work-item kinds while retaining generic Entity and Evidence contracts. |
| **Connector** *(planned boundary)* | A capability-scoped adapter through which configured Sources can be observed. Connector capability, permission, time, and failure semantics are explicit. | One document Connector can observe several configured documentation Sources without making the document vendor a core type. |
| **Workspace** | An isolated admission scope that owns sources and the knowledge later derived from them. It has a stable namespaced identity. | `WORKSPACE:python-maintainers` holds PEP material for one maintainer team. |
| **Source** | A logical, stable origin with ownership and admission metadata. A source is not its newest fetched content. | `SOURCE:PEP:723` represents the PEP 723 publication location. |
| **Source version** | One immutable observation of a source's exact admitted bytes. Its identity combines the source and the SHA-256 content digest. | `SOURCE:PEP:723@sha256:…` identifies one specific body of PEP 723 text. |
| **Content digest** | The canonical SHA-256 hash of the exact admitted source bytes. It is content identity, not a “latest” label. | `sha256:ab12…` changes when the admitted bytes change. |
| **Evidence** | A durable, inspectable pointer into exactly one immutable source version. Evidence is the basis for later credited entities and relationships. | `EVIDENCE:pep-723-replaces` points to PEP 723's `Replaces` header. |
| **Evidence locator** | The exact location inside a source version: a semantic locator plus, when available, a half-open byte span. | `header:Replaces`, bytes `[10, 23)`. |
| **Catalog** | The durable set of workspaces, sources, source versions, and evidence records. It is the authoritative admission record, not a search index. | A catalog admission stores a workspace, PEP source, exact PEP version, and header evidence atomically. |
| **Tenant** | The top-level durable data owner and security boundary. It is not a Workspace label or a client-selected filter. | Every Workspace belongs to exactly one Tenant. |
| **Principal** | A provider-neutral authenticated subject. | A configured demo credential may resolve to a Principal without making that credential a domain type. |
| **Membership** | The verified grant that lets a Principal operate inside one Tenant. | Listing Tenants returns only those for which the Principal has Membership. |
| **Access Context** | The transport-neutral Principal, Tenant, Membership, and request correlation scope required by product services. | A guessed foreign Workspace ID receives the same inaccessible outcome as an unknown ID. |
| **Catalog admission** | The service use case that accepts one internally consistent workspace/source/version/evidence set in a single transaction. | If evidence references a different source version, admission fails before writing. |
| **Reference Profile** *(planned package)* | A removable acquisition manifest, source mapping, cutoff, checksum set, fixture, and experience example used to prove generic behavior on a real corpus. It is not a maintained Connector or core schema. | A bounded public release profile maps source-native records into generic Source, Entity, Event, Relationship, and Evidence kinds. |

## Knowledge and execution

| Term | Meaning in Contour | Example |
|---|---|---|
| **Entity** | A namespaced thing known from evidence; it is not an unqualified assertion of truth. | `PEP:723` with evidence identifying the proposal. |
| **Relationship** | An evidence-backed typed edge between entities. Every credited relationship retains its own evidence. | `PEP:723 --replaces--> PEP:722`, supported by `header:Replaces`. |
| **Job** | One durable request for work, independent from any individual attempt to perform it. | “Ingest this supported PEP source” is one job. |
| **Run** *(planned persistence)* | One observable attempt to execute a job, with its own lifecycle, outputs, and failure information. | A retry after a worker crash is a new run of the same ingestion job. |

## Time, boundaries, and runtime roles

| Term | Meaning in Contour | Example |
|---|---|---|
| **Unknown time** | A deliberate absence of a temporal value. Contour never substitutes ingestion time for it. | A source with no publisher date stores `source_time = unknown`. |
| **Source time** | When the publisher says a document or event occurred. | The date shown by the PEP publisher. |
| **Revision time** | The time associated with an upstream revision. | A Git revision timestamp, if the source provides one. |
| **Domain object** | Framework-independent value or entity that enforces Contour meaning and invariants. | `EvidenceLocator` rejects a span with no end offset. |
| **Service** | Transport-neutral orchestration for a use case. It expresses business workflow and transaction intent, but never SQL or HTTP behavior. | `services/catalog_service.py` validates the chain then asks repository ports to persist it atomically. |
| **Repository port** | A behavior-focused interface used by a service. It shields core logic from a database or storage product. | `repositories/evidence.py` defines `EvidenceRepository.save_evidence(...)`; PostgreSQL implements it today. |
| **Infrastructure implementation** | An implementation of a port for a concrete technology. It contains connection, query, and row-mapping details. | `infrastructure/postgres/evidence_repository.py` maps `EvidenceLocator` to the `evidence` table. |
| **Unit of work** | A short-lived transaction boundary that gives multiple repositories one atomic commit or rollback. | Catalog admission writes its four records through repositories bound to one PostgreSQL connection. |
| **Composition root** | The executable edge that creates process resources and supplies dependencies explicitly. Core code never looks them up globally. | `composition/http.py` creates the pooled PostgreSQL engine, readiness implementation, and health service, then gives FastAPI a shutdown lifespan. |
| **Delivery adapter / controller** | The outer protocol-specific layer. HTTP routes, future CLI commands, and future MCP tools validate and translate their protocol, then call the same service. | A future FastAPI route and a CLI command can both invoke `CatalogAdmissionService`; neither embeds its business rules. |

## Working rule

Use these terms consistently in code, migration names, logs, API schemas, and
tests. If a new term would overlap an existing one, first decide whether it is
the same concept at another boundary or a genuinely new domain concept; avoid
synonyms that obscure provenance and transaction semantics.
