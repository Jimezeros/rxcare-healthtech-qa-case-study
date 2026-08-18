#!/usr/bin/env python3
"""Capture reproducible Phase 2 UI-workflow evidence over loopback TCP.

This non-interactive harness starts the real RxCare ``ThreadingHTTPServer`` on
an ephemeral loopback port and follows the same HTTP sequence as the browser
UI: submit a form payload, look up the canonical record, and retrieve its
audit events.  It does not execute JavaScript, drive a browser, or create
screenshots; those artifacts must be captured and labelled separately.

Only synthetic ``SYN-`` records are used.  The SQLite database is created in a
fresh temporary directory and removed after the sanitized evidence export.
"""

import argparse
import hashlib
import http.client
import ipaddress
import json
import os
import platform
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote

from rxcare.database import RxCareDatabase
from rxcare.http_api import create_bound_server
from rxcare.provenance import capture_source_control_context
from rxcare.service import PrescriptionService
from rxcare.version import APP_VERSION


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPOSITORY_ROOT / "evidence" / "execution"
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
FORBIDDEN_AUDIT_FIELDS = {
    "patient_ref",
    "medication_name",
    "dosage_instruction",
}


class LoopbackBindError(RuntimeError):
    """Raised when the execution environment blocks a loopback listener."""


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def source_manifest() -> Tuple[str, List[Dict[str, str]]]:
    """Fingerprint the executable, UI, SQL, test, and evidence sources."""

    candidates = [
        REPOSITORY_ROOT / "VERSION",
        REPOSITORY_ROOT / "pyproject.toml",
    ]
    for pattern in (
        "src/**/*.py",
        "src/**/*.sql",
        "sql/*.sql",
        "tests/*.py",
        "scripts/*.py",
    ):
        candidates.extend(REPOSITORY_ROOT.glob(pattern))

    entries: List[Dict[str, str]] = []
    for path in sorted({candidate.resolve() for candidate in candidates}):
        entries.append(
            {
                "path": str(path.relative_to(REPOSITORY_ROOT)),
                "sha256": sha256_bytes(path.read_bytes()),
            }
        )
    canonical = json.dumps(
        entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(canonical), entries


def selected_headers(headers: Iterable[Tuple[str, str]]) -> Dict[str, str]:
    """Keep stable, non-sensitive response headers in the evidence bundle."""

    allowed = {
        "cache-control",
        "content-length",
        "content-security-policy",
        "content-type",
        "referrer-policy",
        "x-content-type-options",
    }
    return {
        name.lower(): value
        for name, value in headers
        if name.lower() in allowed
    }


def http_exchange(
    host: str,
    port: int,
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    *,
    expect_json: bool = True,
    timeout: float = 5.0,
) -> Dict[str, Any]:
    """Send one genuine HTTP/1.1 request through a loopback TCP socket."""

    body: Optional[str] = None
    request_headers = {
        "Accept": "application/json" if expect_json else "text/html",
        "Connection": "close",
        "Host": f"{host}:{port}",
    }
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        request_headers["Content-Type"] = "application/json"
        request_headers["Content-Length"] = str(len(body.encode("utf-8")))

    started = time.monotonic()
    connection = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        raw_body = response.read()
        response_headers = selected_headers(response.getheaders())
        status = response.status
        reason = response.reason
    finally:
        connection.close()

    elapsed_ms = round((time.monotonic() - started) * 1000, 3)
    if expect_json:
        try:
            response_body: Any = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Expected JSON from {method} {path}, received invalid JSON"
            ) from error
    else:
        response_body = raw_body.decode("utf-8")

    return {
        "request": {
            "transport": "loopback TCP HTTP/1.1",
            "method": method,
            "path": path,
            "headers": request_headers,
            "body": payload,
        },
        "response": {
            "http_status": status,
            "reason": reason,
            "headers": response_headers,
            "body": response_body,
            "elapsed_ms": elapsed_ms,
        },
    }


def equality_assertion(actual: Any, expected: Any, label: str) -> Dict[str, Any]:
    return {
        "assertion": label,
        "expected": expected,
        "actual": actual,
        "result": "PASS" if actual == expected else "FAIL",
    }


