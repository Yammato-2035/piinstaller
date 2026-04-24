import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.diagnostics.matcher import match_diagnoses
from core.diagnostics.models import DiagnosticsAnalyzeRequest


class TestDiagnosticsMatcherV1(unittest.TestCase):
    def test_hard_signal_priority(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={"manifest_present": False, "archive_corrupted": True},
        )
        hits = match_diagnoses(req)
        self.assertGreaterEqual(len(hits), 2)
        self.assertEqual(hits[0].id, "BACKUP-MANIFEST-001")
        self.assertEqual(hits[1].id, "BACKUP-ARCHIVE-002")

    def test_question_pattern_match(self):
        req = DiagnosticsAnalyzeRequest(question="Restore laeuft, aber SSH ist nicht erreichbar")
        hits = match_diagnoses(req)
        ids = [h.id for h in hits]
        self.assertIn("SSH-DISABLED-017", ids)


if __name__ == "__main__":
    unittest.main()
