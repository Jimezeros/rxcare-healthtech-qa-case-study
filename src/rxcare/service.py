"""Application service that connects validation, persistence, and auditability."""

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .database import RxCareDatabase
from .models import PrescriptionInput, ValidationIssue
from .validation import validate_prescription
from .version import APP_VERSION


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class PrescriptionService:
    """Process one synthetic prescription submission atomically."""

    def __init__(self, database: RxCareDatabase):
        self.database = database
        self.database.initialize()

    @staticmethod
    def _safe_record_id(record_id: Optional[str]) -> str:
        if isinstance(record_id, str) and record_id.strip():
            return record_id.strip()
        return "UNAVAILABLE"

    @staticmethod
    def _insert_audit_event(
        connection: sqlite3.Connection,
        *,
        attempt_id: str,
        timestamp_utc: str,
        record_id: str,
        outcome: str,
        reason_code: Optional[str],
    ) -> int:
        cursor = connection.execute(
            """
            INSERT INTO validation_events (
                attempt_id, timestamp_utc, action, record_id,
                outcome, reason_code, app_version
            ) VALUES (?, ?, 'PRESCRIPTION_VALIDATION', ?, ?, ?, ?)
            """,
            (
                attempt_id,
                timestamp_utc,
                record_id,
                outcome,
                reason_code,
                APP_VERSION,
            ),
        )
        return int(cursor.lastrowid)

    def submit(self, record: PrescriptionInput) -> Dict[str, Any]:
        """Validate, persist when valid, and create exactly one audit event."""

        validation = validate_prescription(record)
        attempt_id = str(uuid.uuid4())
        timestamp_utc = utc_now()
        safe_record_id = self._safe_record_id(record.record_id)

        with self.database.connection() as connection:
            # Acquire the write reservation before the duplicate lookup. This
            # prevents concurrent deferred transactions from all reading a
            # missing ID and then failing while upgrading to a write lock.
            connection.execute("BEGIN IMMEDIATE")

            if not validation.is_valid:
                primary_issue = validation.issues[0]
                event_id = self._insert_audit_event(
                    connection,
                    attempt_id=attempt_id,
                    timestamp_utc=timestamp_utc,
                    record_id=safe_record_id,
                    outcome="REJECTED",
                    reason_code=primary_issue.code,
                )
                connection.commit()
                return {
                    "http_status": 422,
                    "status": "REJECTED",
                    "record_id": safe_record_id,
                    "message": primary_issue.message,
                    "reason_code": primary_issue.code,
                    "issues": [issue.to_dict() for issue in validation.issues],
                    "audit_event_id": event_id,
                    "app_version": APP_VERSION,
                }

            assert record.record_id is not None
            assert record.patient_ref is not None
            assert record.medication_name is not None
            assert record.dosage_instruction is not None
            normalized_record_id = safe_record_id

            if self.database.prescription_exists(
                connection, normalized_record_id
            ):
                duplicate_issue = ValidationIssue(
                    code="DUPLICATE_RECORD_ID",
                    field="record_id",
                    message="Record ID already exists",
                )
                event_id = self._insert_audit_event(
                    connection,
                    attempt_id=attempt_id,
                    timestamp_utc=timestamp_utc,
                    record_id=safe_record_id,
                    outcome="REJECTED",
                    reason_code=duplicate_issue.code,
                )
                connection.commit()
                return {
                    "http_status": 409,
                    "status": "REJECTED",
                    "record_id": safe_record_id,
                    "message": duplicate_issue.message,
                    "reason_code": duplicate_issue.code,
                    "issues": [duplicate_issue.to_dict()],
                    "audit_event_id": event_id,
                    "app_version": APP_VERSION,
                }

            connection.execute(
                """
                INSERT INTO prescriptions (
                    record_id, patient_ref, medication_name,
                    dosage_instruction, created_at_utc, app_version
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized_record_id,
                    record.patient_ref,
                    record.medication_name,
                    record.dosage_instruction,
                    timestamp_utc,
                    APP_VERSION,
                ),
            )
            event_id = self._insert_audit_event(
                connection,
                attempt_id=attempt_id,
                timestamp_utc=timestamp_utc,
                record_id=safe_record_id,
                outcome="ACCEPTED",
                reason_code=None,
            )
            connection.commit()

        return {
            "http_status": 201,
            "status": "ACCEPTED",
            "record_id": safe_record_id,
            "message": "Prescription accepted",
            "reason_code": None,
            "issues": [],
            "audit_event_id": event_id,
            "app_version": APP_VERSION,
        }