def condition_assertion(condition: bool, label: str) -> Dict[str, Any]:
    return {
        "assertion": label,
        "expected": True,
        "actual": bool(condition),
        "result": "PASS" if condition else "FAIL",
    }


def assertions_pass(assertions: Iterable[Dict[str, Any]]) -> bool:
    return all(assertion["result"] == "PASS" for assertion in assertions)


def persist_exchange(path: Path, exchange: Dict[str, Any]) -> None:
    write_json(path, exchange)


def database_counts(database: RxCareDatabase) -> Dict[str, int]:
    with database.connection() as connection:
        prescription_count = int(
            connection.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0]
        )
        audit_count = int(
            connection.execute("SELECT COUNT(*) FROM validation_events").fetchone()[0]
        )
        accepted_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM validation_events WHERE outcome = 'ACCEPTED'"
            ).fetchone()[0]
        )
        rejected_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM validation_events WHERE outcome = 'REJECTED'"
            ).fetchone()[0]
        )
    return {
        "prescriptions": prescription_count,
        "validation_events": audit_count,
        "accepted_events": accepted_count,
        "rejected_events": rejected_count,
    }


def audit_assertions(
    audit_exchange: Dict[str, Any], expected_outcome: str, expected_reason: Any
) -> List[Dict[str, Any]]:
    response = audit_exchange["response"]
    body = response["body"]
    events = body.get("events", []) if isinstance(body, dict) else []
    assertions = [
        equality_assertion(response["http_status"], 200, "audit HTTP status"),
        equality_assertion(len(events), 1, "exactly one audit event"),
    ]
    if len(events) == 1 and isinstance(events[0], dict):
        event = events[0]
        assertions.extend(
            [
                equality_assertion(
                    sorted(event),
                    sorted(ALLOWED_AUDIT_FIELDS),
                    "approved audit fields only",
                ),
                equality_assertion(
                    event.get("outcome"), expected_outcome, "audit outcome"
                ),
                equality_assertion(
                    event.get("reason_code"), expected_reason, "audit reason code"
                ),
                condition_assertion(
                    FORBIDDEN_AUDIT_FIELDS.isdisjoint(event),
                    "no patient, medication, or dosage fields in audit event",
                ),
            ]
        )
    else:
        assertions.append(
            condition_assertion(False, "audit event structure is inspectable")
        )
    return assertions


