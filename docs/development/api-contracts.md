# API Contract Synchronization

**Status:** required backend/frontend integration procedure
**Updated:** 2026-08-19

## Ownership

FastAPI routes and public Pydantic schemas own the HTTP behavior implemented by
this repository. `openapi/contour.openapi.json` is the generated,
frontend-consumable representation of that behavior. It is checked in so an
independently versioned frontend can pin, review, and generate a client without
importing Python internals.

The generated artifact describes implemented behavior, not roadmap intent. The
current contract exposes liveness and readiness plus trusted-local `PUT` and
`GET` operations for canonical workspace identifiers and nested logical-source
identifiers under `/api/v1`. It does not publish listing, ingestion, progress,
authentication, or authorization behavior.

Request validation uses HTTP 400 and the common error envelope with safe
field-level details. Missing resources use 404, immutable identity conflicts use
409, unsupported source configurations use 422, and unavailable required
storage uses 503. An exact repeated `PUT` returns the same accepted resource.
Cross-workspace source reads return the same not-found representation as an
unknown source.

## Generate and verify

After an intentional public route or schema change, regenerate the artifact:

```shell
make openapi
```

Verify that the checked-in artifact matches the application:

```shell
make openapi-check
```

`make quality` includes the drift check. Do not edit the JSON manually or copy
private planning material into its descriptions.

## Compatibility

Prefer additive changes. Before a breaking change, define the compatibility or
versioning boundary and coordinate backend, frontend, and integration tasks.
Review affected paths, request and response schemas, status codes, stable error
envelopes, authentication, validation, pagination, idempotency, and progress
semantics as applicable.

Frontend mocks and generated clients must pin a reviewed artifact. Roadmap
descriptions do not authorize a frontend to invent paths, fields, or errors.
