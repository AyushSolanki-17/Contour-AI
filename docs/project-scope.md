# Project Scope

**Status:** controlling product and repository scope
**Updated:** 2026-08-30

## Purpose

Contour is an open-source, evidence-backed knowledge and investigation platform for complex, evolving domains. It preserves source history, exact evidence, entities, relationships, provenance, and uncertainty so a human or software client can inspect what is known, why it is believed, and how it changed.

Contour is not a generic chat assistant and does not treat model output, graph reachability, or the newest source version as truth by default.

## Initial user and reference data

The first concrete user is an engineering maintainer working with evolving
proposals and guidance. A bounded history of Python Enhancement Proposals
(PEPs) remains the smallest offline conformance input because it is public,
versioned, understandable, and contains deterministic identifiers and
relationships. The first real product-demonstration input is a bounded public
software-organization release profile spanning real project, documentation,
release, incident, security, and disclosure sources.

Both inputs are replaceable workloads, not product dependencies or ecosystem
commitments. PEP-specific and example-organization-specific identity,
validation, formats, and parsing belong in source adapters, acquisition
manifests, fixtures, and provenance. Reusable domain objects, application
services, persistence contracts, and public HTTP schemas remain source-neutral.

The first complete backend job is:

```text
authenticate Principal and select/create accessible Tenant
  -> create Workspace inside that Tenant
  -> register and validate a supported source
  -> ingest an immutable source version
  -> extract basic entities and relationships
  -> index the admitted content
  -> search for an entity or topic
  -> resolve every derived record to exact evidence and its run
```

## Repository ownership

This repository owns:

- the Python domain, service, repository-port, and infrastructure packages;
- FastAPI endpoints and versioned API contracts;
- PostgreSQL schema, migrations, repositories, and initial full-text search;
- source adapters, ingestion, normalization, and deterministic extraction;
- durable background-job and run behavior;
- content-addressed artifact interfaces;
- evaluation, fixtures, tests, benchmarks, and command-line automation;
- backend observability, policy boundaries, and deployment configuration; and
- technical documentation coupled to this implementation.

This repository does not own frontend application code. Frontends consume the API from separate repositories. It also excludes private business strategy, market and competitor research, and raw planning notes.

## Phase 0 backend scope

Phase 0 establishes a usable source-to-evidence backend:

- provider-neutral Principal verification, minimal Membership, and
  non-enumerating Tenant isolation;
- Tenant creation/lookup plus Workspace creation/lookup inside an accessible
  Tenant;
- one small credential-free conformance source plus a bounded real Reference
  Profile admitted through declared Connector capabilities;
- preflight source validation;
- durable acquisition, normalization, extraction, and indexing jobs;
- immutable source versions and exact evidence locators;
- basic namespaced entities and evidence-backed relationships;
- PostgreSQL lexical search over admitted content and entities;
- source, entity, relationship, evidence, job, and run APIs;
- retry, cancellation, idempotency, and worker-crash recovery;
- safe configuration, secret redaction, structured errors, and minimal telemetry; and
- deterministic local fixtures, migrations, CI checks, and reproducible startup.

Every durable and derived record is owned by exactly one Tenant through its
Workspace. That scope must survive repository queries, relationship/evidence
links, jobs/runs, cursors, idempotency, indexes, artifacts, logs, and errors.
Phase 0 proves this with two Principals and two Tenants. It does not include
invitations, membership administration, SSO/SCIM, custom roles, ABAC, billing,
or enterprise governance.

## Product guarantees

- History is never silently overwritten; current state is derived from immutable observations.
- Every credited result resolves to exact evidence or an explicit derivation chain.
- Unknown time stays unknown; ingestion time is not substituted for source or valid time.
- Missing search evidence means “not found in admitted sources,” not “false.”
- Model output is untrusted until schema-validated and never becomes authoritative by default.
- Entity merges are explicit, evidence-backed, and reversible.
- Serving indexes are rebuildable projections, not the only copy of authoritative state.
- Advanced infrastructure or AI must beat a simpler reference on a declared workload before admission.
- A client Tenant selector never authorizes access; verified Membership does,
  and foreign identifiers do not reveal whether data exists.

## Phase 0 non-goals

- frontend implementation;
- microservices, Kubernetes, or distributed ingestion;
- Kafka, Neo4j, a dedicated vector database, or a data warehouse;
- agent frameworks or autonomous decision-making;
- Rust extensions;
- broad enterprise RBAC/ABAC;
- arbitrary source and provider support; and
- security certification or regulatory-compliance claims.

Later phases may introduce these only when the roadmap supplies a real product workload and an adoption gate.
