# RXQA-5 — Manual Test Cases

## Requirement

Reject prescription records with missing dosage instructions.

All records below are synthetic. Execution status: **NOT EXECUTED**.

---

## RXQA-6 / TC-01 — Reject an empty dosage instruction

**Objective:** Verify that a synthetic e-prescription record is rejected when dosage instruction is empty.

**Preconditions**

1. Tester is authenticated in the QA environment.
2. Prescription import form is available.
3. No real patient or pharmacy data is used.

**Synthetic data**

- Record ID: `SYN-RX-001`
- Medication: `Amoxicillin 500 mg`
- Dosage instruction: empty
- Other mandatory fields: valid synthetic values

**Steps**

1. Open the prescription import form.
2. Enter the synthetic record values.
3. Leave Dosage instruction empty.
4. Submit the record for validation.

**Expected result**

1. Submission is rejected.
2. `Dosage is required` appears next to the dosage field.
3. The record is not stored as valid.
4. A privacy-safe audit event is created.

---

## RXQA-7 / TC-02 — Reject whitespace-only dosage

**Objective:** Verify that whitespace-only input is normalised as missing and rejected.

**Preconditions**

1. Tester is authenticated in the QA environment.
2. Prescription import form is available.
3. No real patient or pharmacy data is used.

**Synthetic data**

- Record ID: `SYN-RX-002`
- Medication: `Metformin 850 mg`
- Dosage instruction: three space characters

**Steps**

1. Enter valid synthetic values in all other mandatory fields.
2. Enter three spaces in Dosage instruction.
3. Submit the record.

**Expected result**

1. Whitespace is trimmed.
2. Submission is rejected as an empty value.
3. `Dosage is required` is displayed.
4. The record is not stored as valid.

---

## RXQA-8 / TC-03 — Accept a complete dosage instruction

**Objective:** Provide a positive control and verify that valid data is not falsely rejected.

**Preconditions**

1. Tester is authenticated in the QA environment.
2. Prescription import form is available.
3. No real patient or pharmacy data is used.

**Synthetic data**

- Record ID: `SYN-RX-003`
- Medication: `Lisinopril 10 mg`
- Dosage instruction: `Take one tablet once daily`

**Steps**

1. Open the prescription import form.
2. Enter the synthetic record values.
3. Enter the complete dosage instruction.
4. Submit the record for validation.
5. Reopen or query the accepted record.

**Expected result**

1. No dosage-required message is displayed.
2. The record is accepted and displayed once.
3. Stored dosage text matches the submitted value.
4. A privacy-safe success audit event is created.

---

## RXQA-9 / TC-04 — Create a privacy-safe rejection audit event

**Objective:** Verify that rejection creates traceability without exposing unnecessary sensitive information.

**Preconditions**

1. Tester is authenticated in the QA environment.
2. Prescription import form and authorized audit view are available.
3. No real patient or pharmacy data is used.

**Synthetic data**

- Record ID: `SYN-RX-004`
- Patient reference: `SYN-PAT-004`
- Medication: `Ibuprofen 400 mg`
- Dosage instruction: empty

**Steps**

1. Open the prescription import form.
2. Enter the synthetic record values and leave dosage instruction empty.
3. Submit the record.
4. Record the submission timestamp and synthetic record ID.
5. Open the authorized audit view.
6. Search for the matching validation attempt.

**Expected result**

1. Exactly one rejection event exists.
2. It records timestamp, action, synthetic record ID, and outcome `REJECTED`.
3. It contains no patient name, contact data, or prescription free text.
4. The rejected record is not represented as valid medication.
