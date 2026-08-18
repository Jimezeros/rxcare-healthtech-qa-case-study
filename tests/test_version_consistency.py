"""Release metadata must agree before evidence is generated."""

import re
import unittest
from pathlib import Path

from rxcare.version import APP_VERSION


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class VersionConsistencyTests(unittest.TestCase):
    def test_version_file_package_metadata_and_runtime_match(self) -> None:
        version_file = (REPOSITORY_ROOT / "VERSION").read_text(
            encoding="utf-8"
        ).strip()
        pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        match = re.search(
            r'^version\s*=\s*"([^"]+)"\s*$',
            pyproject,
            flags=re.MULTILINE,
        )

        self.assertIsNotNone(match, "pyproject.toml project version is missing")
        self.assertEqual(version_file, APP_VERSION)
        self.assertEqual(match.group(1), APP_VERSION)


if __name__ == "__main__":
    unittest.main()
