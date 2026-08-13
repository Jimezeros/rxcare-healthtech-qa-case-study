# Project Methodology

## 1. Product concept

RxCare is a fictional web application for medication-profile management and synthetic e-prescription quality validation. The case study focuses on data integrity, patient-safety awareness, privacy, auditability, and clear system behaviour.

## 2. QA workflow

The portfolio follows this evidence chain:

`Risk -> Requirement -> Epic -> Story -> Acceptance Criteria -> Test Case -> Execution Evidence -> Defect -> Retest`

Each artifact must answer:

1. Why does this control exist?
2. Which requirement or risk does it cover?
3. What input and behaviour are being tested?
4. What observable result is expected?
5. What genuine evidence exists?

## 3. Risk-based testing

Test effort is prioritised according to potential impact:

- incomplete or inconsistent medication information;
- duplicate or conflicting records;
- unauthorised access or excessive data exposure;
- missing audit events;
- misleading AI-generated health explanations;
- unclear validation and escalation messages.

## 4. Test-design techniques

The portfolio applies:

- equivalence partitioning for valid and invalid inputs;
- boundary-value analysis where numerical or length limits exist;
- negative testing for missing, malformed, or prohibited values;
- positive controls to detect false rejection;
- state and workflow checks;
- requirements-based and risk-based coverage;
- privacy and audit-log inspection.

## 5. Definition of evidence

A designed test remains **Not Executed** until it is run against an approved testable target. Execution evidence must record the build or version, environment, date, observable result, and privacy-safe screenshot or log reference.

A candidate defect becomes a confirmed defect only after genuine reproduction. The actual result must never be inferred or fabricated.

## 6. Data protection

All examples use synthetic identifiers and fictional medication records. Screenshots must be checked for email addresses, account identifiers, browser tabs, private URLs, avatars, and other unnecessary personal information before publication.
