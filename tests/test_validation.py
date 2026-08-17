"""Unit tests for the pure RXQA-5 validation rule."""

import unittest

from rxcare.models import PrescriptionInput
from rxcare.validation import is_blank, validate_prescription


class BlankValueTests(unittest.TestCase):
    def test_none_empty_and_whitespace_are_blank(self) -> None:
        for value in (None, "", " ", "   ", "\t\n"):
            with self.subTest(value=value):
                self.assertTrue(is_blank(value))

    def test_visible_text_is_not_blank(self) -> None:
        self.assertFalse(is_blank("Take once daily"))


class PrescriptionValidationTests(unittest.TestCase):
    def test_whitespace_dosage_has_exact_rxqa_5_issue(self) -> None:
        result = validate_prescription(
            PrescriptionInput(
                record_id="SYN-RXQA-002",
                patient_ref="SYN-PAT-002",
                medication_name="Synthetic Medicine B",
                dosage_instruction="   ",
            )
        )

        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].code, "DOSAGE_REQUIRED")
        self.assertEqual(result.issues[0].field, "dosage_instruction")
        self.assertEqual(result.issues[0].message, "Dosage is required")

    def test_valid_record_has_no_issues(self) -> None:
        result = validate_prescription(
            PrescriptionInput(
                record_id="SYN-RXQA-003",
                patient_ref="SYN-PAT-003",
                medication_name="Synthetic Medicine C",
                dosage_instruction="Take one unit once daily",
            )
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(result.issues, [])


if __name__ == "__main__":
    unittest.main()

