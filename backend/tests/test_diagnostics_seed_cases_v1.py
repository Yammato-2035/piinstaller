import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.diagnostics.evidence_store import load_evidence_records


class TestDiagnosticsSeedCasesV1(unittest.TestCase):
    def test_required_seed_coverage(self):
        records = load_evidence_records()
        ids = {r.id for r in records}
        expected = {
            "EVID-2026-001",
            "EVID-2026-002",
            "EVID-2026-003",
            "EVID-2026-004",
            "EVID-2026-005",
            "EVID-2026-006",
            "EVID-2026-007",
            "EVID-2026-008",
            "EVID-2026-009",
            "EVID-2026-010",
        }
        self.assertTrue(expected.issubset(ids))


if __name__ == "__main__":
    unittest.main()
