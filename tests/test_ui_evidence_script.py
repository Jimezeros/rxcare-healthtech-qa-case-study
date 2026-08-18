"""Focused tests for the Phase 2 loopback evidence harness."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import capture_ui_execution_evidence as evidence


class UiEvidenceScriptTests(unittest.TestCase):
    def test_case_catalog_is_exact_and_synthetic(self) -> None:
        cases = evidence.ui_case_specs()

        self.assertEqual(
            [case["case_id"] for case in cases],
            ["UI-TC-01", "UI-TC-02", "UI-TC-03", "UI-TC-04"],
        )
        self.assertEqual(
            [case["jira_key"] for case in cases],
            ["RXQA-6", "RXQA-7", "RXQA-8", "RXQA-9"],
        )
        for case in cases:
            payload = case["payload"]
            self.assertTrue(payload["record_id"].startswith("SYN-"))
            self.assertTrue(payload["patient_ref"].startswith("SYN-"))
            self.assertIn("Synthetic", payload["medication_name"])

    def test_bind_denial_creates_blocked_not_pass_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            output_root = Path(temp_directory)
            args = evidence.parse_args(
                [
                    "--output-root",
                    str(output_root),
                    "--run-id",
                    "blocked-test-run",
                ]
            )
            denied = PermissionError(1, "Operation not permitted")
            with mock.patch.object(
                evidence, "create_server", side_effect=denied
            ):
                with self.assertRaises(evidence.LoopbackBindError):
                    evidence.run_capture(args)

            run_directory = output_root / "blocked-test-run"
            metadata = json.loads(
                (run_directory / "run_metadata.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(metadata["overall_result"], "BLOCKED")
            self.assertFalse(metadata["tcp_listener_executed"])
            report = (run_directory / "TEST_EXECUTION_REPORT.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("**BLOCKED — NOT EXECUTED.**", report)
            self.assertNotIn("**PASS**", report)

            listed = {}
            for line in (
                run_directory / "sha256_manifest.txt"
            ).read_text(encoding="utf-8").splitlines():
                digest, relative_path = line.split("  ", 1)
                listed[relative_path] = digest
            actual = {
                str(path.relative_to(run_directory)): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
                for path in run_directory.rglob("*")
                if path.is_file() and path.name != "sha256_manifest.txt"
            }
            self.assertEqual(listed, actual)


if __name__ == "__main__":
    unittest.main()
