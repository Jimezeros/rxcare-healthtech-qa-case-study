# Changelog

All notable changes to the RxCare QA portfolio prototype are recorded here.
Historical execution bundles remain immutable and retain the scope, source
fingerprint, test count, and limitations recorded at their creation time.

## [0.2.0] — 2026-08-18

### Added

- A self-contained, dependency-free browser UI for the synthetic prescription
  validation workflow.
- UI-facing canonical-record and privacy-safe audit-event verification panels.
- A non-interactive evidence harness designed to execute UI-TC-01 through
  UI-TC-04 over a genuine ephemeral loopback TCP listener.
- Source/runtime fingerprints, pre/post database counts, direct-SQL/HTTP quality
  comparisons, RXQA-10 status handling, JUnit output, and SHA-256 manifests for
  the Phase 2 evidence workflow.
- Tests for the UI route, end-to-end handler evidence, version consistency,
  exact synthetic UI case catalog, and honest handling of a blocked listener.
- Expanded evidence-publication and synthetic-data policies, including a
  viewport-only screenshot privacy checklist.

### Verified

- The current automated regression suite passes **21/21** tests.
- The v0.2.0 API contract, validation, persistence, SQL quality checks, and
  privacy-safe audit behaviour have in-process automated coverage.
- Final in-process API evidence run `20260817T212310Z-v0.2.0` passed 5/5 API
  cases and 21/21 automated tests; its SHA-256 manifest verifies successfully.

### Execution status

- The UI is implemented in the source tree.
- Live TCP and browser execution are **BLOCKED — NOT EXECUTED** in the current
  restricted sandbox because binding an ephemeral `127.0.0.1` listener is
  denied.
- Run `20260817T212440Z-ui-loopback-v0.2.0` records that constraint without
  claiming a live request, browser interaction, screenshot, SQL result, or new
  RXQA-10 determination.
- A new timestamped run on a workstation that permits loopback binding is still
  required before Phase 2 live-network or browser evidence can be marked PASS.

### Scope boundaries

- No authentication, authorization, deployment, production integration,
  clinical validation, regulatory compliance, medical advice, or AI capability
  is claimed.
- Only procedurally synthetic data is permitted.

## [0.1.0] — 2026-08-17

### Added

- The first executable RXQA-5 validation slice using Python and SQLite.
- Required-field and whitespace-only dosage validation.
- Atomic canonical persistence and privacy-safe validation audit events.
- Parameterized SQL, schema-level dosage protection, and read-only quality views.
- In-process HTTP-handler contract tests and reproducible evidence generation.

### Evidence

- `20260817T185026Z-v0.1.0` is the canonical immutable v0.1.0 evidence baseline.
- Its report states that live TCP and browser execution were not performed.