def execute_ui_workflow_case(
    host: str,
    port: int,
    database: RxCareDatabase,
    run_directory: Path,
    spec: Dict[str, Any],
    timeout: float,
) -> Dict[str, Any]:
    """Execute one UI-equivalent submit/canonical/audit workflow."""

    case_id = str(spec["case_id"])
    case_directory = run_directory / "ui-cases" / case_id
    payload = dict(spec["payload"])
    record_id = str(payload["record_id"])
    before = database_counts(database)

    submission = http_exchange(
        host,
        port,
        "POST",
        "/api/v1/prescriptions",
        payload,
        timeout=timeout,
    )
    encoded_record_id = quote(record_id, safe="")
    canonical = http_exchange(
        host,
        port,
        "GET",
        f"/api/v1/prescriptions/{encoded_record_id}",
        timeout=timeout,
    )
    audit = http_exchange(
        host,
        port,
        "GET",
        f"/api/v1/audit-events?record_id={encoded_record_id}",
        timeout=timeout,
    )
    after = database_counts(database)

    persist_exchange(case_directory / "request-response.json", submission)
    write_json(case_directory / "request.json", submission["request"])
    write_json(case_directory / "response.json", submission["response"])
    persist_exchange(case_directory / "canonical-record-check.json", canonical)
    persist_exchange(case_directory / "audit-check.json", audit)
    write_json(
        case_directory / "database-counts.json",
        {"before": before, "after": after},
    )

    submission_response = submission["response"]
    response_body = submission_response["body"]
    canonical_response = canonical["response"]
    expected_status = int(spec["expected_http_status"])
    expected_outcome = str(spec["expected_outcome"])
    expected_reason = spec["expected_reason_code"]
    expected_canonical_status = int(spec["expected_canonical_status"])
    assertions = [
        equality_assertion(
            submission_response["http_status"],
            expected_status,
            "submission HTTP status",
        ),
        equality_assertion(
            response_body.get("status"), expected_outcome, "validation outcome"
        ),
        equality_assertion(
            response_body.get("reason_code"), expected_reason, "validation reason code"
        ),
        equality_assertion(
            canonical_response["http_status"],
            expected_canonical_status,
            "canonical lookup HTTP status",
        ),
        equality_assertion(
            after["validation_events"] - before["validation_events"],
            1,
            "one audit row added",
        ),
    ]

    if expected_outcome == "REJECTED":
        assertions.extend(
            [
                equality_assertion(
                    response_body.get("message"),
                    "Dosage is required",
                    "visible validation message",
                ),
                equality_assertion(
                    after["prescriptions"] - before["prescriptions"],
                    0,
                    "no canonical row added",
                ),
            ]
        )
    else:
        canonical_body = canonical_response["body"].get("prescription", {})
        assertions.extend(
            [
                equality_assertion(
                    response_body.get("message"),
                    "Prescription accepted",
                    "visible acceptance message",
                ),
                equality_assertion(
                    after["prescriptions"] - before["prescriptions"],
                    1,
                    "one canonical row added",
                ),
                equality_assertion(
                    canonical_body.get("record_id"), record_id, "canonical record ID"
                ),
                equality_assertion(
                    canonical_body.get("patient_ref"),
                    payload["patient_ref"],
                    "canonical synthetic patient reference",
                ),
                equality_assertion(
                    canonical_body.get("medication_name"),
                    payload["medication_name"],
                    "canonical synthetic medication",
                ),
                equality_assertion(
                    canonical_body.get("dosage_instruction"),
                    payload["dosage_instruction"],
                    "canonical dosage",
                ),
            ]
        )

    assertions.extend(audit_assertions(audit, expected_outcome, expected_reason))
    result = "PASS" if assertions_pass(assertions) else "FAIL"
    write_json(
        case_directory / "assertions.json",
        {
            "case_id": case_id,
            "jira_key": spec["jira_key"],
            "title": spec["title"],
            "execution_mode": "live loopback HTTP; browser-equivalent request chain",
            "result": result,
            "assertions": assertions,
        },
    )
    return {
        "case_id": case_id,
        "jira_key": spec["jira_key"],
        "title": spec["title"],
        "result": result,
        "submission_http_status": submission_response["http_status"],
        "canonical_http_status": canonical_response["http_status"],
        "audit_http_status": audit["response"]["http_status"],
    }


def ui_case_specs() -> List[Dict[str, Any]]:
    return [
        {
            "case_id": "UI-TC-01",
            "jira_key": "RXQA-6",
            "title": "Empty dosage is rejected",
            "payload": {
                "record_id": "SYN-UI-TC-01",
                "patient_ref": "SYN-PAT-UI-01",
                "medication_name": "Synthetic Medicine Alpha",
                "dosage_instruction": "",
            },
            "expected_http_status": 422,
            "expected_outcome": "REJECTED",
            "expected_reason_code": "DOSAGE_REQUIRED",
            "expected_canonical_status": 404,
        },
        {
            "case_id": "UI-TC-02",
            "jira_key": "RXQA-7",
            "title": "Whitespace-only dosage is rejected",
            "payload": {
                "record_id": "SYN-UI-TC-02",
                "patient_ref": "SYN-PAT-UI-02",
                "medication_name": "Synthetic Medicine Beta",
                "dosage_instruction": "   ",
            },
            "expected_http_status": 422,
            "expected_outcome": "REJECTED",
            "expected_reason_code": "DOSAGE_REQUIRED",
            "expected_canonical_status": 404,
        },
        {
            "case_id": "UI-TC-03",
            "jira_key": "RXQA-8",
            "title": "Valid dosage is accepted and persisted",
            "payload": {
                "record_id": "SYN-UI-TC-03",
                "patient_ref": "SYN-PAT-UI-03",
                "medication_name": "Synthetic Medicine Gamma",
                "dosage_instruction": "Take one synthetic unit once daily after food",
            },
            "expected_http_status": 201,
            "expected_outcome": "ACCEPTED",
            "expected_reason_code": None,
            "expected_canonical_status": 200,
        },
        {
            "case_id": "UI-TC-04",
            "jira_key": "RXQA-9",
            "title": "Rejected attempt creates one privacy-safe audit event",
            "payload": {
                "record_id": "SYN-UI-TC-04",
                "patient_ref": "SYN-PAT-UI-04",
                "medication_name": "Synthetic Medicine Delta",
                "dosage_instruction": "",
            },
            "expected_http_status": 422,
            "expected_outcome": "REJECTED",
            "expected_reason_code": "DOSAGE_REQUIRED",
            "expected_canonical_status": 404,
        },
    ]


