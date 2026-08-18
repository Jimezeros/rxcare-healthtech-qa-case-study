#!/usr/bin/env python3
"""Execute the RXQA-5 slice and capture reproducible, synthetic evidence."""

import hashlib
import io
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rxcare.database import RxCareDatabase
from rxcare.http_api import make_handler
from rxcare.service import PrescriptionService
from rxcare.version import APP_VERSION


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_AUDIT_FIELDS = {
    "event_id",
    "attempt_id",
    "timestamp_utc",
    "action",
    "record_id",
    "outcome",
    "reason_code",
    "app_version",
}


def source_manifest() -> Tuple[str, List[Dict[str, str]]]:
    """Fingerprint the exact executable, SQL, and test sources for this run."""

    candidates = [
        REPOSITORY_ROOT / "VERSION",
        REPOSITORY_ROOT / "pyproject.toml",
    ]
    for pattern in ("src/**/*.py", "sql/*.sql", "tests/*.py", "scripts/*.py"):
        candidates.extend(REPOSITORY_ROOT.glob(pattern))

    entries = []
    for path in sorted({item.resolve() for item in candidates}):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(
            {
                "path": str(path.relative_to(REPOSITORY_ROOT)),
                "sha256": digest,
            }
        )
    canonical = json.dumps(
        entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest(), entries


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def http_exchange(
    service: PrescriptionService,
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Exercise the real HTTP handler without opening a blocked TCP port."""

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

    handler_class = make_handler(service)
    handler = handler_class.__new__(handler_class)
    handler.rfile = io.BytesIO(raw_request)
    handler.wfile = io.BytesIO()
    handler.client_address = ("in-process", 0)
    handler.server = object()
    handler.close_connection = True
    handler.handle_one_request()

    raw_response = handler.wfile.getvalue()
    response_headers, response_body = raw_response.split(b"\r\n\r\n", 1)
    status_line = response_headers.splitlines()[0].decode("ascii")
    if not status_line.startswith("HTTP/1.1 "):
        raise AssertionError(f"Unexpected HTTP response framing: {status_line}")
    status = int(status_line.split()[1])
    return status, json.loads(response_body.decode("utf-8"))


def persist_exchange(
    case_directory: Path,
    *,
    method: str,
    path: str,
    request_payload: Optional[Dict[str, Any]],
    status: int,
    response_payload: Dict[str, Any],
) -> None:
    write_json(
        case_directory / "request.json",
        {"method": method, "path": path, "body": request_payload},
    )
    write_json(
        case_directory / "response.json",
        {"http_status": status, "body": response_payload},
    )


def assert_equal(actual: Any, expected: Any, label: str) -> Dict[str, Any]:
    passed = actual == expected
    if not passed:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")
    return {
        "assertion": label,
        "expected": expected,
        "actual": actual,
        "result": "PASS",
    }


def execute_api_cases(
    service: PrescriptionService, run_directory: Path
) -> List[Dict[str, Any]]:
    cases_root = run_directory / "api-cases"
    summaries: List[Dict[str, Any]] = []

    invalid_cases = [
        ("API-TC-01", "Empty dosage is rejected", "SYN-RUN-001", ""),
        (
            "API-TC-02",
            "Whitespace-only dosage is rejected",
            "SYN-RUN-002",
            "   ",
        ),
    ]
    for case_id, title, record_id, dosage in invalid_cases:
        case_directory = cases_root / case_id
        payload = {
            "record_id": record_id,
            "patient_ref": f"SYN-PAT-{record_id[-3:]}",
            "medication_name": "Synthetic Medicine",
            "dosage_instruction": dosage,
        }
        status, response = http_exchange(
            service, "POST", "/api/v1/prescriptions", payload
        )
        persist_exchange(
            case_directory,
            method="POST",
            path="/api/v1/prescriptions",
            request_payload=payload,
            status=status,
            response_payload=response,
        )
        get_status, get_response = http_exchange(
            service, "GET", f"/api/v1/prescriptions/{record_id}"
        )
        audit_status, audit_response = http_exchange(
            service,
            "GET",
            f"/api/v1/audit-events?record_id={record_id}",
        )
        write_json(
            case_directory / "canonical-record-check.json",
            {"http_status": get_status, "body": get_response},
        )
        write_json(
            case_directory / "audit-check.json",
            {"http_status": audit_status, "body": audit_response},
        )
        assertions = [
            assert_equal(status, 422, "HTTP status"),
            assert_equal(response["status"], "REJECTED", "validation status"),
            assert_equal(
                response["reason_code"], "DOSAGE_REQUIRED", "reason code"
            ),
            assert_equal(
                response["message"], "Dosage is required", "error message"
            ),
            assert_equal(get_status, 404, "canonical record absent"),
            assert_equal(audit_status, 200, "audit query status"),
            assert_equal(
                len(audit_response["events"]), 1, "exactly one audit event"
            ),
            assert_equal(
                audit_response["events"][0]["outcome"],
                "REJECTED",
                "audit outcome",
            ),
        ]
        write_json(case_directory / "assertions.json", assertions)
        summaries.append(
            {"case_id": case_id, "title": title, "result": "PASS"}
        )

    valid_case_directory = cases_root / "API-TC-03"
    valid_payload = {
        "record_id": "SYN-RUN-003",
        "patient_ref": "SYN-PAT-003",
        "medication_name": "Synthetic Medicine",
        "dosage_instruction": "Take one unit once daily after food",
    }
    status, response = http_exchange(
        service, "POST", "/api/v1/prescriptions", valid_payload
    )
    persist_exchange(
        valid_case_directory,
        method="POST",
        path="/api/v1/prescriptions",
        request_payload=valid_payload,
        status=status,
        response_payload=response,
    )
    get_status, get_response = http_exchange(
        service, "GET", "/api/v1/prescriptions/SYN-RUN-003"
    )
    write_json(
        valid_case_directory / "canonical-record-check.json",
        {"http_status": get_status, "body": get_response},
    )
    valid_assertions = [
        assert_equal(status, 201, "HTTP status"),
        assert_equal(response["status"], "ACCEPTED", "validation status"),
        assert_equal(get_status, 200, "canonical record found"),
        assert_equal(
            get_response["prescription"]["dosage_instruction"],
            valid_payload["dosage_instruction"],
            "dosage preserved exactly",
        ),
    ]
    write_json(valid_case_directory / "assertions.json", valid_assertions)
    summaries.append(
        {
            "case_id": "API-TC-03",
            "title": "Valid dosage is persisted",
            "result": "PASS",
        }
    )

    privacy_case_directory = cases_root / "API-TC-04"
    audit_status, audit_response = http_exchange(
        service,
        "GET",
        "/api/v1/audit-events?record_id=SYN-RUN-001",
    )
    persist_exchange(
        privacy_case_directory,
        method="GET",
        path="/api/v1/audit-events?record_id=SYN-RUN-001",
        request_payload=None,
        status=audit_status,
        response_payload=audit_response,
    )
    events = audit_response["events"]
    privacy_assertions = [
        assert_equal(audit_status, 200, "HTTP status"),
        assert_equal(len(events), 1, "exactly one rejected event"),
        assert_equal(
            sorted(events[0]),
            sorted(ALLOWED_AUDIT_FIELDS),
            "approved audit fields only",
        ),
        assert_equal(events[0]["outcome"], "REJECTED", "audit outcome"),
        assert_equal(
            events[0]["reason_code"], "DOSAGE_REQUIRED", "audit reason code"
        ),
    ]
    write_json(privacy_case_directory / "assertions.json", privacy_assertions)
    summaries.append(
        {
            "case_id": "API-TC-04",
            "title": "Rejected audit event is privacy-safe",
            "result": "PASS",
        }
    )

    duplicate_case_directory = cases_root / "API-TC-05"
    duplicate_payload = dict(valid_payload)
    duplicate_payload["dosage_instruction"] = "Take twice daily"
    duplicate_status, duplicate_response = http_exchange(
        service, "POST", "/api/v1/prescriptions", duplicate_payload
    )
    persist_exchange(
        duplicate_case_directory,
        method="POST",
        path="/api/v1/prescriptions",
        request_payload=duplicate_payload,
        status=duplicate_status,
        response_payload=duplicate_response,
    )
    duplicate_get_status, duplicate_get_response = http_exchange(
        service, "GET", "/api/v1/prescriptions/SYN-RUN-003"
    )
    duplicate_audit_status, duplicate_audit_response = http_exchange(
        service,
        "GET",
        "/api/v1/audit-events?record_id=SYN-RUN-003",
    )
    write_json(
        duplicate_case_directory / "canonical-record-check.json",
        {
            "http_status": duplicate_get_status,
            "body": duplicate_get_response,
        },
    )
    write_json(
        duplicate_case_directory / "audit-check.json",
        {
            "http_status": duplicate_audit_status,
            "body": duplicate_audit_response,
        },
    )
    duplicate_assertions = [
        assert_equal(duplicate_status, 409, "HTTP status"),
        assert_equal(
            duplicate_response["reason_code"],
            "DUPLICATE_RECORD_ID",
            "duplicate reason code",
        ),
        assert_equal(
            duplicate_get_status, 200, "original canonical record still found"
        ),
        assert_equal(
            duplicate_get_response["prescription"]["dosage_instruction"],
            valid_payload["dosage_instruction"],
            "original dosage not overwritten",
        ),
        assert_equal(
            duplicate_audit_status, 200, "duplicate audit query status"
        ),
        assert_equal(
            len(duplicate_audit_response["events"]),
            2,
            "accepted and duplicate-rejected attempts both audited",
        ),
        assert_equal(
            duplicate_audit_response["events"][1]["reason_code"],
            "DUPLICATE_RECORD_ID",
            "duplicate audit reason code",
        ),
    ]
    write_json(
        duplicate_case_directory / "assertions.json", duplicate_assertions
    )
    summaries.append(
        {
            "case_id": "API-TC-05",
            "title": "Duplicate record ID is rejected",
            "result": "PASS",
        }
    )
    return summaries


def create_markdown_report(
    run_directory: Path,
    metadata: Dict[str, Any],
    case_summaries: List[Dict[str, Any]],
    tests_passed: bool,
) -> None:
    rows = "\n".join(
        f"| {case['case_id']} | {case['title']} | {case['result']} |"
        for case in case_summaries
    )
    overall = "PASS" if tests_passed else "FAIL"
    report = f"""# RxCare v{APP_VERSION} — Execution report

## Result

**{overall}** for the first executable RXQA-5 vertical slice.

- Run ID: `{metadata['run_id']}`
- UTC execution time: `{metadata['started_at_utc']}`
- Runtime: `{metadata['python_version']}` on `{metadata['platform']}`
- Data: synthetic identifiers and fictional medication data only
- Database: fresh temporary SQLite database, removed after sanitized export

## Executed API-contract cases

| Case | Purpose | Result |
|---|---|---|
{rows}

The cases above exercised the real Python HTTP handler with complete HTTP/1.1
request and response framing inside the process. The sandbox blocked opening a
local TCP listener, so a live-port smoke test was **not executed in this run**.
The runbook contains the command for that separate workstation check.

## Automated verification

The standard-library automated suite was executed from a clean temporary
database. Its human-readable output is in `automated_test_output.txt`; the
machine-readable result is in `junit.xml`.

## RXQA-10 status

The whitespace-only dosage risk was **not reproduced on v{APP_VERSION}**:
`API-TC-02` returned HTTP 422, created no canonical prescription row, and
created one privacy-safe `REJECTED` audit event. RXQA-10 remains a candidate
risk, not a confirmed defect.

## Scope boundary

The Jira UI-oriented cases RXQA-6 through RXQA-9 remain `Not Executed` in
this run. Version v{APP_VERSION} includes a local browser UI, but the restricted
execution environment blocked opening a loopback TCP listener. This run
therefore demonstrates the handler/service/database contract, not live browser
execution. It does not demonstrate deployment, clinical validation, regulatory
compliance, authentication, AI capability, or production readiness.
"""
    (run_directory / "TEST_EXECUTION_REPORT.md").write_text(
        report, encoding="utf-8"
    )


def create_manifest(run_directory: Path) -> None:
    lines = []
    for path in sorted(run_directory.rglob("*")):
        if not path.is_file() or path.name == "sha256_manifest.txt":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(run_directory)}")
    (run_directory / "sha256_manifest.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> int:
    started_at = utc_timestamp()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + (
        f"-v{APP_VERSION}"
    )
    run_directory = REPOSITORY_ROOT / "evidence" / "execution" / run_id
    if run_directory.exists():
        raise RuntimeError(f"Run directory already exists: {run_directory}")
    run_directory.mkdir(parents=True)

    source_tree_digest, source_entries = source_manifest()

    metadata: Dict[str, Any] = {
        "run_id": run_id,
        "started_at_utc": started_at,
        "app_version": APP_VERSION,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_sha": None,
        "git_status_note": (
            "Execution used the verified local staging copy; network-restricted "
            "Git synchronization was not performed in this run."
        ),
        "source_tree_sha256": source_tree_digest,
        "database": "fresh temporary SQLite database; deleted after export",
        "data_classification": "synthetic only",
        "http_execution_mode": "in-process BaseHTTPRequestHandler contract",
        "tcp_listener_executed": False,
        "test_runner": "Python unittest (pytest-compatible test structure)",
        "command": "PYTHONPATH=src python3 scripts/capture_execution_evidence.py",
    }
    write_json(run_directory / "run_metadata.json", metadata)
    write_json(
        run_directory / "source_manifest.json",
        {
            "algorithm": "SHA-256",
            "combined_source_tree_sha256": source_tree_digest,
            "files": source_entries,
        },
    )

    with tempfile.TemporaryDirectory(prefix="rxcare-evidence-") as temp_dir:
        database = RxCareDatabase(Path(temp_dir) / "rxcare-run.db")
        service = PrescriptionService(database)
        case_summaries = execute_api_cases(service, run_directory)
        write_json(
            run_directory / "quality_checks.json",
            {
                "prescription_checks": database.quality_checks(),
                "audit_summary": database.audit_summary(),
            },
        )
        all_events: List[Dict[str, Any]] = []
        for record_id in ("SYN-RUN-001", "SYN-RUN-002", "SYN-RUN-003"):
            all_events.extend(database.get_audit_events(record_id))
        write_json(run_directory / "sanitized_audit_events.json", all_events)

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPOSITORY_ROOT / "src")
    environment["PYTHONPYCACHEPREFIX"] = "/tmp/rxcare-evidence-pycache"
    junit_path = run_directory / "junit.xml"
    test_process = subprocess.run(
        [
            sys.executable,
            "scripts/run_tests.py",
            "--junit",
            str(junit_path),
        ],
        cwd=REPOSITORY_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    test_output = test_process.stdout
    if test_process.stderr:
        test_output += "\n[stderr]\n" + test_process.stderr
    (run_directory / "automated_test_output.txt").write_text(
        test_output, encoding="utf-8"
    )
    tests_passed = test_process.returncode == 0
    write_json(
        run_directory / "candidate_risk_RXQA-10.json",
        {
            "issue": "RXQA-10",
            "version": APP_VERSION,
            "status": "NOT_REPRODUCED",
            "evidence_case": "API-TC-02",
            "interpretation": (
                "Whitespace-only dosage was rejected; no confirmed defect exists."
            ),
        },
    )
    create_markdown_report(
        run_directory, metadata, case_summaries, tests_passed
    )
    create_manifest(run_directory)

    print(run_directory)
    if not tests_passed:
        print("Automated tests failed; inspect automated_test_output.txt")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
