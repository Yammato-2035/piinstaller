import json
import unittest
from pathlib import Path


class TestI18nBackupDiagKeysV1(unittest.TestCase):
    def test_de_en_have_fix3_and_diag_keys(self):
        root = Path(__file__).resolve().parents[2]
        de = json.loads((root / "frontend/src/locales/de.json").read_text(encoding="utf-8"))
        en = json.loads((root / "frontend/src/locales/en.json").read_text(encoding="utf-8"))

        required = [
            "backup.messages.source_permission_denied",
            "backup.messages.verify_archive_unreadable",
            "backup.messages.verify_integrity_failed",
            "backup.messages.restore_blocked_entries",
            "backup.messages.restore_target_missing",
            "backup.messages.restore_target_invalid",
            "backup.messages.restore_not_writable",
            "backup.messages.restore_success",
            "backup.messages.preview_private_tmp_hint",
            "backup.messages.list_timeout",
            "backup.messages.backup_target_not_writable",
            "diagnosis.codes.BACKUP-SOURCE-PERM-032.title",
            "diagnosis.codes.BACKUP-SOURCE-PERM-032.user_summary",
            "diagnosis.codes.SYSTEMD-NNP-031.title",
            "diagnosis.codes.PERM-GROUP-008.title",
            "diagnosis.codes.OWNER-MODE-023.title",
            "diagnosis.codes.BACKUP-MANIFEST-001.title",
            "diagnosis.codes.BACKUP-MANIFEST-001.user_summary",
            "diagnosis.codes.BACKUP-ARCHIVE-002.title",
            "diagnosis.codes.BACKUP-HASH-003.title",
            "diagnosis.codes.RESTORE-PATH-004.title",
            "diagnosis.codes.RESTORE-RUNTIME-006.title",
            "diagnosis.codes.RESTORE-RUNTIME-006.user_summary",
            "diagnosis.codes.STORAGE-PROTECTION-005.title",
        ]
        for k in required:
            self.assertIn(k, de, f"missing de key: {k}")
            self.assertIn(k, en, f"missing en key: {k}")
            self.assertTrue(str(de[k]).strip())
            self.assertTrue(str(en[k]).strip())


if __name__ == "__main__":
    unittest.main()
