"""
FIX-2: /api/backup/create — kein pauschales sudo-Gate für data+local (NoNewPrivileges / HW1).
"""

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


class TestBackupCreateSudoGateV1(unittest.TestCase):
    @unittest.skipUnless(_has_fastapi(), "fastapi")
    def test_needs_sudo_precheck_model(self) -> None:
        import app as app_module

        self.assertFalse(app_module._backup_create_needs_sudo_precheck("data", "local"))
        self.assertFalse(app_module._backup_create_needs_sudo_precheck("DATA", "Local"))
        self.assertTrue(app_module._backup_create_needs_sudo_precheck("full", "local"))
        self.assertTrue(app_module._backup_create_needs_sudo_precheck("data", "local_and_cloud"))
        self.assertTrue(app_module._backup_create_needs_sudo_precheck("incremental", "local"))

    @unittest.skipUnless(_has_fastapi(), "fastapi")
    def test_sudo_nnp_detection(self) -> None:
        import app as app_module

        self.assertTrue(
            app_module._sudo_n_true_failed_due_to_nnp(
                {"success": False, "stderr": 'sudo: Flag "keine neuen Privilegien" ist gesetzt', "stdout": ""}
            )
        )
        self.assertTrue(
            app_module._sudo_n_true_failed_due_to_nnp(
                {"success": False, "stderr": "no new privileges", "stdout": ""}
            )
        )
        self.assertFalse(
            app_module._sudo_n_true_failed_due_to_nnp({"success": False, "stderr": "sorry, try again", "stdout": ""})
        )

    @unittest.skipUnless(_has_testclient_stack(), "TestClient stack")
    @patch("app._do_backup_logic")
    @patch("app._validate_backup_dir")
    def test_create_data_local_no_sudo_n_gate(self, mock_vdir, mock_logic) -> None:
        import app as app_module
        from fastapi.testclient import TestClient

        mock_vdir.return_value = "/mnt/setuphelfer/backups/__pytest_fix2__"
        mock_logic.return_value = {
            "status": "success",
            "message": "ok",
            "results": [],
            "backup_file": "/mnt/setuphelfer/backups/__pytest_fix2__/pi-backup-data-x.tar.gz",
            "timestamp": "x",
            "code": "backup.success",
            "severity": "success",
        }

        calls: list[tuple[str, object]] = []
        _orig_run_command = app_module.run_command

        def tracker(cmd, sudo=False, sudo_password=None, timeout=10):
            cs = cmd if isinstance(cmd, str) else str(cmd)
            calls.append((cs, sudo))
            return _orig_run_command(cmd, sudo=sudo, sudo_password=sudo_password, timeout=timeout)

        with patch.object(app_module.os, "makedirs"):
            with patch.object(app_module, "run_command", side_effect=tracker):
                client = TestClient(app_module.app)
                r = client.post(
                    "/api/backup/create",
                    json={
                        "backup_dir": "/mnt/setuphelfer/backups/__pytest_fix2__",
                        "type": "data",
                        "target": "local",
                    },
                )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body.get("status"), "success", body)
        sudo_n = [c for c in calls if "sudo -n true" in c[0]]
        self.assertEqual(sudo_n, [], calls)

    @unittest.skipUnless(_has_testclient_stack(), "TestClient stack")
    @patch("app._validate_backup_dir")
    def test_create_full_sudo_required_when_no_password(self, mock_vdir) -> None:
        import app as app_module
        from fastapi.testclient import TestClient

        mock_vdir.return_value = "/mnt/setuphelfer/backups/__pytest_full__"

        def fake_run(cmd, sudo=False, sudo_password=None, timeout=10):
            s = cmd if isinstance(cmd, str) else str(cmd)
            if "sudo -n true" in s:
                return {"success": False, "stderr": "a password is required", "stdout": "", "returncode": 1}
            return {"success": True, "stdout": "20260101_000000", "stderr": "", "returncode": 0}

        with patch.object(app_module, "run_command", side_effect=fake_run):
            client = TestClient(app_module.app)
            r = client.post(
                "/api/backup/create",
                json={
                    "backup_dir": "/mnt/setuphelfer/backups/__pytest_full__",
                    "type": "full",
                    "target": "local",
                },
            )
        self.assertEqual(r.status_code, 200)
        b = r.json()
        self.assertEqual(b.get("code"), "backup.sudo_required")
        self.assertTrue(b.get("requires_sudo_password"))

    @unittest.skipUnless(_has_testclient_stack(), "TestClient stack")
    @patch("app._validate_backup_dir")
    def test_create_full_sudo_blocked_by_nnp(self, mock_vdir) -> None:
        import app as app_module
        from fastapi.testclient import TestClient

        mock_vdir.return_value = "/mnt/setuphelfer/backups/__pytest_nnp__"

        def fake_run(cmd, sudo=False, sudo_password=None, timeout=10):
            s = cmd if isinstance(cmd, str) else str(cmd)
            if "sudo -n true" in s:
                return {
                    "success": False,
                    "stderr": 'sudo: Flag "keine neuen Privilegien" ist gesetzt',
                    "stdout": "",
                    "returncode": 1,
                }
            return {"success": True, "stdout": "20260101_000000", "stderr": "", "returncode": 0}

        with patch.object(app_module, "run_command", side_effect=fake_run):
            client = TestClient(app_module.app)
            r = client.post(
                "/api/backup/create",
                json={
                    "backup_dir": "/mnt/setuphelfer/backups/__pytest_nnp__",
                    "type": "full",
                    "target": "local",
                },
            )
        self.assertEqual(r.status_code, 200)
        b = r.json()
        self.assertEqual(b.get("code"), "backup.sudo_blocked_by_nnp")
        self.assertEqual((b.get("details") or {}).get("diagnosis_id"), "SYSTEMD-NNP-031")
        self.assertFalse(b.get("requires_sudo_password", True))

    @unittest.skipUnless(_has_testclient_stack(), "TestClient stack")
    @patch("app._do_backup_logic")
    @patch("app._validate_backup_dir")
    @patch("app.os.makedirs", side_effect=PermissionError("denied"))
    def test_create_data_local_mkdir_perm_no_sudo_fallback(self, mock_makedirs, mock_vdir, mock_logic) -> None:
        import app as app_module
        from fastapi.testclient import TestClient

        mock_vdir.return_value = "/mnt/setuphelfer/backups/__pytest_eacces__"
        mock_logic.return_value = {"status": "success"}

        def fake_run(cmd, sudo=False, sudo_password=None, timeout=10):
            return {"success": True, "stdout": "20260101_000000", "stderr": "", "returncode": 0}

        with patch.object(app_module, "run_command", side_effect=fake_run):
            client = TestClient(app_module.app)
            r = client.post(
                "/api/backup/create",
                json={
                    "backup_dir": "/mnt/setuphelfer/backups/__pytest_eacces__",
                    "type": "data",
                    "target": "local",
                },
            )
        self.assertEqual(r.status_code, 200)
        b = r.json()
        self.assertEqual(b.get("code"), "backup.mkdir_failed")
        self.assertEqual((b.get("details") or {}).get("diagnosis_id"), "PERM-GROUP-008")
        mock_logic.assert_not_called()


if __name__ == "__main__":
    unittest.main()
