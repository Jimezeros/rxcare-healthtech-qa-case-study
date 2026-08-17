"""HTTP-handler contract tests without opening a network listener.

The execution sandbox blocks local TCP binding. These tests still exercise
the real ``BaseHTTPRequestHandler`` parsing and response-writing path by
passing complete HTTP/1.1 messages through in-memory byte streams. A separate
local runbook explains how to start the listener on a normal workstation.
"""

import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from rxcare.database import RxCareDatabase
from rxcare.http_api import make_handler
from rxcare.service import PrescriptionService


class RxCareHttpApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "rxcare-http.db"
        self.service = PrescriptionService(
            RxCareDatabase(database_path)
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def request_json(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        body = b""
        headers = ["Host: rxcare.local", "Connection: close"]
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers.extend(
                [
                    "Content-Type: application/json",
                    f"Content-Length: {len(body)}",
                ]
            )
        raw_request = (
            f"{method} {path} HTTP/1.1\r\n"
            + "\r\n".join(headers)
            + "\r\n\r\n"
        ).encode("ascii") + body

        handler_class = make_handler(self.service)
        handler = handler_class.__new__(handler_class)
        handler.rfile = io.BytesIO(raw_request)
        handler.wfile = io.BytesIO()
        handler.client_address = ("in-process", 0)
        handler.server = object()
        handler.close_connection = True
        handler.handle_one_request()

        raw_response = handler.wfile.getvalue()
        header_bytes, response_body = raw_response.split(b"\r\n\r\n", 1)
        status_line = header_bytes.splitlines()[0].decode("ascii")
        self.last_status_line = status_line
        status = int(status_line.split()[1])
        return status, json.loads(response_body.decode("utf-8"))

    def test_health_endpoint(self) -> None:
        status, payload = self.request_json("GET", "/health")
        self.assertEqual(status, 200)
        self.assertTrue(self.last_status_line.startswith("HTTP/1.1 200"))
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["app_version"], "0.1.0")

    def test_whitespace_dosage_returns_structured_422(self) -> None:
        status, payload = self.request_json(
            "POST",
            "/api/v1/prescriptions",
            {
                "record_id": "SYN-HTTP-001",
                "patient_ref": "SYN-PAT-HTTP-001",
                "medication_name": "Synthetic Medicine",
                "dosage_instruction": "   ",
            },
        )

        self.assertEqual(status, 422)
        self.assertEqual(payload["status"], "REJECTED")
        self.assertEqual(payload["message"], "Dosage is required")
        self.assertEqual(payload["reason_code"], "DOSAGE_REQUIRED")

        get_status, get_payload = self.request_json(
            "GET", "/api/v1/prescriptions/SYN-HTTP-001"
        )
        self.assertEqual(get_status, 404)
        self.assertEqual(get_payload["status"], "NOT_FOUND")

    def test_valid_submission_can_be_retrieved(self) -> None:
        request_payload = {
            "record_id": "SYN-HTTP-002",
            "patient_ref": "SYN-PAT-HTTP-002",
            "medication_name": "Synthetic Medicine",
            "dosage_instruction": "Take one unit once daily",
        }
        status, payload = self.request_json(
            "POST", "/api/v1/prescriptions", request_payload
        )
        self.assertEqual(status, 201)
        self.assertEqual(payload["status"], "ACCEPTED")

        get_status, get_payload = self.request_json(
            "GET", "/api/v1/prescriptions/SYN-HTTP-002"
        )
        self.assertEqual(get_status, 200)
        self.assertEqual(
            get_payload["prescription"]["dosage_instruction"],
            request_payload["dosage_instruction"],
        )


if __name__ == "__main__":
    unittest.main()
