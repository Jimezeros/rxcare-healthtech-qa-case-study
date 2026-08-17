# RXQA-5 — Executed API-contract cases

These cases are separate from the Jira UI-oriented cases RXQA-6 through RXQA-9. The UI cases remain **Not Executed**. The cases below were executed against the Python HTTP handler and a fresh temporary SQLite database in run [`20260817T185026Z-v0.1.0`](evidence/execution/20260817T185026Z-v0.1.0/).

| Case | Input or control | Expected result | Result |
|---|---|---|---|
| API-TC-01 | Empty dosage | HTTP 422; exact error; no canonical row; one rejected audit event | **PASS** |
| API-TC-02 | Three spaces as dosage | HTTP 422 after whitespace normalization; no canonical row; one rejected audit event | **PASS** |
| API-TC-03 | Complete synthetic dosage | HTTP 201; one canonical row; submitted dosage preserved | **PASS** |
| API-TC-04 | Audit event for rejected attempt | Exactly one event; rejected outcome and only approved privacy-safe fields | **PASS** |
| API-TC-05 | Duplicate synthetic record ID | HTTP 409; original canonical value not overwritten | **PASS** |

## Evidence index

- [API-TC-01 request, response, storage check, audit check, and assertions](evidence/execution/20260817T185026Z-v0.1.0/api-cases/API-TC-01/)
- [API-TC-02 request, response, storage check, audit check, and assertions](evidence/execution/20260817T185026Z-v0.1.0/api-cases/API-TC-02/)
- [API-TC-03 request, response, canonical row, and assertions](evidence/execution/20260817T185026Z-v0.1.0/api-cases/API-TC-03/)
- [API-TC-04 sanitized audit response and assertions](evidence/execution/20260817T185026Z-v0.1.0/api-cases/API-TC-04/)
- [API-TC-05 duplicate response, canonical-row check, audit check, and assertions](evidence/execution/20260817T185026Z-v0.1.0/api-cases/API-TC-05/)

## Execution qualification

The restricted sprint environment did not permit binding a local TCP port. The run therefore exercised the real `BaseHTTPRequestHandler` using complete in-process HTTP/1.1 request and response messages. The listener code is implemented but its live-port smoke test remains **Not Executed** in this evidence run. See [RUNBOOK_GR.md](RUNBOOK_GR.md) for the local command.
