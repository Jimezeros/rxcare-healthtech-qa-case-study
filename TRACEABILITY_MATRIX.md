# Requirements Traceability Matrix

## Jira UI-oriented test design

These original cases target a future prescription-import user interface. No UI exists in v0.1.0, so their execution status remains unchanged.

| Risk / requirement | Jira Story | Jira test design | Coverage | UI execution | Linked risk |
|---|---|---|---|---|---|
| Missing dosage must be rejected | RXQA-5 | RXQA-6 / TC-01 | Negative — empty value | **Not Executed** | — |
| Whitespace must not bypass validation | RXQA-5 | RXQA-7 / TC-02 | Negative — normalisation | **Not Executed** | RXQA-10 candidate risk |
| Valid dosage must not be falsely rejected | RXQA-5 | RXQA-8 / TC-03 | Positive control | **Not Executed** | — |
| Rejection must create a privacy-safe audit event | RXQA-5 | RXQA-9 / TC-04 | Auditability and privacy | **Not Executed** | — |

## Executable prototype coverage — v0.1.0

| Risk / requirement | Executable case | Automated protection | Execution | Evidence |
|---|---|---|---|---|
| Empty dosage is rejected and absent from canonical storage | API-TC-01 | service and HTTP-handler tests | **Passed** | [API-TC-01](evidence/execution/20260817T185026Z-v0.1.0/api-cases/API-TC-01/) |
| Whitespace-only dosage is normalized as missing | API-TC-02 | pure validation, service, handler, and SQLite constraint tests | **Passed** | [API-TC-02](evidence/execution/20260817T185026Z-v0.1.0/api-cases/API-TC-02/) |
| Valid dosage is accepted and preserved | API-TC-03 | service and handler tests | **Passed** | [API-TC-03](evidence/execution/20260817T185026Z-v0.1.0/api-cases/API-TC-03/) |
| Rejection creates one audit event with approved fields only | API-TC-04 | rejected-outcome and privacy-field allow-list tests | **Passed** | [API-TC-04](evidence/execution/20260817T185026Z-v0.1.0/api-cases/API-TC-04/) |
| Duplicate record ID does not overwrite canonical data | API-TC-05 | service integration test and primary key | **Passed** | [API-TC-05](evidence/execution/20260817T185026Z-v0.1.0/api-cases/API-TC-05/) |

## Interpretation

The executable cases verify one local API/service/database slice. They do not convert the separate UI test designs into executed UI tests. RXQA-10 was not reproduced on v0.1.0 and remains a candidate risk rather than a confirmed defect.
