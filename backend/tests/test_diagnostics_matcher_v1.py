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

    def test_verify_integrity_failed_signal(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={"code": "backup.verify_integrity_failed"},
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("VERIFY-STAGING-038", ids)

    def test_restore_failed_enospc_signal(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={"code": "backup.restore_failed", "stderr": "tar: write: No space left on device"},
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("RESTORE-TMPFS-007", ids)

    def test_memorymax_question_pattern(self):
        req = DiagnosticsAnalyzeRequest(question="Deep verify bricht ab, MemoryMax zu klein?")
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("SYSTEMD-MEMORYMAX-037", ids)


if __name__ == "__main__":
    unittest.main()
