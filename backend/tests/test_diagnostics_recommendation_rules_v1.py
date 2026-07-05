"""Diagnostics recommendation rules — human review required for new hardware."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


class DiagnosticsRecommendationRulesV1Tests(unittest.TestCase):
    def test_diagnostic_rule_human_review_flag(self) -> None:
        sql = Path(__file__).resolve().parents[2] / "docs/architecture/sql/diagnostics_hardware_db_schema_v1.sql"
        text = sql.read_text(encoding="utf-8")
        self.assertIn("review_required", text)
        self.assertIn("hardware_review_queue", text)


if __name__ == "__main__":
    unittest.main()
