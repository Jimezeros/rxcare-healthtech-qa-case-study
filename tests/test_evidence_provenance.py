"""Regression tests for evidence/source revision provenance."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rxcare.provenance import capture_source_control_context
from scripts import capture_execution_evidence as api_evidence


class EvidenceProvenanceTests(unittest.TestCase):
    def test_detached_copy_accepts_explicit_source_commit_truthfully(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            with mock.patch.dict(
                os.environ,
                {"RXCARE_SOURCE_COMMIT": "A" * 40},
                clear=False,
            ):
                context = capture_source_control_context(
                    Path(temp_directory)
                )

        self.assertEqual(context["source_test_commit_sha"], "a" * 40)
        self.assertEqual(
            context["source_test_commit_origin"], "explicit_override"
        )
        self.assertEqual(
            context["source_test_working_tree"],
            "not available in this staging copy",
        )
        self.assertTrue(
            context["source_test_context_captured_before_evidence"]
        )
        self.assertIsNone(context["final_release_commit_sha"])
        self.assertIsNone(context["final_release_tag"])

    def test_invalid_explicit_source_commit_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            with self.assertRaisesRegex(ValueError, "40- or 64-character"):
                capture_source_control_context(
                    Path(temp_directory), explicit_commit="not-a-commit"
                )

    def test_api_runner_captures_context_before_creating_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            run_directory = Path(temp_directory) / "provenance-test-run"
            expected = {
                "source_test_commit_sha": "b" * 40,
                "source_test_working_tree": "clean",
            }

            def capture_before_output(
                _repository_root, explicit_source_commit
            ):
                self.assertFalse(run_directory.exists())
                self.assertEqual(explicit_source_commit, "b" * 40)
                return expected

            with mock.patch.object(
                api_evidence,
                "capture_source_control_context",
                side_effect=capture_before_output,
            ):
                actual = api_evidence.prepare_run_directory(
                    run_directory, "b" * 40
                )

            self.assertTrue(run_directory.is_dir())
            self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
