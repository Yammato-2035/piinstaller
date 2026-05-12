import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.diagnostics.matcher import match_diagnoses
from core.diagnostics.models import DiagnosticsAnalyzeRequest
from core.diagnostics.registry import get_catalog, get_case_by_id


class TestDiagnosticsMatcherHw1R01R04V1(unittest.TestCase):
    def test_catalog_contains_backup_source_perm_032(self):
        self.assertIsNotNone(get_case_by_id("BACKUP-SOURCE-PERM-032"))
        self.assertGreaterEqual(len(get_catalog()), 32)

    def test_match_backup_source_perm_by_code_and_details(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={
                "code": "backup.source_permission_denied",
                "details.diagnosis_id": "BACKUP-SOURCE-PERM-032",
                "unreadable_sources": "[{\"path\":\"/home/tester\"}]",
            },
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("BACKUP-SOURCE-PERM-032", ids)

    def test_match_systemd_nnp_by_api_code(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={
                "code": "backup.sudo_blocked_by_nnp",
            },
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("SYSTEMD-NNP-031", ids)

    def test_match_owner_mode_root_root_755(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={
                "mount_owner_mode": "drwxr-xr-x root:root 755 /mnt/setuphelfer/backups/test-run",
            },
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("OWNER-MODE-023", ids)

    def test_match_perm_group_by_probe_denied(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={
                "target_probe_error": "touch: Keine Berechtigung",
            },
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("PERM-GROUP-008", ids)

    def test_match_storage_protection_005_signal(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={"storage_protection": "storage-protection-005"},
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("STORAGE-PROTECTION-005", ids)

    def test_match_manifest_missing_signal(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={"manifest_present": "false"},
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("BACKUP-MANIFEST-001", ids)

    def test_match_archive_corrupted_signal(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={"archive_corrupted": "true"},
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("BACKUP-ARCHIVE-002", ids)

    def test_match_verify_hash_mismatch_signal(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={"verify_status": "hash_mismatch"},
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("BACKUP-HASH-003", ids)

    def test_match_restore_path_unsafe_signal(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={"restore_path_safe": "false"},
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("RESTORE-PATH-004", ids)


if __name__ == "__main__":
    unittest.main()
