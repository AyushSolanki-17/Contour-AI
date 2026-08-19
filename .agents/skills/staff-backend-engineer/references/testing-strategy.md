# Proportional Testing Strategy

Read this reference when deciding whether to add tests, changing a test suite,
or reviewing test volume and layering. Repository-specific testing standards
remain authoritative.

## Admission gate

A permanent test needs a named reason to exist: an observable contract, domain
or knowledge invariant, security property, failure mode, compatibility promise,
or confirmed regression. Do not use test count, line coverage, branch count, or
one-test-per-production-unit conventions as goals.

Before writing a test:

1. State what realistic regression it detects and what externally meaningful
   behavior would fail.
2. Search existing tests for the same failure signal.
3. Extend or parameterize existing coverage when it remains more readable than
   another case.
4. Select the cheapest layer with sufficient fidelity.
5. Avoid repeating the same assertion at multiple layers unless each layer
   protects a distinct integration contract.

Do not test private call order, trivial field assignment, constant values,
framework or standard-library behavior, generated boilerplate, or mocks that
merely restate the implementation. A new class, file, DTO, route, or branch does
not automatically justify another test.

## Layer choice

- Unit/property: deterministic domain behavior, algorithms, state transitions,
  parsing, identities, and boundary-value spaces.
- Contract: public HTTP/CLI/MCP schemas, error mapping, compatibility, and
  authorization observable by a client.
- Integration: repository constraints, transactions, migrations, adapters, and
  failure behavior that doubles cannot prove.
- End-to-end: a small number of critical user journeys crossing the assembled
  system; do not reproduce all lower-level edge cases.
- Evaluation/benchmark: extraction, retrieval, ranking, generation quality, or
  operational performance where ordinary pass/fail tests are insufficient.

Prefer one representative success path and one case for each materially
different failure class. Parameterize equivalent input boundaries. Use direct
invariant tests for security, concurrency, irreversible data changes, and
knowledge correctness even when a broader path also touches them.

## Maintenance budget

Keep fixtures local and small until genuine reuse makes a shared fixture
clearer. Avoid broad mocks and snapshots that make harmless refactors rewrite
large portions of the suite. Default tests should remain deterministic,
service-free where practical, and fast enough to run routinely.

During review, consolidate or remove tests whose contract disappeared, whose
signal is fully subsumed, or whose runtime/flakiness/maintenance cost is higher
than the risk they protect. Preserve a regression test while its defect can
realistically recur; tests are safeguards, not a historical archive.
