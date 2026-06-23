from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


class TestApiConsistencyFix9V1(unittest.TestCase):
    def test_backup_list_uses_dedicated_read_validation(self) -> None:
        app_py = _backend / "app.py"
        handlers_py = _backend / "core" / "backup_readonly_handlers.py"
        text = app_py.read_text(encoding="utf-8")
        list_block = handlers_py.read_text(encoding="utf-8")
        list_fn = list_block.split("async def list_backups", 1)[1]
        self.assertIn("def _validate_backup_list_dir(", text)
        self.assertIn('"validation_mode": "read_only"', list_fn)
        self.assertIn("rt.load_backup_index", list_fn)
        self.assertIn('"index_available": False', list_fn)
        self.assertIn('"message": "Noch kein Backup-Index vorhanden"', list_fn)
        self.assertNotIn("os.scandir(", list_fn)
        self.assertNotIn(".glob(", list_fn)
        self.assertNotIn("resolve_mount_source_for_path", text)
        self.assertNotIn("_collect_backups_sync", list_fn)
        self.assertIn('"diagnosis_id": diagnosis_id', list_fn)

    def test_backup_data_success_returns_source_plan_details(self) -> None:
        app_py = _backend / "app.py"
        text = app_py.read_text(encoding="utf-8")
        self.assertIn('"selected_sources": data_sources', text)
        self.assertIn('"skipped_sources": skipped_optional', text)
        self.assertIn('"required_sources": required_sources', text)
        self.assertIn('"optional_sources": optional_sources', text)

    def test_restore_preview_response_exposes_private_tmp_hint(self) -> None:
        app_py = _backend / "app.py"
        handlers_py = _backend / "core" / "backup_execute_handlers.py"
        text = app_py.read_text(encoding="utf-8")
        restore_fn = handlers_py.read_text(encoding="utf-8").split("async def restore_backup", 1)[1]
        self.assertIn("def _private_tmp_isolation_active()", text)
        self.assertIn('"private_tmp_isolation": private_tmp_isolation', restore_fn)
        self.assertIn('"preview_dir_visibility_note": preview_visibility_note', restore_fn)
        self.assertIn('"service_private_tmp_hint": private_tmp_hint_key', restore_fn)

    def test_backup_index_write_contains_only_metadata(self) -> None:
        app_py = _backend / "app.py"
        text = app_py.read_text(encoding="utf-8")
        self.assertIn("def _record_backup_index_entry(", text)
        self.assertIn('"backup_file": backup_file', text)
        self.assertIn('"source_summary": {"selected_sources": list(selected_sources or [])}', text)
        helper_block = text.split("def _record_backup_index_entry(", 1)[1].split("\ndef _validate_backup_list_dir", 1)[0]
        self.assertNotIn("sudo_password", helper_block)
        self.assertNotIn("passphrase", helper_block)


if __name__ == "__main__":
    unittest.main()
