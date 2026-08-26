# Knowledge Model

**Status:** controlling semantic model; physical schema remains an implementation decision
**Updated:** 2026-08-19

## Separation of concerns

Contour separates what a thing is, what a source says about it, and why the system believes a derived record. Collapsing these layers makes updates destructive and turns extraction confidence into false certainty.

## Phase 0 objects

- **Workspace:** the scope, settings, ownership context, and admitted capabilities for related work.
- **Source:** a stable logical origin with a namespaced identifier, canonical locator, source type, scope, license, and data classification. It does not contain mutable “latest text.”
- **Source version:** an immutable observed source state with content hash, retrieval/observation time, source revision metadata where known, and bytes or a content-addressed pointer.
- **Evidence:** an exact inspectable locator and span or structured field inside one source version.
- **Entity:** a namespaced thing with identity across mentions and revisions. Aliases are observations, not automatic merges.
- **Relationship:** a typed connection between entities with one or more evidence attachments and temporal scope where known. A relationship does not imply causality or material impact.
- **Job:** durable requested work with queueing, retry, cancellation, and terminal state.
- **Run:** one execution attempt with inputs, code/configuration identity, stages, outputs, metrics, failures, and artifacts.

Claims, events, investigations, findings, dispositions, decisions, and detailed temporal intervals are compatible extensions, but should not become Phase 0 product behavior unless a concrete use case requires them.

## Identity

1. Prefer identifiers owned by the source domain, such as `PEP:723`.
2. Namespace every identifier.
3. Preserve original mentions when normalizing presentation.
4. Keep possible duplicates as candidates until evidence or a deterministic rule resolves them.
5. Record merge and split decisions as reversible events; never silently merge.

### Phase 0 source identity representation

The initial domain values keep source identifiers as an uppercase namespace and
a source-owned local value (for example, `SOURCE:PEP:723`). A source version is
identified by that source identifier and the SHA-256 digest of the exact bytes
admitted to Contour, serialized as `SOURCE:PEP:723@sha256:<digest>`. Upstream
revision metadata is retained separately because it can be absent or change in
format; it does not replace the content identity.

Evidence locators always carry this source-version identity. They can identify
a structured field (such as `header:Replaces`) and, when byte offsets are
available, a non-empty half-open byte span. Phase 0 applies no byte
canonicalization before raw persistence: the digest is SHA-256 over the exact
admitted bytes and is also the content-addressed artifact reference. The
filesystem implementation maps it to
`sha256/<first-two-hex-characters>/<remaining-hex-characters>` beneath its
configured root; other implementations must preserve the same digest contract.
The manifest retains the first accepted observation time. Seeing the same
content again returns that immutable version rather than overwriting when it was
first observed.

## Evidence and provenance

The minimum inspectable chain is:

```text
entity or relationship
  -> extraction assertion
  -> exact evidence locator
  -> immutable source version
  -> canonical source and revision
  -> ingestion run and extractor version
```

Provenance must survive normalization, chunking, extraction, deduplication, indexing, retrieval, and API serialization.

## Time

Do not model all time as one timestamp:

- **source time:** when the publisher says a document or event occurred;
- **valid time:** when a claim is understood to hold in the represented world;
- **transaction time:** when Contour observed or stored it; and
- **revision time:** the source-control or upstream revision timestamp.

Unknown time remains unknown. “Latest” is a query result, never an overwritten record. When validity intervals are introduced, use half-open intervals `[valid_from, valid_to)` and allow open bounds.

## Confidence and epistemic state

Keep extraction confidence, entity-linking confidence, relationship classification confidence, source authority, evidence sufficiency, and contradiction state separate. Do not average them into one opaque truth score.

Observed evidence, extracted assertions, derived findings, hypotheses, and human decisions must remain distinguishable in storage and API representations.

## Example

```yaml
source:
  id: SOURCE:PEP:723
  canonical_url: https://peps.python.org/pep-0723/

version:
  id: SOURCE:PEP:723@<revision>
  content_hash: sha256:<digest>

evidence:
  source_version: SOURCE:PEP:723@<revision>
  locator: "header:Replaces"
  text: "Replaces: 722"

relationship:
  from: PEP:723
  type: replaces
  to: PEP:722
  evidence: <evidence-id>
  extraction_method: pep_header_parser@<version>
```

## Blocking invariants

- No evidence exists without exactly one immutable source version.
- No credited entity assertion or relationship exists without evidence or a complete `derived_from` chain.
- Immutable source content and prior assertion sets are never rewritten as “latest.”
- Content identity uses a documented digest and canonicalization policy.
- Identifiers are namespaced and stable for the same admitted input.
- Entity merges require an explicit reversible decision.
- Relationship paths retain edge-level evidence.
- Unknown temporal values are not fabricated.
- A citation refers to the same source version and locator used to derive or retrieve the result.
- Derived indexes and artifacts can be rebuilt from immutable inputs and a locked manifest.
- Graph topology is never used as a substitute for temporal validity, authority, or sufficient evidence.
