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
from .version import APP_VERSION


def _json_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")


def make_handler(service: PrescriptionService):
    """Create a request handler bound to one service instance."""

    class RxCareRequestHandler(BaseHTTPRequestHandler):
        server_version = "RxCarePrototype/0.1"
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

        def _read_json(self) -> Tuple[bool, Dict[str, Any]]:
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(content_length)
                payload = json.loads(raw.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("JSON body must be an object")
                return True, payload
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                return False, {}

        def do_GET(self) -> None:  # noqa: N802 - HTTP handler naming
            parsed = urlparse(self.path)

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

            is_valid_json, payload = self._read_json()
            if not is_valid_json:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "status": "REJECTED",
                        "reason_code": "INVALID_JSON",
                        "message": "A JSON object is required",
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
