#!/usr/bin/env python3
"""Run the standard-library test suite and emit a small JUnit XML report."""

import argparse
import sys
import time
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class RecordingResult(unittest.TextTestResult):
    """Text result that also records machine-readable test outcomes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started_at: Dict[str, float] = {}
        self.records: List[Dict[str, object]] = []

    def startTest(self, test):  # noqa: N802 - unittest API naming
        self.started_at[test.id()] = time.monotonic()
        super().startTest(test)

    def _record(self, test, status: str, detail: str = "") -> None:
        started = self.started_at.get(test.id(), time.monotonic())
        self.records.append(
            {
                "id": test.id(),
                "status": status,
                "detail": detail,
                "seconds": round(time.monotonic() - started, 6),
            }
        )

    def addSuccess(self, test):  # noqa: N802 - unittest API naming
        super().addSuccess(test)
        self._record(test, "passed")

    def addFailure(self, test, err):  # noqa: N802 - unittest API naming
        super().addFailure(test, err)
        self._record(test, "failed", self._exc_info_to_string(err, test))

    def addError(self, test, err):  # noqa: N802 - unittest API naming
        super().addError(test, err)
        self._record(test, "error", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):  # noqa: N802 - unittest API naming
        super().addSkip(test, reason)
        self._record(test, "skipped", reason)

    def addSubTest(self, test, subtest, err):  # noqa: N802 - unittest API naming
        super().addSubTest(test, subtest, err)
        if err is None:
            return
        status = (
            "failed"
            if issubclass(err[0], test.failureException)
            else "error"
        )
        started = self.started_at.get(test.id(), time.monotonic())
        self.records.append(
            {
                "id": subtest.id(),
                "status": status,
                "detail": self._exc_info_to_string(err, test),
                "seconds": round(time.monotonic() - started, 6),
            }
        )


def write_junit(path: Path, result: RecordingResult, elapsed: float) -> None:
    suite = ET.Element(
        "testsuite",
        {
            "name": "rxcare",
            "tests": str(result.testsRun),
            "failures": str(len(result.failures)),
            "errors": str(len(result.errors)),
            "skipped": str(len(result.skipped)),
            "time": f"{elapsed:.6f}",
        },
    )
    for record in result.records:
        test_id = str(record["id"])
        parts = test_id.rsplit(".", 1)
        case = ET.SubElement(
            suite,
            "testcase",
            {
                "classname": parts[0] if len(parts) == 2 else "rxcare",
                "name": parts[-1],
                "time": f"{float(record['seconds']):.6f}",
            },
        )
        if record["status"] == "failed":
            ET.SubElement(case, "failure").text = str(record["detail"])
        elif record["status"] == "error":
            ET.SubElement(case, "error").text = str(record["detail"])
        elif record["status"] == "skipped":
            ET.SubElement(case, "skipped").text = str(record["detail"])

    tree = ET.ElementTree(suite)
    ET.indent(tree, space="  ")
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--junit", type=Path, required=True)
    args = parser.parse_args()

    # ``python scripts/run_tests.py`` otherwise places only ``scripts/`` at the
    # front of sys.path.  The repository root is required for tests that import
    # the evidence modules as the ``scripts`` namespace package.
    root_text = str(REPOSITORY_ROOT)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    suite = unittest.defaultTestLoader.discover(
        str(REPOSITORY_ROOT / "tests"),
        top_level_dir=root_text,
    )
    runner = unittest.TextTestRunner(
        stream=sys.stdout,
        verbosity=2,
        resultclass=RecordingResult,
    )
    started = time.monotonic()
    result = runner.run(suite)
    elapsed = time.monotonic() - started
    assert isinstance(result, RecordingResult)
    write_junit(args.junit, result, elapsed)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
