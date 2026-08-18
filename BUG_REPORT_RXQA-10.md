# RXQA-10 — Candidate Risk Assessment

## Summary

Whitespace-only dosage could bypass required-field validation if input is not
normalized before the required-field check.

> **Current status:** NOT REPRODUCED IN RXCARE v0.2.0 API/HANDLER TESTS.  
> **Browser UI determination:** BLOCKED — NOT EXECUTED.  
> RXQA-10 remains a candidate risk, not a confirmed defect.

The original Jira item records the risk that `RXQA-7 / UI-TC-02` is designed to
detect. Automated API/handler coverage rejects the value correctly, but this
result is not substituted for genuine browser-to-live-server execution.

## Traceability

- Epic: `RXQA-3 — Medication Safety and Data Validation`
- Story: `RXQA-5 — Reject prescription records with missing dosage instructions`
- Test case: `RXQA-7 / UI-TC-02`
- API equivalent: `API-TC-02`
- Risk priority: High
- Potential severity: High

## Current v0.2.0 environment

- Local synthetic-data prototype
- Build/version: `0.2.0`
- Automated suite: **21/21 Passed**
- Final API evidence run: `20260817T212310Z-v0.2.0`
- API handler contract: Executed in-process
- Live loopback/browser execution: **BLOCKED — NOT EXECUTED**
- Block reason: restricted environment denied the loopback TCP bind

## Synthetic test data

- Record ID: `SYN-UI-TC02-001`
- Patient reference: `SYN-PAT-TC02-001`
- Medication: `Synthetic Medicine B`
- Dosage instruction: exactly three ASCII space characters

## Browser steps

1. Open the local RxCare v0.2.0 validation workspace.
2. Enter all mandatory synthetic values.
3. Enter exactly three spaces in Dosage instruction.
4. Select `Validate and verify` once.
5. Inspect the validation, canonical-record, audit, and safe browser-evidence
   values.

## Expected browser result

1. Safe browser evidence reports `dosage_length: 3` and code points
   `[32, 32, 32]` without retaining dosage text.
2. The service returns HTTP `422`, `REJECTED`, `DOSAGE_REQUIRED`, and exact
   message `Dosage is required` next to the dosage field.
3. Canonical lookup returns `NOT_FOUND`.
4. Exactly one privacy-safe `REJECTED` audit event exists.

## Executed API/handler result — v0.2.0

`API-TC-02` submitted exactly three spaces in `dosage_instruction` through the
in-process HTTP handler.

Observed API result:

1. HTTP `422` returned.
2. Status was `REJECTED`.
3. Reason code was `DOSAGE_REQUIRED`.
4. Exact response message was `Dosage is required`.
5. The canonical-record query returned `404`.
6. Exactly one privacy-safe `REJECTED` audit event was recorded.

Conclusion for the API path: **not reproduced on v0.2.0**.

## Browser UI result — v0.2.0

No live listener, browser request, DOM interaction, or screenshot was executed
because the sandbox denied the loopback bind. The UI result is therefore
**BLOCKED — NOT EXECUTED**, not Passed and not Failed. The blocked run provides
no new evidence for or against RXQA-10 through the browser path.

## Potential impact

Incomplete medication instructions could be stored as valid data, creating a
data-integrity and potential patient-safety risk.

## Evidence

- [v0.2.0 API-TC-02 package](evidence/execution/20260817T212310Z-v0.2.0/api-cases/API-TC-02/)
- [v0.2.0 machine-readable API risk assessment](evidence/execution/20260817T212310Z-v0.2.0/candidate_risk_RXQA-10.json)
- [blocked browser-attempt assessment](evidence/execution/20260817T212440Z-ui-loopback-v0.2.0/candidate_risk_RXQA-10.json)
- [blocked browser-attempt report](evidence/execution/20260817T212440Z-ui-loopback-v0.2.0/TEST_EXECUTION_REPORT.md)

## Historical v0.1.0 result

The same candidate risk was also not reproduced in the earlier API-only
baseline. Its evidence remains available at
[`20260817T185026Z-v0.1.0`](evidence/execution/20260817T185026Z-v0.1.0/).
That result did not include a UI and is not presented as browser evidence.
