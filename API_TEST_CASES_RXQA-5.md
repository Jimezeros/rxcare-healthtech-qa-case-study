# RXQA-5 — Executed API-contract cases

These cases are separate from the browser UI cases RXQA-6 through RXQA-9. The
v0.2.0 UI is implemented, but live loopback/browser execution was blocked by
the restricted environment. Every UI case therefore remains **BLOCKED — NOT
EXECUTED**; the API results below do not establish a UI PASS.

The API cases exercised the real Python `BaseHTTPRequestHandler` with complete
in-process HTTP/1.1 request and response messages and a fresh temporary SQLite
database. The final API evidence run `20260817T212310Z-v0.2.0` and its
automated suite passed **5/5** API cases and **21/21** tests.

| Case | Input or control | Expected result | API/handler result |
|---|---|---|---|
| API-TC-01 | Empty dosage | HTTP 422; exact error; no canonical row; one rejected audit event | **PASS** |
| API-TC-02 | Three spaces as dosage | HTTP 422 after whitespace normalization; no canonical row; one rejected audit event | **PASS** |
| API-TC-03 | Complete synthetic dosage | HTTP 201; one canonical row; submitted dosage preserved | **PASS** |
| API-TC-04 | Audit event for rejected attempt | Exactly one event; rejected outcome and only approved privacy-safe fields | **PASS** |
| API-TC-05 | Duplicate synthetic record ID | HTTP 409; original canonical value not overwritten | **PASS** |

## v0.2.0 evidence index

- [API-TC-01 request, response, storage check, audit check, and assertions](evidence/execution/20260817T212310Z-v0.2.0/api-cases/API-TC-01/)
- [API-TC-02 request, response, storage check, audit check, and assertions](evidence/execution/20260817T212310Z-v0.2.0/api-cases/API-TC-02/)
- [API-TC-03 request, response, canonical row, and assertions](evidence/execution/20260817T212310Z-v0.2.0/api-cases/API-TC-03/)
- [API-TC-04 sanitized audit response and assertions](evidence/execution/20260817T212310Z-v0.2.0/api-cases/API-TC-04/)
- [API-TC-05 duplicate response, canonical-row check, audit check, and assertions](evidence/execution/20260817T212310Z-v0.2.0/api-cases/API-TC-05/)
- [automated test output](evidence/execution/20260817T212310Z-v0.2.0/automated_test_output.txt)
- [JUnit XML](evidence/execution/20260817T212310Z-v0.2.0/junit.xml)

## Execution qualification

The restricted sprint environment did not permit binding a loopback TCP port.
The listener code and browser UI are implemented, but their live path remains
**BLOCKED — NOT EXECUTED**. No UI case, screenshot, JavaScript execution, or
live-port regression result is inferred from the in-process API result. The
blocked attempt is documented in the
[v0.2.0 loopback execution report](evidence/execution/20260817T212440Z-ui-loopback-v0.2.0/TEST_EXECUTION_REPORT.md).
See [RUNBOOK_GR.md](RUNBOOK_GR.md) for the independent normal-workstation retry.

## Historical v0.1.0 evidence

The earlier verified API baseline remains available at
[`20260817T185026Z-v0.1.0`](evidence/execution/20260817T185026Z-v0.1.0/).
It is preserved as historical API/service/database evidence and is not used to
claim execution of the v0.2.0 browser UI.
