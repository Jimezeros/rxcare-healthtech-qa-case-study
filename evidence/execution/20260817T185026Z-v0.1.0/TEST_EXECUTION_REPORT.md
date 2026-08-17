# RxCare v0.1.0 — Execution report

## Result

**PASS** for the first executable RXQA-5 vertical slice.

- Run ID: `20260817T185026Z-v0.1.0`
- UTC execution time: `2026-08-17T18:50:26Z`
- Runtime: `3.9.6` on `macOS-26.5.2-arm64-arm-64bit`
- Data: synthetic identifiers and fictional medication data only
- Database: fresh temporary SQLite database, removed after sanitized export

## Executed API-contract cases

| Case | Purpose | Result |
|---|---|---|
| API-TC-01 | Empty dosage is rejected | PASS |
| API-TC-02 | Whitespace-only dosage is rejected | PASS |
| API-TC-03 | Valid dosage is persisted | PASS |
| API-TC-04 | Rejected audit event is privacy-safe | PASS |
| API-TC-05 | Duplicate record ID is rejected | PASS |

The cases above exercised the real Python HTTP handler with complete HTTP/1.1
request and response framing inside the process. The sandbox blocked opening a
local TCP listener, so a live-port smoke test was **not executed in this run**.
The runbook contains the command for that separate workstation check.

## Automated verification

The standard-library automated suite was executed from a clean temporary
database. Its human-readable output is in `automated_test_output.txt`; the
machine-readable result is in `junit.xml`.

## RXQA-10 status

The whitespace-only dosage risk was **not reproduced on v0.1.0**:
`API-TC-02` returned HTTP 422, created no canonical prescription row, and
created one privacy-safe `REJECTED` audit event. RXQA-10 remains a candidate
risk, not a confirmed defect.

## Scope boundary

The existing Jira UI-oriented manual cases RXQA-6 through RXQA-9 remain
`Not Executed`. This run executed separate API-contract and automated cases
linked to RXQA-5. It does not demonstrate a user interface, deployment,
clinical validation, regulatory compliance, authentication, AI capability,
or production readiness.
