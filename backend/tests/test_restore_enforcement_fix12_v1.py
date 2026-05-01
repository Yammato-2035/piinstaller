from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


def _has_fastapi() -> bool:
    return importlib.util.find_spec("fastapi") is not None


def _has_testclient_stack() -> bool:
    return _has_fastapi() and importlib.util.find_spec("httpx") is not None


_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


class TestRestoreEnforcementFix12V1(unittest.TestCase):
    def _backup_file_for_tests(self) -> str:
        p = Path("/tmp/setuphelfer-test/fix12")
        p.mkdir(parents=True, exist_ok=True)
        f = p / "dummy.tar.gz"
        f.write_bytes(b"not-a-real-tar")
        return str(f)

    @unittest.skipUnless(_has_testclient_stack(), "TestClient stack")
    def test_restore_without_target_dir_returns_missing_error(self) -> None:
        import app as app_module
        from fastapi.testclient import TestClient

        backup_file = self._backup_file_for_tests()
        with patch.object(app_module, "_analyze_tar_members", return_value={"total_files": 0, "total_dirs": 0, "total_other": 0, "blocked_entries": []}):
            client = TestClient(app_module.app)
            r = client.post("/api/backup/restore", json={"file": backup_file, "mode": "restore"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json().get("code"), "backup.restore_target_missing")

    @unittest.skipUnless(_has_testclient_stack(), "TestClient stack")
    def test_restore_with_valid_target_returns_restore_success(self) -> None:
        import app as app_module
        from fastapi.testclient import TestClient

        backup_file = self._backup_file_for_tests()
        analysis = {"total_files": 2, "total_dirs": 1, "total_other": 0, "blocked_entries": []}
        with patch.object(app_module, "_analyze_tar_members", return_value=analysis):
            with patch.object(app_module, "_validate_restore_target_dir", return_value="/mnt/setuphelfer/restore-target"):
                with patch.object(app_module, "run_command_async", return_value={"success": True, "stdout": "", "stderr": ""}) as m_async:
                    client = TestClient(app_module.app)
                    r = client.post(
                        "/api/backup/restore",
                        json={
                            "file": backup_file,
                            "mode": "restore",
                            "target_dir": "/mnt/setuphelfer/restore-target",
                        },
                    )
        body = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(body.get("code"), "backup.restore_success")
        self.assertEqual(body.get("mode"), "restore")
        self.assertEqual(body.get("target_dir"), "/mnt/setuphelfer/restore-target")
        self.assertEqual(m_async.call_count, 1)

    @unittest.skipUnless(_has_testclient_stack(), "TestClient stack")
    def test_restore_media_target_maps_to_storage_protection(self) -> None:
        import app as app_module
        from fastapi.testclient import TestClient

        backup_file = self._backup_file_for_tests()
        with patch.object(app_module, "_analyze_tar_members", return_value={"total_files": 0, "total_dirs": 0, "total_other": 0, "blocked_entries": []}):
            with patch.object(app_module, "_validate_restore_target_dir", side_effect=ValueError("STORAGE-PROTECTION-005: blocked")):
                client = TestClient(app_module.app)
                r = client.post(
                    "/api/backup/restore",
                    json={"file": backup_file, "mode": "restore", "target_dir": "/media/user/x"},
                )
        body = r.json()
        self.assertEqual(body.get("code"), "backup.restore_target_invalid")
        self.assertEqual((body.get("details") or {}).get("diagnosis_id"), "STORAGE-PROTECTION-005")

    @unittest.skipUnless(_has_testclient_stack(), "TestClient stack")
    def test_restore_nowrite_target_maps_to_perm_group(self) -> None:
        import app as app_module
        from fastapi.testclient import TestClient

        backup_file = self._backup_file_for_tests()
        with patch.object(app_module, "_analyze_tar_members", return_value={"total_files": 0, "total_dirs": 0, "total_other": 0, "blocked_entries": []}):
            with patch.object(app_module, "_validate_restore_target_dir", side_effect=ValueError("PERM-GROUP-008: denied")):
                client = TestClient(app_module.app)
                r = client.post(
                    "/api/backup/restore",
                    json={"file": backup_file, "mode": "restore", "target_dir": "/mnt/setuphelfer/restore-nowrite"},
                )
        body = r.json()
        self.assertEqual(body.get("code"), "backup.restore_not_writable")
        self.assertEqual((body.get("details") or {}).get("diagnosis_id"), "PERM-GROUP-008")

    @unittest.skipUnless(_has_testclient_stack(), "TestClient stack")
    def test_restore_root_target_is_blocked(self) -> None:
        import app as app_module
        from fastapi.testclient import TestClient

        backup_file = self._backup_file_for_tests()
        with patch.object(app_module, "_analyze_tar_members", return_value={"total_files": 0, "total_dirs": 0, "total_other": 0, "blocked_entries": []}):
            client = TestClient(app_module.app)
            r = client.post("/api/backup/restore", json={"file": backup_file, "mode": "restore", "target_dir": "/"})
        body = r.json()
        self.assertEqual(body.get("code"), "backup.restore_target_invalid")
        self.assertEqual((body.get("details") or {}).get("diagnosis_id"), "RESTORE-RUNTIME-006")

    @unittest.skipUnless(_has_testclient_stack(), "TestClient stack")
    def test_preview_does_not_call_restore_engine(self) -> None:
        import app as app_module
        from fastapi.testclient import TestClient

        backup_file = self._backup_file_for_tests()
        analysis = {"total_files": 1, "total_dirs": 0, "total_other": 0, "blocked_entries": []}
        with patch.object(app_module, "_analyze_tar_members", return_value=analysis):
            with patch.object(app_module, "RESTORE_PREVIEW_BASE", Path("/tmp/setuphelfer-test/preview-fix12")):
                with patch.object(app_module, "run_command_async", return_value={"success": True, "stdout": "", "stderr": ""}) as m_async:
                        client = TestClient(app_module.app)
                        r = client.post("/api/backup/restore", json={"file": backup_file, "mode": "preview"})
        body = r.json()
        self.assertEqual(body.get("code"), "backup.restore_preview_ok")
        self.assertEqual(m_async.call_count, 1)

    @unittest.skipUnless(_has_testclient_stack(), "TestClient stack")
    def test_preview_and_restore_have_explicitly_different_codes(self) -> None:
        import app as app_module
        from fastapi.testclient import TestClient

        backup_file = self._backup_file_for_tests()
        analysis = {"total_files": 1, "total_dirs": 0, "total_other": 0, "blocked_entries": []}
        with patch.object(app_module, "_analyze_tar_members", return_value=analysis):
            with patch.object(app_module, "RESTORE_PREVIEW_BASE", Path("/tmp/setuphelfer-test/preview-fix12-diff")):
                with patch.object(app_module, "run_command_async", return_value={"success": True, "stdout": "", "stderr": ""}):
                        with patch.object(app_module, "_validate_restore_target_dir", return_value="/mnt/setuphelfer/restore-target"):
                            client = TestClient(app_module.app)
                            r_preview = client.post("/api/backup/restore", json={"file": backup_file, "mode": "preview"})
                            r_restore = client.post(
                                "/api/backup/restore",
                                json={"file": backup_file, "mode": "restore", "target_dir": "/mnt/setuphelfer/restore-target"},
                            )
        self.assertEqual(r_preview.json().get("code"), "backup.restore_preview_ok")
        self.assertEqual(r_restore.json().get("code"), "backup.restore_success")


if __name__ == "__main__":
    unittest.main()


class TestRestoreEnforcementFix12SourceChecks(unittest.TestCase):
    def test_restore_contract_and_codes_present_in_source(self) -> None:
        app_py = _backend / "app.py"
        text = app_py.read_text(encoding="utf-8")
        self.assertIn("if mode not in (\"preview\", \"restore\")", text)
        self.assertIn("\"backup.restore_target_missing\"", text)
        self.assertIn("\"backup.restore_target_invalid\"", text)
        self.assertIn("\"backup.restore_not_writable\"", text)
        self.assertIn("\"backup.restore_success\"", text)
        self.assertIn("\"backup.restore_preview_ok\"", text)
        self.assertIn("if not target_dir:", text)
        self.assertIn("if target_dir.strip() == \"/\":", text)
