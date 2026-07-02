"""Diagnostics learning import contract tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


class DiagnosticsLearningImportContractV1Tests(unittest.TestCase):
    def test_schema_valid_json(self) -> None:
        path = Path(__file__).resolve().parents[2] / "docs/architecture/diagnostics_learning_import_contract_v1.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("$schema", schema)


if __name__ == "__main__":
    unittest.main()
