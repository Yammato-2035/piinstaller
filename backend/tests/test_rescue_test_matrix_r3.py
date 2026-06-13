"""Phase R.3: rescue_test_matrix contract tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


class TestRescueTestMatrixR3(unittest.TestCase):
    def test_matrix_has_20_entries(self) -> None:
        import core.rescue_test_matrix as tm

        entries = tm.build_rescue_test_matrix_entries()
        self.assertGreaterEqual(len(entries), 18)
        ids = {e["id"] for e in entries}
        self.assertIn("R3-BOOT-001", ids)
        self.assertIn("R3-NEXT-001", ids)

    def test_status_values_valid(self) -> None:
        import core.rescue_test_matrix as tm

        allowed = {"green", "yellow", "red", "gray", "blocked", "unknown"}
        for e in tm.build_rescue_test_matrix_entries():
            self.assertIn(e["status"], allowed)

    def test_document_shape(self) -> None:
        import core.rescue_test_matrix as tm

        doc = tm.build_rescue_test_matrix_document()
        self.assertEqual(doc["matrix_version"], 3)
        self.assertIn("status_counts", doc)


if __name__ == "__main__":
    unittest.main()
