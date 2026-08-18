# RxCare v0.2.0 — Execution report

## Result

**PASS** for the first executable RXQA-5 vertical slice.

- Run ID: `20260817T212310Z-v0.2.0`
- UTC execution time: `2026-08-17T21:23:10Z`
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

The whitespace-only dosage risk was **not reproduced on v0.2.0**:
`API-TC-02` returned HTTP 422, created no canonical prescription row, and
created one privacy-safe `REJECTED` audit event. RXQA-10 remains a candidate
risk, not a confirmed defect.

## Scope boundary

The Jira UI-oriented cases RXQA-6 through RXQA-9 remain `Not Executed` in
this run. Version v0.2.0 includes a local browser UI, but the restricted
execution environment blocked opening a loopback TCP listener. This run
therefore demonstrates the handler/service/database contract, not live browser
execution. It does not demonstrate deployment, clinical validation, regulatory
compliance, authentication, AI capability, or production readiness.
