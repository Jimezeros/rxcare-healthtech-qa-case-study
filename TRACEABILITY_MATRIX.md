# Requirements Traceability Matrix

## Browser UI coverage — v0.2.0

The local single-page UI and its integration hooks are implemented. Genuine
browser-to-live-server execution was attempted, but the restricted sprint
environment denied the required loopback TCP bind. The four Jira-oriented UI
cases therefore remain **BLOCKED — NOT EXECUTED**; implementation and automated
contract coverage are not substituted for browser execution.

| Risk / requirement | Jira Story | Browser case | Coverage | UI execution | Linked risk |
|---|---|---|---|---|---|
| Missing dosage must be rejected and exact field error displayed | RXQA-5 | RXQA-6 / UI-TC-01 | Negative — empty value | **BLOCKED — NOT EXECUTED** | — |
| Three spaces must not bypass validation | RXQA-5 | RXQA-7 / UI-TC-02 | Negative — normalisation | **BLOCKED — NOT EXECUTED** | RXQA-10 candidate risk |
| Valid dosage must not be falsely rejected | RXQA-5 | RXQA-8 / UI-TC-03 | Positive control | **BLOCKED — NOT EXECUTED** | — |
| Rejection must create a visible, privacy-safe audit event | RXQA-5 | RXQA-9 / UI-TC-04 | Auditability and privacy | **BLOCKED — NOT EXECUTED** | — |

Blocked-attempt evidence: [v0.2.0 loopback execution report](evidence/execution/20260817T212440Z-ui-loopback-v0.2.0/TEST_EXECUTION_REPORT.md).

## Executable API/service/database coverage — v0.2.0

The final API evidence run `20260817T212310Z-v0.2.0` passed **5/5** cases and
the current automated suite passed **21/21** tests. The table below reports
API/handler coverage only. It does not establish a browser UI result.

| Risk / requirement | Executable case | Automated protection | API/handler result | Evidence |
|---|---|---|---|---|
| Empty dosage is rejected and absent from canonical storage | API-TC-01 | service and HTTP-handler tests | **Passed** | [API-TC-01](evidence/execution/20260817T212310Z-v0.2.0/api-cases/API-TC-01/) |
| Whitespace-only dosage is normalized as missing | API-TC-02 | pure validation, service, handler, and SQLite constraint tests | **Passed** | [API-TC-02](evidence/execution/20260817T212310Z-v0.2.0/api-cases/API-TC-02/) |
| Valid dosage is accepted and preserved | API-TC-03 | service and handler tests | **Passed** | [API-TC-03](evidence/execution/20260817T212310Z-v0.2.0/api-cases/API-TC-03/) |
| Rejection creates one audit event with approved fields only | API-TC-04 | rejected-outcome and privacy-field allow-list tests | **Passed** | [API-TC-04](evidence/execution/20260817T212310Z-v0.2.0/api-cases/API-TC-04/) |
| Duplicate record ID does not overwrite canonical data | API-TC-05 | service integration test and primary key | **Passed** | [API-TC-05](evidence/execution/20260817T212310Z-v0.2.0/api-cases/API-TC-05/) |

## RXQA-10 interpretation

RXQA-10 was **not reproduced in the v0.2.0 API/handler tests**. Its browser UI
determination remains **BLOCKED — NOT EXECUTED** because no live loopback
request, DOM interaction, or screenshot was completed. It therefore remains a
candidate risk rather than a confirmed UI defect.

## Historical v0.1.0 baseline

The earlier v0.1.0 API/service/database evidence remains available and is not
recast as UI evidence: [verified run `20260817T185026Z-v0.1.0`](evidence/execution/20260817T185026Z-v0.1.0/).
