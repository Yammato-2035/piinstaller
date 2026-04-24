import json
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.diagnostics.registry import get_case_by_id


class TestHwTest1MatrixV1(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.matrix = json.loads(
            (root / "data/diagnostics/hw_test_1_matrix.json").read_text(encoding="utf-8")
        )

    def test_has_24_tests(self):
        tests = self.matrix.get("tests", [])
        self.assertEqual(len(tests), 24)

    def test_test_ids_unique_and_complete(self):
        tests = self.matrix.get("tests", [])
        ids = [row["test_id"] for row in tests]
        self.assertEqual(len(ids), len(set(ids)))
        expected = {f"HW1-{i:02d}" for i in range(1, 25)}
        self.assertEqual(set(ids), expected)

    def test_diagnosis_ids_exist(self):
        for row in self.matrix.get("tests", []):
            for did in row.get("possible_diagnosis_ids", []):
                self.assertIsNotNone(get_case_by_id(did), msg=f"unknown diagnosis id: {did}")

    def test_results_are_planned_only(self):
        allowed = {"planned", "passed", "failed", "inconclusive"}
        for row in self.matrix.get("tests", []):
            self.assertIn(row.get("result"), allowed)
            self.assertTrue(row.get("evidence_required"))


if __name__ == "__main__":
    unittest.main()
