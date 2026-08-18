"""Integration tests for validation, SQLite persistence, and audit events."""

import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from rxcare.database import RxCareDatabase
from rxcare.models import PrescriptionInput
from rxcare.service import PrescriptionService
from rxcare.version import APP_VERSION


class PrescriptionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database = RxCareDatabase(
            Path(self.temporary_directory.name) / "rxcare-test.db"
        )
        self.service = PrescriptionService(self.database)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @staticmethod
    def record(
        record_id: str, dosage_instruction: Optional[str]
    ) -> PrescriptionInput:
        return PrescriptionInput(
            record_id=record_id,
            patient_ref=f"SYN-PAT-{record_id[-3:]}",
            medication_name="Synthetic Medicine",
            dosage_instruction=dosage_instruction,
        )

    def assert_rejected_without_canonical_row(
        self, record_id: str, dosage_instruction: Optional[str]
    ) -> None:
        response = self.service.submit(
            self.record(record_id, dosage_instruction)
        )

        self.assertEqual(response["http_status"], 422)
        self.assertEqual(response["status"], "REJECTED")
        self.assertEqual(response["message"], "Dosage is required")
        self.assertEqual(response["reason_code"], "DOSAGE_REQUIRED")
        self.assertIsNone(self.database.get_prescription(record_id))

        events = self.database.get_audit_events(record_id)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["outcome"], "REJECTED")
        self.assertEqual(events[0]["reason_code"], "DOSAGE_REQUIRED")

    def test_empty_dosage_is_rejected_and_audited_once(self) -> None:
        self.assert_rejected_without_canonical_row("SYN-RXQA-001", "")

    def test_whitespace_dosage_is_rejected_and_audited_once(self) -> None:
        self.assert_rejected_without_canonical_row("SYN-RXQA-002", "   ")

    def test_null_dosage_is_rejected_and_audited_once(self) -> None:
        self.assert_rejected_without_canonical_row("SYN-RXQA-NULL", None)

    def test_valid_dosage_is_preserved_and_accepted_once(self) -> None:
        record = self.record(
            "SYN-RXQA-003", "Take one unit once daily after food"
        )
        response = self.service.submit(record)

        self.assertEqual(response["http_status"], 201)
        self.assertEqual(response["status"], "ACCEPTED")
        stored = self.database.get_prescription("SYN-RXQA-003")
        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(
            stored["dosage_instruction"], record.dosage_instruction
        )

        events = self.database.get_audit_events("SYN-RXQA-003")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["outcome"], "ACCEPTED")
        self.assertIsNone(events[0]["reason_code"])

    def test_audit_event_has_only_approved_privacy_safe_fields(self) -> None:
        record_id = "SYN-RXQA-004"
        self.service.submit(self.record(record_id, ""))

        events = self.database.get_audit_events(record_id)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["outcome"], "REJECTED")
        self.assertEqual(events[0]["reason_code"], "DOSAGE_REQUIRED")
        self.assertEqual(
            set(events[0]),
            {
                "event_id",
                "attempt_id",
                "timestamp_utc",
                "action",
                "record_id",
                "outcome",
                "reason_code",
                "app_version",
            },
        )
        serialized = repr(events[0])
        self.assertNotIn("patient_ref", serialized)
        self.assertNotIn("medication_name", serialized)
        self.assertNotIn("dosage_instruction", serialized)

    def test_duplicate_record_id_is_rejected_without_overwrite(self) -> None:
        record_id = "SYN-RXQA-005"
        first = self.service.submit(self.record(record_id, "Take once daily"))
        duplicate = self.service.submit(
            self.record(record_id, "Take twice daily")
        )

        self.assertEqual(first["http_status"], 201)
        self.assertEqual(duplicate["http_status"], 409)
        self.assertEqual(duplicate["reason_code"], "DUPLICATE_RECORD_ID")
        stored = self.database.get_prescription(record_id)
        assert stored is not None
        self.assertEqual(stored["dosage_instruction"], "Take once daily")
        self.assertEqual(len(self.database.get_audit_events(record_id)), 2)

    def test_40_concurrent_same_record_requests_are_controlled_and_audited(
        self,
    ) -> None:
        worker_count = 40
        record_id = "SYN-RXQA-CONCURRENT-001"
        start_barrier = threading.Barrier(worker_count)

        def submit_once(worker_number: int):
            start_barrier.wait(timeout=10)
            return self.service.submit(
                PrescriptionInput(
                    record_id=record_id,
                    patient_ref=f"SYN-PAT-CONCURRENT-{worker_number:02d}",
                    medication_name="Synthetic Medicine",
                    dosage_instruction=(
                        f"Take synthetic unit {worker_number:02d} once daily"
                    ),
                )
            )

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            responses = list(executor.map(submit_once, range(worker_count)))

        accepted = [
            response for response in responses
            if response["http_status"] == 201
        ]
        conflicts = [
            response for response in responses
            if response["http_status"] == 409
        ]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(len(conflicts), worker_count - 1)
        self.assertEqual(
            {response["reason_code"] for response in conflicts},
            {"DUPLICATE_RECORD_ID"},
        )

        stored = self.database.get_prescription(record_id)
        self.assertIsNotNone(stored)
        events = self.database.get_audit_events(record_id)
        self.assertEqual(len(events), worker_count)
        self.assertEqual(
            sum(event["outcome"] == "ACCEPTED" for event in events), 1
        )
        self.assertEqual(
            sum(event["outcome"] == "REJECTED" for event in events),
            worker_count - 1,
        )
        self.assertEqual(
            {event["reason_code"] for event in events if event["outcome"] == "REJECTED"},
            {"DUPLICATE_RECORD_ID"},
        )
        self.assertEqual(
            len({event["attempt_id"] for event in events}), worker_count
        )

    def test_record_id_is_normalized_consistently_before_storage(self) -> None:
        submitted = PrescriptionInput(
            record_id="  SYN-RXQA-007  ",
            patient_ref="SYN-PAT-007",
            medication_name="Synthetic Medicine",
            dosage_instruction="Take once daily",
        )

        response = self.service.submit(submitted)

        self.assertEqual(response["http_status"], 201)
        self.assertEqual(response["record_id"], "SYN-RXQA-007")
        self.assertIsNotNone(self.database.get_prescription("SYN-RXQA-007"))
        self.assertIsNone(
            self.database.get_prescription("  SYN-RXQA-007  ")
        )
        events = self.database.get_audit_events("SYN-RXQA-007")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["record_id"], "SYN-RXQA-007")

    def test_sqlite_check_rejects_direct_whitespace_variants(self) -> None:
        variants = {
            "spaces": "   ",
            "tab": "\t",
            "newline": "\n",
            "carriage-return-newline": "\r\n",
            "non-breaking-space": "\u00a0",
            "em-space": "\u2003",
            "ideographic-space": "\u3000",
        }
        for index, (label, dosage) in enumerate(variants.items(), 1):
            with self.subTest(label=label):
                with self.database.connection() as connection:
                    with self.assertRaises(sqlite3.IntegrityError):
                        connection.execute(
                            """
                            INSERT INTO prescriptions (
                                record_id, patient_ref, medication_name,
                                dosage_instruction, created_at_utc, app_version
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                f"SYN-DIRECT-{index:03d}",
                                "SYN-PAT-DIRECT",
                                "Synthetic Medicine",
                                dosage,
                                "2026-08-17T00:00:00Z",
                                APP_VERSION,
                            ),
                        )

    def test_quality_checks_are_zero_for_valid_canonical_data(self) -> None:
        self.service.submit(
            self.record("SYN-RXQA-006", "Take one unit every morning")
        )

        findings = {
            row["check_name"]: row["finding_count"]
            for row in self.database.quality_checks()
        }
        self.assertEqual(
            findings,
            {
                "DUPLICATE_RECORD_ID_GROUPS": 0,
                "EMPTY_DOSAGE": 0,
                "NULL_DOSAGE": 0,
                "WHITESPACE_ONLY_DOSAGE": 0,
            },
        )


if __name__ == "__main__":
    unittest.main()
