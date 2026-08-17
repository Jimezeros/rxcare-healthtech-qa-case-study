# RXQA-10 — Candidate Risk Assessment

## Summary

Whitespace-only dosage could bypass required-field validation if the input is not normalized before the required-field check.

> **Current status:** NOT REPRODUCED ON RXCARE v0.1.0 — NOT A CONFIRMED DEFECT.

The original Jira item documents the risk that `RXQA-7 / TC-02` was designed to detect. It was not an observed production defect. The first executable API variant has now been run, and the risk did not reproduce.

## Traceability

- Epic: `RXQA-3 — Medication Safety and Data Validation`
- Story: `RXQA-5 — Reject prescription records with missing dosage instructions`
- Test case: `RXQA-7 / TC-02`
- Risk priority: High
- Potential severity: High

## Environment

- Local synthetic-data prototype
- Build/version: `0.1.0`
- Evidence run: `20260817T185026Z-v0.1.0`
- UI/browser execution: Not Executed
- API handler contract: Executed in-process

## Synthetic test data

- Record ID: `SYN-RX-002`
- Medication: `Metformin 850 mg`
- Dosage instruction: three space characters
- Other mandatory fields: valid synthetic values

## Steps to reproduce

1. Open the prescription import form.
2. Enter all mandatory synthetic values.
3. Enter three spaces in Dosage instruction.
4. Submit the record.

## Expected result

The input is trimmed, treated as empty, and rejected. `Dosage is required` is displayed, the record is not stored as valid, and a privacy-safe rejection audit event is created.

## Original candidate result

The record might be accepted if validation counted whitespace as a non-empty value. This was a hypothesis to test, not an observed result.

## Executed API result — v0.1.0

`API-TC-02` submitted three spaces in `dosage_instruction`.

Observed result:

1. HTTP 422 returned.
2. Status was `REJECTED`.
3. Reason code was `DOSAGE_REQUIRED`.
4. Exact message was `Dosage is required`.
5. The canonical-record query returned 404.
6. Exactly one privacy-safe `REJECTED` audit event was recorded.

Conclusion: **not reproduced on v0.1.0**.

## Potential impact

Incomplete medication instructions could be stored as valid data, creating a data-integrity and potential patient-safety risk.

## Evidence

- [API-TC-02 request and response package](evidence/execution/20260817T185026Z-v0.1.0/api-cases/API-TC-02/)
- [Machine-readable risk assessment](evidence/execution/20260817T185026Z-v0.1.0/candidate_risk_RXQA-10.json)
- [Full execution report](evidence/execution/20260817T185026Z-v0.1.0/TEST_EXECUTION_REPORT.md)

The original UI steps remain unexecuted because v0.1.0 has no UI. A future UI implementation should still execute RXQA-7 independently.
