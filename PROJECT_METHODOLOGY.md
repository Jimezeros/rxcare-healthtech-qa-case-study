# Project Methodology

## 1. Product concept and current increment

RxCare is a fictional medication-management and synthetic e-prescription quality application. Version `0.2.0` is not a complete HealthTech product: it is one local browser/HTTP/Python/SQLite validation slice for dosage completeness. The case study focuses on data integrity, patient-safety awareness, privacy, auditability, and evidence-backed system behaviour.

## 2. QA workflow

The portfolio follows this evidence chain:

`Risk -> Requirement -> Epic -> Story -> Acceptance Criteria -> Test Case -> Execution Evidence -> Defect decision -> Retest when needed`

Each artifact must answer:

1. Why does this control exist?
2. Which requirement or risk does it cover?
3. What input and behaviour are being tested?
4. What observable result is expected?
5. What genuine evidence exists?

## 3. Risk-based backlog

The broader backlog is prioritised according to potential impact:

- incomplete or inconsistent medication information;
- duplicate records;
- unauthorised access or excessive data exposure;
- missing audit events;
- misleading AI-generated health explanations;
- unclear validation and escalation messages.

Only dosage completeness, duplicate-record protection, minimum audit exposure, and a local synthetic-data browser workspace are implemented in v0.2.0. The other items remain planned.

## 4. Test-design techniques

The current executable slice applies:

- equivalence partitioning for valid and invalid inputs;
- negative testing for missing, malformed, or prohibited values;
- positive controls to detect false rejection;
- requirements-based and risk-based coverage;
- privacy and audit-log inspection.

Boundary-value analysis, wider state/workflow testing, authentication/RBAC checks, and AI-content evaluation remain planned rather than demonstrated.

## 5. Definition of evidence

A designed test remains **Not Executed** until it is run against an approved testable target. Execution evidence must record the build or version, environment, date, observable result, and privacy-safe screenshot or log reference.

A candidate defect becomes a confirmed defect only after genuine reproduction. The actual result must never be inferred or fabricated.

The API evidence follows that rule: whitespace-only dosage was rejected, so RXQA-10 is recorded as `Not reproduced through the v0.2.0 API/handler path`, not converted into a confirmed defect. The separate browser reproduction remains `Blocked — Not Executed` because the restricted environment denied a loopback listener.

## 6. Data protection

All examples use synthetic identifiers and fictional medication records. Screenshots must be checked for email addresses, account identifiers, browser tabs, private URLs, avatars, and other unnecessary personal information before publication.

Structured audit evidence must exclude synthetic patient references, medication names, dosage instructions, and free text unless a specific test requires those fields and publication remains safe.

## 7. Execution layers and honest status

The project reports each layer independently:

- implementation status: the local UI, HTTP adapter, service, SQLite repository, SQL checks, and evidence tooling exist;
- automated status: 21 unit, integration, database, handler, UI-contract, evidence-runner, and version-consistency tests pass;
- API evidence status: five deterministic API-contract cases execute against a fresh temporary database;
- live UI status: browser-to-loopback execution is `Blocked — Not Executed` in the restricted sprint environment;
- visual preview status: a static render may be inspected for layout, but it is never used as execution evidence.

These statuses are not merged into a broader claim. A passing handler test does not become a passing browser case, and a static screenshot does not prove a submitted request.

## 8. Phase 3 domain review boundary

Independent domain review is planned for a later phase. No reviewer name, professional relationship, review outcome, endorsement, clinical approval, or regulatory conclusion is published before the review actually occurs and the reviewer explicitly approves any attribution. Phase 2 therefore makes no domain-validation claim.
