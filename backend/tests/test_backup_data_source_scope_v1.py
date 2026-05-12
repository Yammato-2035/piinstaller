"""
FIX-3: Data-Backup-Quellen sind nicht-privilegiert und liefern strukturierte Fehler.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


def _has_fastapi() -> bool:
    return importlib.util.find_spec("fastapi") is not None


@unittest.skipUnless(_has_fastapi(), "fastapi")
class TestBackupDataSourceScopeV1(unittest.TestCase):
    def test_service_home_candidates_use_effective_service_user(self) -> None:
        import app as app_module

        class _PwEntry:
            pw_dir = "/srv/setuphelfer-home"

        with patch.object(app_module.os, "geteuid", return_value=1234):
            with patch.object(app_module.pwd, "getpwuid", return_value=_PwEntry()):
                candidates = app_module._data_required_source_candidates()

        self.assertEqual([str(p) for p in candidates], ["/srv/setuphelfer-home"])

    def test_is_readable_data_source_permission_error_is_structured(self) -> None:
        import app as app_module

        with patch.object(app_module.Path, "home", return_value=Path("/home/blocked")):
            with patch.object(app_module.Path, "resolve", return_value=Path("/home/blocked")):
                with patch.object(app_module.Path, "exists", side_effect=PermissionError("[Errno 13] Permission denied: '/home/blocked'")):
                    ok, reason = app_module._is_readable_data_source(Path("/home/blocked"))

        self.assertFalse(ok)
        self.assertIn("Permission denied", reason)

    def test_plan_data_sources_excludes_opt_containerd(self) -> None:
        import app as app_module

        def fake_readable(p: Path):
            s = str(p)
            if s == "/home/tester":
                return True, ""
            if s == "/var/www":
                return False, "permission denied"
            return False, "missing"

        with patch.object(app_module, "_service_user_home_path", return_value=Path("/home/tester")):
            with patch.object(app_module, "_is_allowed_data_source_path", return_value=True):
                with patch.object(app_module, "_is_readable_data_source", side_effect=fake_readable):
                    includes, skipped_optional, unreadable_required = app_module._plan_data_backup_sources()

        self.assertEqual(includes, ["/home/tester"])
        self.assertEqual(unreadable_required, [])
        self.assertEqual(skipped_optional, [])
        self.assertFalse(any("containerd" in p for p in includes))

    def test_plan_data_sources_blocks_opt_tree_even_if_readable(self) -> None:
        import app as app_module

        with patch.object(app_module, "_data_required_source_candidates", return_value=[Path("/opt/specialhome")]):
            with patch.object(app_module, "_data_optional_source_candidates", return_value=[]):
                with patch.object(app_module, "_is_readable_data_source", return_value=(True, "")):
                    includes, skipped_optional, unreadable_required = app_module._plan_data_backup_sources()

        self.assertEqual(includes, [])
        self.assertTrue(any("opt" in (x.get("path") or "") for x in unreadable_required))

    def test_data_backup_unreadable_required_returns_structured_error(self) -> None:
        import app as app_module

        with patch.object(app_module, "_configured_data_backup_sources", return_value=[Path("/mnt/setuphelfer/test-data")]):
            with patch.object(
                app_module,
                "_plan_data_backup_sources",
                return_value=([], [], [{"path": "/mnt/setuphelfer/test-data", "reason": "denied"}]),
            ):
                with patch.object(app_module, "validate_backup_target"):
                    out = app_module._do_backup_logic(
                        sudo_password="",
                        backup_type="data",
                        backup_dir="/mnt/setuphelfer/backups/test-run",
                        timestamp="20260425_999999",
                    )

        self.assertEqual(out.get("code"), "backup.source_permission_denied")
        self.assertEqual((out.get("details") or {}).get("diagnosis_id"), "BACKUP-SOURCE-PERM-032")
        self.assertEqual((out.get("details") or {}).get("selected_sources"), [])
        self.assertEqual((out.get("details") or {}).get("required_sources"), ["/mnt/setuphelfer/test-data"])
        self.assertEqual((out.get("details") or {}).get("optional_sources"), [])
        unreadable = (out.get("details") or {}).get("unreadable_sources") or []
        self.assertTrue(any(x.get("path") == "/mnt/setuphelfer/test-data" for x in unreadable))

    def test_data_backup_permission_denied_from_tar_mapped(self) -> None:
        import app as app_module

        seen_cmds: list[str] = []

        def fake_run_command(cmd, sudo=False, sudo_password=None, timeout=10):
            s = str(cmd)
            seen_cmds.append(s)
            # _run_tar nutzt systemd-inhibit + sh -c; Kommando beginnt nicht mit "tar -czf "
            if "tar -czf" in s:
                return {
                    "success": False,
                    "stderr": "tar: /mnt/setuphelfer/test-data: Funktion open fehlgeschlagen: Keine Berechtigung\n",
                    "stdout": "",
                    "returncode": 2,
                }
            return {"success": True, "stdout": "", "stderr": "", "returncode": 0}

        with patch.object(app_module, "_plan_data_backup_sources", return_value=(["/mnt/setuphelfer/test-data"], [], [])):
            with patch.object(app_module, "_configured_data_backup_sources", return_value=[Path("/mnt/setuphelfer/test-data")]):
                with patch.object(app_module, "run_command", side_effect=fake_run_command):
                    with patch.object(app_module, "validate_backup_target"):
                        out = app_module._do_backup_logic(
                            sudo_password="",
                            backup_type="data",
                            backup_dir="/mnt/setuphelfer/backups/test-run",
                            timestamp="20260425_111111",
                        )

        self.assertEqual(out.get("code"), "backup.source_permission_denied")
        self.assertEqual((out.get("details") or {}).get("diagnosis_id"), "BACKUP-SOURCE-PERM-032")
        self.assertEqual((out.get("details") or {}).get("selected_sources"), ["/mnt/setuphelfer/test-data"])
        unreadable = (out.get("details") or {}).get("unreadable_sources") or []
        self.assertTrue(any(x.get("path") == "/mnt/setuphelfer/test-data" for x in unreadable))
        tar_cmds = [c for c in seen_cmds if "tar -czf" in c]
        self.assertTrue(tar_cmds, "expected tar command")
        self.assertFalse(any(" /opt " in c or c.endswith(" /opt") for c in tar_cmds), tar_cmds)

    def test_configured_data_source_is_preferred_over_home(self) -> None:
        import app as app_module

        with patch.object(app_module, "_configured_data_backup_sources", return_value=[Path("/mnt/setuphelfer/test-data")]):
            with patch.object(app_module, "_service_user_home_path", return_value=Path("/home/volker")):
                with patch.object(app_module, "_is_allowed_data_source_path", return_value=True):
                    with patch.object(app_module, "_is_readable_data_source", return_value=(True, "")):
                        includes, _, unreadable_required = app_module._plan_data_backup_sources()

        self.assertEqual(includes, ["/mnt/setuphelfer/test-data"])
        self.assertEqual(unreadable_required, [])
        self.assertFalse(any(p.startswith("/home/") for p in includes))

    def test_configured_opt_source_is_rejected(self) -> None:
        import app as app_module

        with patch.object(app_module, "_configured_data_backup_sources", return_value=[Path("/opt/containerd")]):
            includes, _, unreadable_required = app_module._plan_data_backup_sources()

        self.assertEqual(includes, [])
        self.assertTrue(any((x.get("path") or "").startswith("/opt") for x in unreadable_required))


if __name__ == "__main__":
    unittest.main()