def capture_health_and_ui(
    host: str, port: int, run_directory: Path, timeout: float
) -> Tuple[bool, Dict[str, Any]]:
    health = http_exchange(host, port, "GET", "/health", timeout=timeout)
    health_assertions = [
        equality_assertion(
            health["response"]["http_status"], 200, "health HTTP status"
        ),
        equality_assertion(
            health["response"]["body"].get("status"), "ok", "health status"
        ),
        equality_assertion(
            health["response"]["body"].get("app_version"),
            APP_VERSION,
            "health app version",
        ),
    ]
    write_json(
        run_directory / "health.json",
        {**health, "assertions": health_assertions},
    )

    ui = http_exchange(
        host, port, "GET", "/", expect_json=False, timeout=timeout
    )
    html = ui["response"].pop("body")
    encoded_html = html.encode("utf-8")
    markers = {
        "prescription_form": 'id="prescription-form"' in html,
        "submit_api_call": 'fetchJson("/api/v1/prescriptions"' in html,
        "canonical_api_call": "/api/v1/prescriptions/" in html,
        "audit_api_call": "/api/v1/audit-events?record_id=" in html,
        "synthetic_data_notice": "Synthetic data only." in html,
        "app_version": f"Prototype v{APP_VERSION}" in html,
    }
    ui["response"].update(
        {
            "body_sha256": sha256_bytes(encoded_html),
            "body_bytes": len(encoded_html),
            "required_markers": markers,
            "body_capture": (
                "HTML intentionally fingerprinted rather than duplicated; "
                "source is src/rxcare/ui.py"
            ),
        }
    )
    ui_assertions = [
        equality_assertion(ui["response"]["http_status"], 200, "UI HTTP status"),
        condition_assertion(all(markers.values()), "all required UI markers present"),
    ]
    write_json(
        run_directory / "ui-route.json",
        {**ui, "assertions": ui_assertions},
    )
    return (
        assertions_pass(health_assertions) and assertions_pass(ui_assertions),
        {"health": health, "ui_markers": markers},
    )


def capture_quality_checks(
    host: str,
    port: int,
    database: RxCareDatabase,
    run_directory: Path,
    timeout: float,
) -> Tuple[bool, Dict[str, Any]]:
    network = http_exchange(
        host, port, "GET", "/api/v1/quality-checks", timeout=timeout
    )
    direct_checks = database.quality_checks()
    direct_audit_summary = database.audit_summary()
    findings = {
        str(row["check_name"]): int(row["finding_count"])
        for row in direct_checks
    }
    audit_counts = {
        str(row["outcome"]): int(row["event_count"])
        for row in direct_audit_summary
    }
    assertions = [
        equality_assertion(
            network["response"]["http_status"], 200, "quality endpoint status"
        ),
        equality_assertion(
            network["response"]["body"].get("prescription_checks"),
            direct_checks,
            "HTTP and direct SQL prescription checks agree",
        ),
        equality_assertion(
            network["response"]["body"].get("audit_summary"),
            direct_audit_summary,
            "HTTP and direct SQL audit summary agree",
        ),
        condition_assertion(
            bool(findings) and all(count == 0 for count in findings.values()),
            "all prescription quality finding counts are zero",
        ),
        equality_assertion(audit_counts.get("ACCEPTED", 0), 1, "accepted audit count"),
        equality_assertion(audit_counts.get("REJECTED", 0), 3, "rejected audit count"),
    ]
    payload = {
        "execution_method": (
            "existing sql/quality_checks.sql views queried directly and through "
            "GET /api/v1/quality-checks"
        ),
        "sql_source": "sql/quality_checks.sql",
        "sql_source_sha256": sha256_bytes(
            (REPOSITORY_ROOT / "sql" / "quality_checks.sql").read_bytes()
        ),
        "network_exchange": network,
        "direct_sql": {
            "prescription_checks": direct_checks,
            "audit_summary": direct_audit_summary,
        },
        "result": "PASS" if assertions_pass(assertions) else "FAIL",
        "assertions": assertions,
    }
    write_json(run_directory / "quality_checks.json", payload)
    return assertions_pass(assertions), payload


