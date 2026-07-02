"""Diagnostics hardware DB schema tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


class DiagnosticsHardwareDbSchemaV1Tests(unittest.TestCase):
    def test_schema_has_hardware_key(self) -> None:
        path = Path(__file__).resolve().parents[2] / "docs/architecture/hardware_db_schema_v1.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        blob = json.dumps(schema)
        self.assertIn("hardware_key", blob)

    def test_sql_schema_exists(self) -> None:
        sql = Path(__file__).resolve().parents[2] / "docs/architecture/sql/diagnostics_hardware_db_schema_v1.sql"
        self.assertTrue(sql.is_file())
        self.assertIn("hardware_profiles", sql.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
