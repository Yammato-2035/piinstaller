import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.diagnostics.evidence_store import load_evidence_records, evidence_summary_map
from core.diagnostics.runner import diagnosis_by_id


class TestDiagnosticsEvidenceMappingV1(unittest.TestCase):
    def test_seed_records_exist(self):
        rows = load_evidence_records()
        self.assertGreaterEqual(len(rows), 10)

    def test_confirmed_count_for_perm_group(self):
        summary = evidence_summary_map()
        item = summary.get("PERM-GROUP-008")
        self.assertIsNotNone(item)
        assert item is not None
        self.assertGreaterEqual(item.confirmed, 1)

    def test_diagnosis_detail_contains_evidence_counts(self):
        row = diagnosis_by_id("BACKUP-MANIFEST-001")
        self.assertIsNotNone(row)
        assert row is not None
        self.assertIn("evidence_counts", row)
        self.assertGreaterEqual(row["evidence_counts"]["confirmed"], 1)


if __name__ == "__main__":
    unittest.main()