def capture_database_counts(
    run_directory: Path, before: Dict[str, int], after: Dict[str, int]
) -> Tuple[bool, Dict[str, Any]]:
    expected_after = {
        "prescriptions": 1,
        "validation_events": 4,
        "accepted_events": 1,
        "rejected_events": 3,
    }
    assertions = [
        equality_assertion(
            before,
            {
                "prescriptions": 0,
                "validation_events": 0,
                "accepted_events": 0,
                "rejected_events": 0,
            },
            "fresh database begins empty",
        ),
        equality_assertion(after, expected_after, "post-run database counts"),
    ]
    payload = {
        "before": before,
        "after": after,
        "expected_after": expected_after,
        "result": "PASS" if assertions_pass(assertions) else "FAIL",
        "assertions": assertions,
    }
    write_json(run_directory / "database-counts.json", payload)
    return assertions_pass(assertions), payload


def run_regression_suite(run_directory: Path, skip: bool) -> Dict[str, Any]:
    if skip:
        payload = {
            "status": "SKIPPED_BY_EXPLICIT_OPTION",
            "command": None,
            "return_code": None,
        }
        write_json(run_directory / "regression_status.json", payload)
        return payload

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPOSITORY_ROOT / "src")
    environment["PYTHONPYCACHEPREFIX"] = "/tmp/rxcare-ui-evidence-pycache"
    junit_path = run_directory / "junit.xml"
    command = [
        sys.executable,
        "scripts/run_tests.py",
        "--junit",
        str(junit_path),
    ]
    process = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    output = process.stdout
    if process.stderr:
        output += "\n[stderr]\n" + process.stderr
    (run_directory / "automated_test_output.txt").write_text(
        output, encoding="utf-8"
    )
    payload = {
        "status": "PASS" if process.returncode == 0 else "FAIL",
        "command": (
            "PYTHONPATH=src python3 scripts/run_tests.py "
            "--junit <run>/junit.xml"
        ),
        "return_code": process.returncode,
    }
    write_json(run_directory / "regression_status.json", payload)
    return payload


