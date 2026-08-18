"""A dependency-free local REST adapter for the first RxCare prototype.

FastAPI is a later sprint milestone. This adapter keeps the first execution
fully reproducible on the installed Python runtime while preserving a small,
clear HTTP contract.
"""

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from .database import RxCareDatabase
from .models import PrescriptionInput
from .service import PrescriptionService
from .ui import render_index
from .version import APP_VERSION


MAX_JSON_BODY_BYTES = 64 * 1024


def _json_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")


def make_handler(service: PrescriptionService):
    """Create a request handler bound to one service instance."""

    class RxCareRequestHandler(BaseHTTPRequestHandler):
        server_version = f"RxCarePrototype/{APP_VERSION}"
        protocol_version = "HTTP/1.1"

        def log_message(self, format_string: str, *args: object) -> None:
            # Evidence is captured as structured JSON instead of access logs.
            return

        def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
            body = _json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, status: int, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'unsafe-inline'; "
                "script-src 'unsafe-inline'; connect-src 'self'; "
                "img-src 'self' data:; base-uri 'none'; form-action 'self'",
            )
            self.end_headers()
            self.wfile.write(body)

        def _read_json(
            self,
        ) -> Tuple[bool, Dict[str, Any], int, str, str]:
            content_type = self.headers.get("Content-Type", "")
            media_type = content_type.split(";", 1)[0].strip().lower()
            if media_type != "application/json":
                return (
                    False,
                    {},
                    HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                    "UNSUPPORTED_MEDIA_TYPE",
                    "Content-Type must be application/json",
                )

            raw_content_length = self.headers.get("Content-Length")
            if raw_content_length is None:
                return (
                    False,
                    {},
                    HTTPStatus.LENGTH_REQUIRED,
                    "CONTENT_LENGTH_REQUIRED",
                    "Content-Length is required",
                )

            try:
                content_length = int(raw_content_length)
            except ValueError:
                return (
                    False,
                    {},
                    HTTPStatus.BAD_REQUEST,
                    "INVALID_CONTENT_LENGTH",
                    "Content-Length must be a non-negative integer",
                )

            if content_length < 0:
                return (
                    False,
                    {},
                    HTTPStatus.BAD_REQUEST,
                    "INVALID_CONTENT_LENGTH",
                    "Content-Length must be a non-negative integer",
                )
            if content_length > MAX_JSON_BODY_BYTES:
                self.close_connection = True
                return (
                    False,
                    {},
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    "PAYLOAD_TOO_LARGE",
                    f"JSON body exceeds {MAX_JSON_BODY_BYTES} bytes",
                )

            try:
                raw = self.rfile.read(content_length)
                if len(raw) != content_length:
                    return (
                        False,
                        {},
                        HTTPStatus.BAD_REQUEST,
                        "INCOMPLETE_BODY",
                        "Request body is shorter than Content-Length",
                    )
                payload = json.loads(raw.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("JSON body must be an object")
                return True, payload, HTTPStatus.OK, "", ""
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                return (
                    False,
                    {},
                    HTTPStatus.BAD_REQUEST,
                    "INVALID_JSON",
                    "A JSON object is required",
                )

        def do_GET(self) -> None:  # noqa: N802 - HTTP handler naming
            parsed = urlparse(self.path)

            if parsed.path in ("/", "/index.html"):
                self._send_html(HTTPStatus.OK, render_index(APP_VERSION))
                return

            if parsed.path == "/health":
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "app_version": APP_VERSION,
                        "scope": "local synthetic-data prototype",
                    },
                )
                return

            prescription_prefix = "/api/v1/prescriptions/"
            if parsed.path.startswith(prescription_prefix):
                record_id = unquote(parsed.path[len(prescription_prefix) :])
                result = service.database.get_prescription(record_id)
                if result is None:
                    self._send_json(
                        HTTPStatus.NOT_FOUND,
                        {"status": "NOT_FOUND", "record_id": record_id},
                    )
                else:
                    self._send_json(HTTPStatus.OK, {"prescription": result})
                return

            if parsed.path == "/api/v1/audit-events":
                record_id = parse_qs(parsed.query).get("record_id", [""])[0]
                events = service.database.get_audit_events(record_id)
                self._send_json(
                    HTTPStatus.OK,
                    {"record_id": record_id, "events": events},
                )
                return

            if parsed.path == "/api/v1/quality-checks":
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "prescription_checks": service.database.quality_checks(),
                        "audit_summary": service.database.audit_summary(),
                    },
                )
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"status": "NOT_FOUND"})

        def do_POST(self) -> None:  # noqa: N802 - HTTP handler naming
            if urlparse(self.path).path != "/api/v1/prescriptions":
                self._send_json(HTTPStatus.NOT_FOUND, {"status": "NOT_FOUND"})
                return

            (
                is_valid_json,
                payload,
                error_status,
                error_code,
                error_message,
            ) = self._read_json()
            if not is_valid_json:
                self._send_json(
                    error_status,
                    {
                        "status": "REJECTED",
                        "reason_code": error_code,
                        "message": error_message,
                    },
                )
                return

            result = service.submit(PrescriptionInput.from_mapping(payload))
            status = int(result.pop("http_status"))
            self._send_json(status, result)

    return RxCareRequestHandler


def create_server(
    database_path: Path, host: str = "127.0.0.1", port: int = 0
) -> ThreadingHTTPServer:
    database = RxCareDatabase(database_path)
    service = PrescriptionService(database)
    return create_bound_server(service, host, port)


def create_bound_server(
    service: PrescriptionService, host: str = "127.0.0.1", port: int = 0
) -> ThreadingHTTPServer:
    """Bind the HTTP server after service/database initialization succeeds."""

    return ThreadingHTTPServer((host, port), make_handler(service))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local RxCare API")
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("runtime/rxcare.db"),
        help="SQLite database path",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = create_server(args.database, args.host, args.port)
    print(
        f"RxCare {APP_VERSION} listening on "
        f"http://{server.server_address[0]}:{server.server_address[1]}"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
