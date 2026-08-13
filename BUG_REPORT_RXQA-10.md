# RXQA-10 — Candidate Defect Report

## Summary

Whitespace-only dosage may bypass required-field validation.

> **Status:** PORTFOLIO PRACTICE — NOT YET EXECUTED AGAINST A WORKING APPLICATION.

This report documents the defect that `RXQA-7 / TC-02` is designed to detect. It is not represented as an observed production defect.

## Traceability

- Epic: `RXQA-3 — Medication Safety and Data Validation`
- Story: `RXQA-5 — Reject prescription records with missing dosage instructions`
- Test case: `RXQA-7 / TC-02`
- Priority: High
- Potential severity: High

## Environment

- Planned QA environment / synthetic RxCare prototype
- Browser: to be recorded during execution
- Build/version: to be recorded during execution

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

## Candidate actual result

The record may be accepted if validation counts whitespace as a non-empty value.

## Potential impact

Incomplete medication instructions could be stored as valid data, creating a data-integrity and potential patient-safety risk.

## Reproducibility and evidence

To be confirmed during genuine execution. No screenshot, timestamp, browser, or build evidence is claimed yet.
