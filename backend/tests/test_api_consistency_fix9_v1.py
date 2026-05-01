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
        text = app_py.read_text(encoding="utf-8")
        list_block = text.split('@app.get("/api/backup/list")', 1)[1].split("\n\n@app.post(\"/api/backup/verify\")", 1)[0]
        self.assertIn("def _validate_backup_list_dir(", text)
        self.assertIn('"validation_mode": "read_only"', list_block)
        self.assertIn("idx = await asyncio.wait_for(asyncio.to_thread(_load_backup_index), timeout=1.0)", list_block)
        self.assertIn('"index_available": False', list_block)
        self.assertIn('"message": "Noch kein Backup-Index vorhanden"', list_block)
        self.assertNotIn("os.scandir(", list_block)
        self.assertNotIn(".glob(", list_block)
        self.assertNotIn("resolve_mount_source_for_path", text)
        self.assertNotIn("_collect_backups_sync", list_block)
        self.assertIn('"diagnosis_id": diagnosis_id', text)

    def test_backup_data_success_returns_source_plan_details(self) -> None:
        app_py = _backend / "app.py"
        text = app_py.read_text(encoding="utf-8")
        self.assertIn('"selected_sources": data_sources', text)
        self.assertIn('"skipped_sources": skipped_optional', text)
        self.assertIn('"required_sources": required_sources', text)
        self.assertIn('"optional_sources": optional_sources', text)

    def test_restore_preview_response_exposes_private_tmp_hint(self) -> None:
        app_py = _backend / "app.py"
        text = app_py.read_text(encoding="utf-8")
        self.assertIn("def _private_tmp_isolation_active()", text)
        self.assertIn('"private_tmp_isolation": private_tmp_isolation', text)
        self.assertIn('"preview_dir_visibility_note": preview_visibility_note', text)
        self.assertIn('"service_private_tmp_hint": private_tmp_hint_key', text)

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