def create_manifest(run_directory: Path) -> None:
    lines = []
    for path in sorted(run_directory.rglob("*")):
        if not path.is_file() or path.name == "sha256_manifest.txt":
            continue
        digest = sha256_bytes(path.read_bytes())
        lines.append(f"{digest}  {path.relative_to(run_directory)}")
    (run_directory / "sha256_manifest.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def create_blocked_run(
    run_directory: Path,
    run_id: str,
    started_at: str,
    bind_error: OSError,
    loopback_host: str,
    source_control_context: Dict[str, Any],
) -> None:
    """Record a truthful non-PASS bundle when loopback binding is denied."""

    run_directory.mkdir(parents=True)
    source_tree_digest, source_entries = source_manifest()
    metadata: Dict[str, Any] = {
        "run_id": run_id,
        "started_at_utc": started_at,
        "completed_at_utc": utc_timestamp(),
        "app_version": APP_VERSION,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "source_tree_sha256": source_tree_digest,
        "database": "fresh temporary SQLite database; removed after blocked setup",
        "data_classification": "synthetic only; no case payload was submitted",
        "http_execution_mode": "NOT EXECUTED — loopback bind blocked",
        "loopback_host": loopback_host,
        "tcp_listener_executed": False,
        "ui_route_requested": False,
        "browser_javascript_executed": False,
        "browser_screenshots_captured": False,
        "overall_result": "BLOCKED",
        "command": (
            "PYTHONPATH=src python3 scripts/capture_ui_execution_evidence.py"
        ),
        **source_control_context,
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
    write_json(
        run_directory / "loopback_bind_status.json",
        {
            "status": "BLOCKED",
            "error_type": type(bind_error).__name__,
            "errno": bind_error.errno,
            "safe_diagnostic": (
                "The execution environment denied creation of the required "
                "loopback TCP listener. No network request was executed."
            ),
            "retry_guidance": (
                "Run the same command on a workstation that permits binding "
                "an ephemeral 127.0.0.1 port."
            ),
        },
    )
    write_json(
        run_directory / "browser_evidence_status.json",
        {
            "status": "NOT_EXECUTED_ENVIRONMENT_BLOCKED",
            "interpretation": (
                "No UI route, browser DOM interaction, or screenshot is claimed."
            ),
        },
    )
    write_json(
        run_directory / "quality_checks.json",
        {
            "status": "NOT_EXECUTED_ENVIRONMENT_BLOCKED",
            "claim": "No SQL quality-check result is claimed for this blocked run.",
        },
    )
    write_json(
        run_directory / "candidate_risk_RXQA-10.json",
        {
            "issue": "RXQA-10",
            "version": APP_VERSION,
            "status": "NOT_EXECUTED_ENVIRONMENT_BLOCKED",
            "interpretation": (
                "This blocked run provides no new evidence for or against the risk."
            ),
        },
    )
    report = f"""# RxCare v{APP_VERSION} — Phase 2 loopback execution report

## Result

**BLOCKED — NOT EXECUTED.**

- Run ID: `{run_id}`
- UTC attempt time: `{started_at}`
- Required transport: genuine TCP HTTP/1.1 on a loopback-only port
- Listener status: the execution environment denied the loopback bind
- Submitted records: none
- Browser/screenshots: not executed

No UI-TC case, health request, SQL result, regression result, or RXQA-10
determination is presented as executed by this run. This bundle exists to make
the environmental constraint auditable; it is not PASS evidence and must not
be substituted for a workstation loopback run.

## How to retry

From the repository root on a workstation that permits `127.0.0.1` listeners:

```text
PYTHONPATH=src python3 scripts/capture_ui_execution_evidence.py
```

The script will use an OS-assigned ephemeral port, a fresh temporary SQLite
database, synthetic data only, and will exit non-zero unless every network,
case, count, SQL, and regression assertion passes.
"""
    (run_directory / "TEST_EXECUTION_REPORT.md").write_text(
        report, encoding="utf-8"
    )
    create_manifest(run_directory)


def create_report(
    run_directory: Path,
    metadata: Dict[str, Any],
    case_summaries: List[Dict[str, Any]],
    infrastructure_passed: bool,
    counts_passed: bool,
    quality_passed: bool,
    regression: Dict[str, Any],
) -> bool:
    cases_passed = all(case["result"] == "PASS" for case in case_summaries)
    regression_passed = regression["status"] == "PASS"
    overall_passed = all(
        (
            infrastructure_passed,
            cases_passed,
            counts_passed,
            quality_passed,
            regression_passed,
        )
    )
    rows = "\n".join(
        "| {case_id} | {jira_key} | {title} | {result} |".format(**case)
        for case in case_summaries
    )
    report = f"""# RxCare v{APP_VERSION} — Phase 2 loopback execution report

## Result

**{'PASS' if overall_passed else 'FAIL'}** for the live loopback HTTP workflow run.

- Run ID: `{metadata['run_id']}`
- UTC execution time: `{metadata['started_at_utc']}`
- Transport: genuine TCP HTTP/1.1 on an ephemeral loopback-only port
- Database: fresh temporary SQLite database, deleted after sanitized export
- Data classification: synthetic only
- Browser status: JavaScript/DOM interaction and screenshots were **not** executed by this script

## Executed UI-workflow HTTP cases

| Case | Jira | Purpose | Result |
|---|---|---|---|
{rows}

For each case, the harness followed the network sequence used by the browser UI:
`POST /api/v1/prescriptions`, canonical record lookup, and audit-event lookup.
This proves the real loopback listener and UI-facing HTTP workflow. It does not
by itself prove rendering, click behaviour, client-side JavaScript, accessibility,
or visual presentation; those require separately labelled browser evidence.

## Integrity and quality controls

- UI and health routes: `{'PASS' if infrastructure_passed else 'FAIL'}`
- Fresh-database pre/post counts: `{'PASS' if counts_passed else 'FAIL'}`
- SQL quality checks and HTTP/direct-SQL agreement: `{'PASS' if quality_passed else 'FAIL'}`
- Automated regression suite: `{regression['status']}`
- SHA-256 manifest: `sha256_manifest.txt`
- Exact source fingerprint: `source_manifest.json`

## RXQA-10 status

`UI-TC-02` tested whitespace-only dosage over the live loopback listener. The
machine-readable determination is in `candidate_risk_RXQA-10.json`. A rejected
HTTP 422 response, absent canonical row, and one privacy-safe rejection event
support **NOT_REPRODUCED**; no candidate defect is presented as confirmed.

## Scope boundary

This run demonstrates a local educational prototype and synthetic-data QA
evidence. It does not demonstrate authentication, deployment, clinical
validation, regulatory compliance, medical advice, AI capability, or
production readiness. `browser_evidence_status.json` intentionally prevents
the loopback harness from being mistaken for browser screenshot evidence.
"""
    (run_directory / "TEST_EXECUTION_REPORT.md").write_text(
        report, encoding="utf-8"
    )
    return overall_passed


def run_capture(args: argparse.Namespace) -> Tuple[Path, bool]:
    try:
        address = ipaddress.ip_address(args.host)
    except ValueError as error:
        raise ValueError("--host must be a numeric loopback address") from error
    if not address.is_loopback:
        raise ValueError("--host must be loopback-only (for example 127.0.0.1)")

    started_at = utc_timestamp()
    run_id = args.run_id or (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + f"-ui-loopback-v{APP_VERSION}"
    )
    output_root = args.output_root.resolve()
    run_directory = output_root / run_id
    if run_directory.exists():
        raise FileExistsError(f"Run directory already exists: {run_directory}")
    # This must happen before either the PASS/FAIL run or a BLOCKED bundle is
    # created, otherwise evidence output itself would alter Git dirty state.
    source_control_context = capture_source_control_context(
        REPOSITORY_ROOT, args.source_commit
    )

    with tempfile.TemporaryDirectory(prefix="rxcare-ui-evidence-") as temp_dir:
        database_path = Path(temp_dir) / "rxcare-ui-run.db"
        # Complete application/database initialization before the narrow bind
        # error boundary. An OSError here is an application failure and must
        # never be labelled as an environment-blocked loopback listener.
        database = RxCareDatabase(database_path)
        service = PrescriptionService(database)
        try:
            server = create_bound_server(service, args.host, args.port)
        except OSError as error:
            create_blocked_run(
                run_directory,
                run_id,
                started_at,
                error,
                args.host,
                source_control_context,
            )
            raise LoopbackBindError(
                "The environment blocked the required loopback TCP listener; "
                "no live-network PASS evidence was created. Blocked evidence: "
                f"{run_directory}"
            ) from error

        # Use a second repository object for direct read-only verification of the
        # same temporary SQLite file. The server owns its service instance.
        verification_database = RxCareDatabase(database_path)
        bound_host = str(server.server_address[0])
        bound_port = int(server.server_address[1])
        thread = threading.Thread(
            target=server.serve_forever,
            name="rxcare-ui-evidence-server",
            daemon=True,
        )
        thread.start()

        run_directory.mkdir(parents=True)
        source_tree_digest, source_entries = source_manifest()
        metadata: Dict[str, Any] = {
            "run_id": run_id,
            "started_at_utc": started_at,
            "app_version": APP_VERSION,
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "source_tree_sha256": source_tree_digest,
            "database": "fresh temporary SQLite database; deleted after export",
            "data_classification": "synthetic only",
            "http_execution_mode": "live loopback TCP HTTP/1.1",
            "loopback_host": bound_host,
            "ephemeral_port_used": True,
            "tcp_listener_executed": True,
            "ui_route_requested": True,
            "browser_javascript_executed": False,
            "browser_screenshots_captured": False,
            "command": (
                "PYTHONPATH=src python3 "
                "scripts/capture_ui_execution_evidence.py"
            ),
            **source_control_context,
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
        write_json(
            run_directory / "browser_evidence_status.json",
            {
                "status": "NOT_CAPTURED_BY_THIS_SCRIPT",
                "interpretation": (
                    "The UI HTML route and its live network workflow were exercised, "
                    "but no browser DOM interaction or screenshot is claimed."
                ),
                "separate_capture_required_for": [
                    "rendering",
                    "field interaction",
                    "client-side JavaScript",
                    "visible status and error states",
                    "visual accessibility review",
                ],
            },
        )

        case_summaries: List[Dict[str, Any]] = []
        infrastructure_passed = False
        counts_passed = False
        quality_passed = False
        overall_passed = False
        regression: Dict[str, Any] = {"status": "NOT_RUN"}
        before = database_counts(verification_database)
        try:
            infrastructure_passed, _ = capture_health_and_ui(
                bound_host, bound_port, run_directory, args.timeout
            )
            for spec in ui_case_specs():
                case_summaries.append(
                    execute_ui_workflow_case(
                        bound_host,
                        bound_port,
                        verification_database,
                        run_directory,
                        spec,
                        args.timeout,
                    )
                )
            after = database_counts(verification_database)
            counts_passed, _ = capture_database_counts(
                run_directory, before, after
            )
            quality_passed, _ = capture_quality_checks(
                bound_host,
                bound_port,
                verification_database,
                run_directory,
                args.timeout,
            )
            all_events: List[Dict[str, Any]] = []
            for spec in ui_case_specs():
                record_id = str(spec["payload"]["record_id"])
                all_events.extend(
                    verification_database.get_audit_events(record_id)
                )
            write_json(run_directory / "sanitized_audit_events.json", all_events)

            whitespace_case = next(
                case for case in case_summaries if case["case_id"] == "UI-TC-02"
            )
            rxqa_10_status = (
                "NOT_REPRODUCED"
                if whitespace_case["result"] == "PASS"
                else "INCONCLUSIVE_OR_REPRODUCED"
            )
            write_json(
                run_directory / "candidate_risk_RXQA-10.json",
                {
                    "issue": "RXQA-10",
                    "version": APP_VERSION,
                    "status": rxqa_10_status,
                    "evidence_case": "UI-TC-02",
                    "execution_mode": "live loopback TCP HTTP/1.1",
                    "interpretation": (
                        "Whitespace-only dosage was rejected with no canonical "
                        "row and one privacy-safe audit event."
                        if rxqa_10_status == "NOT_REPRODUCED"
                        else "The expected rejection chain was not fully observed; "
                        "inspect UI-TC-02 before assigning defect status."
                    ),
                },
            )
        except Exception as error:
            write_json(
                run_directory / "execution_error.json",
                {
                    "status": "INCOMPLETE",
                    "error_type": type(error).__name__,
                    "message": str(error),
                    "claim": "No PASS claim is made for the interrupted steps.",
                },
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        regression = run_regression_suite(run_directory, args.skip_tests)
        overall_passed = create_report(
            run_directory,
            metadata,
            case_summaries,
            infrastructure_passed,
            counts_passed,
            quality_passed,
            regression,
        )
        metadata["completed_at_utc"] = utc_timestamp()
        metadata["overall_result"] = "PASS" if overall_passed else "FAIL"
        write_json(run_directory / "run_metadata.json", metadata)
        create_manifest(run_directory)
        return run_directory, overall_passed


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Capture synthetic RxCare UI-workflow evidence over a genuine "
            "loopback TCP listener."
        )
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="parent directory for the immutable run folder",
    )
    parser.add_argument(
        "--run-id",
        help="explicit run directory name (default: UTC timestamp plus version)",
    )
    parser.add_argument(
        "--source-commit",
        help=(
            "source/test Git commit for a detached staging copy; must match "
            "HEAD when Git metadata is available"
        ),
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="loopback port; 0 requests an ephemeral OS-assigned port",
    )
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="skip the regression suite (the evidence report will say so)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        run_directory, passed = run_capture(args)
    except LoopbackBindError as error:
        print(f"LOOPBACK_BIND_FAILED: {error}", file=sys.stderr)
        return 2
    except (FileExistsError, ValueError) as error:
        print(f"CONFIGURATION_ERROR: {error}", file=sys.stderr)
        return 2
    print(run_directory)
    if not passed:
        print(
            "Evidence run completed with FAIL/INCOMPLETE status; inspect the report.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
