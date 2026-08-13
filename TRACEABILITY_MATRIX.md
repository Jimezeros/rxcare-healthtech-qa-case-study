# Requirements Traceability Matrix

| Risk / requirement | Jira Story | Test case | Coverage | Execution | Linked defect |
|---|---|---|---|---|---|
| Missing dosage must be rejected | RXQA-5 | RXQA-6 / TC-01 | Negative — empty value | Not Executed | — |
| Whitespace must not bypass validation | RXQA-5 | RXQA-7 / TC-02 | Negative — normalisation | Not Executed | RXQA-10 candidate defect |
| Valid dosage must not be falsely rejected | RXQA-5 | RXQA-8 / TC-03 | Positive control | Not Executed | — |
| Rejection must create a privacy-safe audit event | RXQA-5 | RXQA-9 / TC-04 | Auditability and privacy | Not Executed | — |

## Coverage interpretation

The four tests cover the invalid empty partition, a whitespace-bypass variant, a valid positive control, and the audit/privacy consequence of rejection.

Execution results will be added only after a genuine test target exists. Until then, coverage refers to test design rather than verified system behaviour.
