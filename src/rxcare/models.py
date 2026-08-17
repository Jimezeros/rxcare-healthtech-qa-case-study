"""Small data models used by the validation service.

The models deliberately use Python's standard library so the first prototype
can be executed on a clean Python installation without downloading packages.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PrescriptionInput:
    """A synthetic prescription submission received by the prototype."""

    record_id: Optional[str]
    patient_ref: Optional[str]
    medication_name: Optional[str]
    dosage_instruction: Optional[str]

    @classmethod
    def from_mapping(cls, payload: Dict[str, Any]) -> "PrescriptionInput":
        """Create a model without silently inventing missing input values."""

        return cls(
            record_id=payload.get("record_id"),
            patient_ref=payload.get("patient_ref"),
            medication_name=payload.get("medication_name"),
            dosage_instruction=payload.get("dosage_instruction"),
        )


@dataclass(frozen=True)
class ValidationIssue:
    """A machine-readable business-validation failure."""

    code: str
    field: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationResult:
    """The outcome of pure validation before persistence."""

    is_valid: bool
    issues: List[ValidationIssue]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "issues": [issue.to_dict() for issue in self.issues],
        }
