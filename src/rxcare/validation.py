"""Pure validation rules for the RXQA-5 vertical slice."""

from typing import List, Optional

from .models import PrescriptionInput, ValidationIssue, ValidationResult


def is_blank(value: Optional[str]) -> bool:
    """Return True for None, empty, or whitespace-only text."""

    return value is None or not isinstance(value, str) or value.strip() == ""


def validate_prescription(record: PrescriptionInput) -> ValidationResult:
    """Validate fields required by the local prototype.

    RXQA-5 is the central product rule: a dosage instruction must exist after
    whitespace normalisation. The other required-field checks protect the API
    contract; they are not presented as extra medication-safety coverage.
    """

    issues: List[ValidationIssue] = []

    if is_blank(record.record_id):
        issues.append(
            ValidationIssue(
                code="RECORD_ID_REQUIRED",
                field="record_id",
                message="Record ID is required",
            )
        )

    if is_blank(record.patient_ref):
        issues.append(
            ValidationIssue(
                code="PATIENT_REF_REQUIRED",
                field="patient_ref",
                message="Synthetic patient reference is required",
            )
        )

    if is_blank(record.medication_name):
        issues.append(
            ValidationIssue(
                code="MEDICATION_REQUIRED",
                field="medication_name",
                message="Medication name is required",
            )
        )

    if is_blank(record.dosage_instruction):
        issues.append(
            ValidationIssue(
                code="DOSAGE_REQUIRED",
                field="dosage_instruction",
                message="Dosage is required",
            )
        )

    return ValidationResult(is_valid=not issues, issues=issues)
