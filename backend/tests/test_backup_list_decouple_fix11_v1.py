from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


class TestBackupListDecoupleFix11V1(unittest.TestCase):
    def test_backup_list_reads_index_instead_of_scanning_filesystem(self) -> None:
        app_py = _backend / "app.py"
        handlers_py = _backend / "core" / "backup_readonly_handlers.py"
        text = app_py.read_text(encoding="utf-8")
        list_block = handlers_py.read_text(encoding="utf-8")
        list_fn = list_block.split("async def list_backups", 1)[1]
        self.assertIn("def _backup_index_path()", text)
        self.assertIn("def _load_backup_index()", text)
        self.assertIn("rt.load_backup_index", list_fn)
        self.assertNotIn("os.scandir(", list_fn)
        self.assertNotIn(".glob(", list_fn)

    def test_backup_list_without_index_returns_non_blocking_empty_success(self) -> None:
        handlers_py = _backend / "core" / "backup_readonly_handlers.py"
        text = handlers_py.read_text(encoding="utf-8")
        self.assertIn('"index_available": False', text)
        self.assertIn('"message": "Noch kein Backup-Index vorhanden"', text)

    def test_media_path_is_blocked_without_scan(self) -> None:
        app_py = _backend / "app.py"
        handlers_py = _backend / "core" / "backup_readonly_handlers.py"
        validate_fn = app_py.read_text(encoding="utf-8").split("def _validate_backup_list_dir", 1)[1].split("\ndef _", 1)[0]
        list_fn = handlers_py.read_text(encoding="utf-8").split("async def list_backups", 1)[1]
        self.assertIn("STORAGE-PROTECTION-005", validate_fn)
        self.assertIn("/media/", validate_fn)
        self.assertIn('"backup.path_invalid"', list_fn)
        self.assertIn("STORAGE-PROTECTION-005", list_fn)
        self.assertIn('"diagnosis_id": diagnosis_id', list_fn)
        self.assertNotIn("os.scandir(", list_fn)

    def test_successful_backup_updates_index(self) -> None:
        app_py = _backend / "app.py"
        text = app_py.read_text(encoding="utf-8")
        self.assertIn("_record_backup_index_entry(", text)
        self.assertIn('"storage_path": str(bf.parent)', text)
        helper_block = text.split("def _record_backup_index_entry(", 1)[1].split("\ndef _validate_backup_list_dir", 1)[0]
        self.assertNotIn("password", helper_block.lower())


if __name__ == "__main__":
    unittest.main()
