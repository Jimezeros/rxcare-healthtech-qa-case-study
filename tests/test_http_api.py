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
from rxcare.http_api import MAX_JSON_BODY_BYTES, make_handler
from rxcare.service import PrescriptionService
from rxcare.version import APP_VERSION


class RxCareHttpApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "rxcare-http.db"
        self.service = PrescriptionService(
            RxCareDatabase(database_path)
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, Dict[str, str], bytes]:
        body = b""
        headers: Dict[str, str] = {}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
            }
        return self.raw_request(method, path, body=body, headers=headers)

    def raw_request(
        self,
        method: str,
        path: str,
        *,
        body: bytes = b"",
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Dict[str, str], bytes]:
        request_headers = ["Host: rxcare.local", "Connection: close"]
        request_headers.extend(
            f"{name}: {value}" for name, value in (headers or {}).items()
        )
        raw_request = (
            f"{method} {path} HTTP/1.1\r\n"
            + "\r\n".join(request_headers)
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
        header_lines = header_bytes.splitlines()
        status_line = header_lines[0].decode("ascii")
        self.last_status_line = status_line
        status = int(status_line.split()[1])
        response_headers = {}
        for raw_header in header_lines[1:]:
            name, value = raw_header.decode("iso-8859-1").split(":", 1)
            response_headers[name.lower()] = value.strip()
        return status, response_headers, response_body

    def request_json(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        status, _, response_body = self.request(method, path, payload)
        return status, json.loads(response_body.decode("utf-8"))

    def test_ui_route_serves_self_contained_validation_workspace(self) -> None:
        status, headers, response_body = self.request("GET", "/")
        html = response_body.decode("utf-8")

        self.assertEqual(status, 200)
        self.assertTrue(self.last_status_line.startswith("HTTP/1.1 200"))
        self.assertEqual(headers["content-type"], "text/html; charset=utf-8")
        self.assertEqual(headers["cache-control"], "no-store")
        self.assertIn("default-src 'self'", headers["content-security-policy"])
        self.assertIn('id="prescription-form"', html)
        for field_name in (
            "record_id",
            "patient_ref",
            "medication_name",
            "dosage_instruction",
        ):
            self.assertIn(f'name="{field_name}"', html)
        self.assertIn('fetchJson("/api/v1/prescriptions"', html)
        self.assertIn("/api/v1/audit-events?record_id=", html)
        self.assertIn('data-testid="canonical-output"', html)
        self.assertIn('data-testid="audit-output"', html)
        self.assertIn('id="dosage-error"', html)
        self.assertIn('role="alert" hidden>Dosage is required', html)
        self.assertIn(
            'aria-describedby="dosage-hint dosage-error"', html
        )
        self.assertIn("window.__rxcareEvidence", html)
        self.assertIn("dosage_code_points", html)
        self.assertIn(': "   ";', html)
        self.assertIn("Synthetic data only.", html)
        self.assertIn(f"Prototype v{APP_VERSION}", html)

    def test_health_endpoint(self) -> None:
        status, payload = self.request_json("GET", "/health")
        self.assertEqual(status, 200)
        self.assertTrue(self.last_status_line.startswith("HTTP/1.1 200"))
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["app_version"], APP_VERSION)

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

        audit_status, audit_payload = self.request_json(
            "GET", "/api/v1/audit-events?record_id=SYN-HTTP-001"
        )
        self.assertEqual(audit_status, 200)
        self.assertEqual(len(audit_payload["events"]), 1)
        self.assertEqual(audit_payload["events"][0]["outcome"], "REJECTED")
        self.assertEqual(
            audit_payload["events"][0]["reason_code"], "DOSAGE_REQUIRED"
        )

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

    def test_end_to_end_handler_exposes_canonical_and_safe_audit_evidence(self) -> None:
        request_payload = {
            "record_id": "SYN-HTTP-E2E-001",
            "patient_ref": "SYN-PAT-E2E-001",
            "medication_name": "Synthetic Medicine",
            "dosage_instruction": "Take one synthetic unit once daily",
        }

        submit_status, submit_payload = self.request_json(
            "POST", "/api/v1/prescriptions", request_payload
        )
        self.assertEqual(submit_status, 201)
        self.assertEqual(submit_payload["status"], "ACCEPTED")

        canonical_status, canonical_payload = self.request_json(
            "GET", "/api/v1/prescriptions/SYN-HTTP-E2E-001"
        )
        self.assertEqual(canonical_status, 200)
        self.assertEqual(
            canonical_payload["prescription"]["record_id"],
            request_payload["record_id"],
        )
        self.assertEqual(
            canonical_payload["prescription"]["patient_ref"],
            request_payload["patient_ref"],
        )

        audit_status, audit_payload = self.request_json(
            "GET", "/api/v1/audit-events?record_id=SYN-HTTP-E2E-001"
        )
        self.assertEqual(audit_status, 200)
        self.assertEqual(len(audit_payload["events"]), 1)
        event = audit_payload["events"][0]
        self.assertEqual(event["outcome"], "ACCEPTED")
        self.assertIsNone(event["reason_code"])
        self.assertEqual(event["record_id"], request_payload["record_id"])
        self.assertNotIn("patient_ref", event)
        self.assertNotIn("medication_name", event)
        self.assertNotIn("dosage_instruction", event)

    def test_post_rejects_unsupported_content_type_without_audit(self) -> None:
        body = b'{}'
        status, _, response_body = self.raw_request(
            "POST",
            "/api/v1/prescriptions",
            body=body,
            headers={
                "Content-Type": "text/plain",
                "Content-Length": str(len(body)),
            },
        )
        payload = json.loads(response_body.decode("utf-8"))

        self.assertEqual(status, 415)
        self.assertEqual(payload["reason_code"], "UNSUPPORTED_MEDIA_TYPE")
        self.assertEqual(self.service.database.audit_summary(), [])

    def test_post_requires_valid_content_length_without_audit(self) -> None:
        cases = (
            ("missing", {}, "CONTENT_LENGTH_REQUIRED", 411),
            (
                "non-integer",
                {"Content-Length": "not-a-number"},
                "INVALID_CONTENT_LENGTH",
                400,
            ),
            (
                "negative",
                {"Content-Length": "-1"},
                "INVALID_CONTENT_LENGTH",
                400,
            ),
            (
                "short-body",
                {"Content-Length": "3"},
                "INCOMPLETE_BODY",
                400,
            ),
        )
        for label, extra_headers, reason_code, expected_status in cases:
            with self.subTest(label=label):
                headers = {"Content-Type": "application/json"}
                headers.update(extra_headers)
                body = b"{}" if label != "missing" else b""
                status, _, response_body = self.raw_request(
                    "POST",
                    "/api/v1/prescriptions",
                    body=body,
                    headers=headers,
                )
                payload = json.loads(response_body.decode("utf-8"))
                self.assertEqual(status, expected_status)
                self.assertEqual(payload["reason_code"], reason_code)

        self.assertEqual(self.service.database.audit_summary(), [])

    def test_post_rejects_oversized_declared_body_without_reading(self) -> None:
        status, _, response_body = self.raw_request(
            "POST",
            "/api/v1/prescriptions",
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(MAX_JSON_BODY_BYTES + 1),
            },
        )
        payload = json.loads(response_body.decode("utf-8"))

        self.assertEqual(status, 413)
        self.assertEqual(payload["reason_code"], "PAYLOAD_TOO_LARGE")
        self.assertEqual(self.service.database.audit_summary(), [])

    def test_json_content_type_parameters_are_accepted(self) -> None:
        request_payload = {
            "record_id": "SYN-HTTP-CONTENT-TYPE-001",
            "patient_ref": "SYN-PAT-CONTENT-TYPE-001",
            "medication_name": "Synthetic Medicine",
            "dosage_instruction": "Take one synthetic unit daily",
        }
        body = json.dumps(request_payload).encode("utf-8")
        status, _, response_body = self.raw_request(
            "POST",
            "/api/v1/prescriptions",
            body=body,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Content-Length": str(len(body)),
            },
        )
        payload = json.loads(response_body.decode("utf-8"))

        self.assertEqual(status, 201)
        self.assertEqual(payload["status"], "ACCEPTED")


if __name__ == "__main__":
    unittest.main()
