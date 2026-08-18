"""Guard packaged SQL resources against divergence from reviewable SQL."""

import unittest
from pathlib import Path

from rxcare.database import sql_resource_text


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class SqlResourceDriftTests(unittest.TestCase):
    def test_packaged_sql_matches_repository_sql_byte_for_byte(self) -> None:
        for filename in ("schema.sql", "quality_checks.sql"):
            with self.subTest(filename=filename):
                reviewable_sql = (
                    REPOSITORY_ROOT / "sql" / filename
                ).read_text(encoding="utf-8")
                self.assertEqual(sql_resource_text(filename), reviewable_sql)

    def test_package_data_configuration_includes_sql_resources(self) -> None:
        configuration = (REPOSITORY_ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn("[tool.setuptools.package-data]", configuration)
        self.assertIn('rxcare = ["sql/*.sql"]', configuration)


if __name__ == "__main__":
    unittest.main()
