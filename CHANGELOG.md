# Changelog

Notable changes to Contour are recorded here. Entries describe user-visible,
operator-visible, or developer-facing behavior; task bookkeeping and ordinary
refactors belong in the task history and Git history instead.

The format follows Keep a Changelog conventions. Until the first release, new
entries remain under `Unreleased`. A release moves them under a version and ISO
date without rewriting what was actually delivered.

## Unreleased

### Added

- A bounded repository-native task queue with explicit ownership, acceptance,
  review, archival, and human/agent handoff rules.
- Installable Python 3.14 backend package foundation with a locked development
  environment and deterministic format, lint, type, and test commands.
- Local pinned PostgreSQL Compose runtime with a loopback-only listener,
  persistent development volume, readiness probe, and documented reset flow.
- GitHub Actions quality gate for locked Python checks, documentation links, and
  repository-history secret scanning with Gitleaks.
