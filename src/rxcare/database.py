"""SQLite persistence with parameterised SQL and privacy-safe audit events."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, List, Optional


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPOSITORY_ROOT / "sql" / "schema.sql"
QUALITY_CHECKS_PATH = REPOSITORY_ROOT / "sql" / "quality_checks.sql"


class RxCareDatabase:
    """A small repository around one SQLite database file."""

    def __init__(self, database_path: Path):
        self.database_path = Path(database_path)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.database_path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create the schema and read-only quality-check views."""

        with self.connection() as connection:
            connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            connection.executescript(
                QUALITY_CHECKS_PATH.read_text(encoding="utf-8")
            )
            connection.commit()

    @staticmethod
    def prescription_exists(
        connection: sqlite3.Connection, record_id: str
    ) -> bool:
        row = connection.execute(
            "SELECT 1 FROM prescriptions WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        return row is not None

    @staticmethod
    def get_prescription_from_connection(
        connection: sqlite3.Connection, record_id: str
    ) -> Optional[Dict[str, str]]:
        row = connection.execute(
            """
            SELECT record_id, patient_ref, medication_name,
                   dosage_instruction, created_at_utc, app_version
            FROM prescriptions
            WHERE record_id = ?
            """,
            (record_id,),
        ).fetchone()
        return dict(row) if row else None

    def get_prescription(self, record_id: str) -> Optional[Dict[str, str]]:
        with self.connection() as connection:
            return self.get_prescription_from_connection(connection, record_id)

    def get_audit_events(self, record_id: str) -> List[Dict[str, str]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT event_id, attempt_id, timestamp_utc, action,
                       record_id, outcome, reason_code, app_version
                FROM validation_events
                WHERE record_id = ?
                ORDER BY event_id
                """,
                (record_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def quality_checks(self) -> List[Dict[str, object]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT check_name, finding_count
                FROM prescription_quality_checks
                ORDER BY check_name
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def audit_summary(self) -> List[Dict[str, object]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT outcome, event_count
                FROM audit_outcome_summary
                ORDER BY outcome
                """
            ).fetchall()
            return [dict(row) for row in rows]
