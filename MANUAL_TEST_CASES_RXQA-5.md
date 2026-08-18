# RXQA-5 — Browser UI Test Cases

## Requirement

Reject prescription records with missing dosage instructions.

## v0.2.0 local execution profile

These are the browser variants mapped one-to-one to Jira cases RXQA-6 through RXQA-9. They target the local RxCare v0.2.0 prototype, a fresh SQLite database, and synthetic data only. Authentication/RBAC is outside this increment; the page and local audit-evidence panel do not implement authorization.

**Current execution status:** `BLOCKED — NOT EXECUTED`. The restricted sprint environment denied binding a loopback TCP listener. The UI and its integration hooks are implemented and automated-contract tested, but no browser-to-live-server PASS or screenshot is claimed.

---

## RXQA-6 / UI-TC-01 — Reject an empty dosage instruction

**Objective:** Verify that a synthetic prescription record is rejected when dosage instruction is empty.

**Synthetic data**

- Record ID: `SYN-UI-TC01-001`
- Patient reference: `SYN-PAT-TC01-001`
- Medication: `Synthetic Medicine A`
- Dosage instruction: empty

**Steps**

1. Open the local RxCare v0.2.0 validation workspace.
2. Enter the synthetic values.
3. Leave Dosage instruction empty.
4. Select `Validate and verify` once.
5. Inspect the validation, canonical-record, and audit panels.

**Expected result**

1. The request reaches the Python validation service and returns HTTP `422`.
2. Status is `REJECTED`, reason code is `DOSAGE_REQUIRED`, and `Dosage is required` appears next to the dosage field.
3. Canonical lookup returns `NOT_FOUND`.
4. Exactly one privacy-safe `REJECTED` audit event exists.

**Observed result:** Not observed; live loopback listener blocked by environment.  
**Status:** `BLOCKED — NOT EXECUTED`.

---

## RXQA-7 / UI-TC-02 — Reject whitespace-only dosage

**Objective:** Verify through the browser path that three ASCII spaces cannot bypass validation.

**Synthetic data**

- Record ID: `SYN-UI-TC02-001`
- Patient reference: `SYN-PAT-TC02-001`
- Medication: `Synthetic Medicine B`
- Dosage instruction: exactly three ASCII spaces

**Steps**

1. Enter valid synthetic values in all other fields.
2. Enter exactly three spaces in Dosage instruction.
3. Select `Validate and verify` once.
4. Inspect the validation, canonical-record, audit, and safe browser-evidence values.

**Expected result**

1. Safe browser evidence reports `dosage_length: 3` and code points `[32, 32, 32]` without retaining dosage text.
2. The service returns HTTP `422`, `REJECTED`, `DOSAGE_REQUIRED`, and exact message `Dosage is required`.
3. Canonical lookup returns `NOT_FOUND`.
4. Exactly one privacy-safe `REJECTED` audit event exists.

**Observed result:** Not observed through a live browser. The separate API/handler case passed, but it is not substituted for this UI execution.  
**Status:** `BLOCKED — NOT EXECUTED`.

---

## RXQA-8 / UI-TC-03 — Accept a complete dosage instruction

**Objective:** Verify the positive control and ensure valid data is not falsely rejected.

**Synthetic data**

- Record ID: `SYN-UI-TC03-001`
- Patient reference: `SYN-PAT-TC03-001`
- Medication: `Synthetic Medicine C`
- Dosage instruction: `Take one synthetic unit once daily`

**Steps**

1. Open the local validation workspace.
2. Enter the synthetic values and complete dosage instruction.
3. Select `Validate and verify` once.
4. Inspect the validation, canonical-record, and audit panels.

**Expected result**

1. The service returns HTTP `201` and status `ACCEPTED` with no dosage error.
2. Exactly one canonical record is shown.
3. Stored values, especially dosage, match the submitted values exactly.
4. Exactly one privacy-safe `ACCEPTED` audit event exists.

**Observed result:** Not observed; live loopback listener blocked by environment.  
**Status:** `BLOCKED — NOT EXECUTED`.

---

## RXQA-9 / UI-TC-04 — Create a privacy-safe rejection audit event

**Objective:** Verify browser-visible rejection traceability without unnecessary sensitive fields.

**Synthetic data**

- Record ID: `SYN-UI-TC04-001`
- Patient reference: `SYN-PAT-TC04-001`
- Medication: `Synthetic Medicine D`
- Dosage instruction: empty

**Steps**

1. Open the local validation workspace.
2. Enter the synthetic values and leave dosage empty.
3. Select `Validate and verify` once.
4. Inspect the audit-evidence panel for the matching synthetic record ID.

**Expected result**

1. Submission returns HTTP `422` and no canonical record exists.
2. Exactly one event exists with only `event_id`, `attempt_id`, `timestamp_utc`, `action`, `record_id`, `outcome`, `reason_code`, and `app_version`.
3. The event records `PRESCRIPTION_VALIDATION`, `REJECTED`, and `DOSAGE_REQUIRED`.
4. The event contains no patient reference, medication name, dosage text, or other free text.

**Observed result:** Not observed; live loopback listener blocked by environment.  
**Status:** `BLOCKED — NOT EXECUTED`.

## Run-level acceptance check

After genuine execution of all four cases against a fresh database, the expected total is one canonical record and four audit events: three `REJECTED` and one `ACCEPTED`. All canonical SQL quality-check findings must remain zero. Until that run and privacy-safe evidence exist, these cases remain `Not Executed`.
