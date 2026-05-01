"""
FIX-13: Full-Backup schließt /media-Bäume aus und nutzt robuste cancelbare tar-Ausführung.
"""

from __future__ import annotations

import importlib.util
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


def _has_fastapi() -> bool:
    return importlib.util.find_spec("fastapi") is not None


@unittest.skipUnless(_has_fastapi(), "fastapi")
class TestBackupFullExcludesFix13V1(unittest.TestCase):
    def test_full_backup_command_excludes_media_and_existing_paths(self) -> None:
        import app as app_module

        seen_cmds: list[str] = []

        def fake_run_command(cmd, sudo=False, sudo_password=None, timeout=10):
            seen_cmds.append(str(cmd))
            return {"success": False, "stderr": "simulated tar fail", "stdout": "", "returncode": 2}

        with patch.object(app_module, "run_command", side_effect=fake_run_command):
            with patch.object(app_module, "validate_backup_target"):
                out = app_module._do_backup_logic(
                    sudo_password="",
                    backup_type="full",
                    backup_dir="/media/volker/setuphelfer-back/backups",
                    timestamp="20260429_223000",
                )

        tar_cmds = [c for c in seen_cmds if c.startswith("tar -czf ")]
        self.assertTrue(tar_cmds, "expected tar command for full backup")
        tar_cmd = tar_cmds[0]
        self.assertIn("--exclude=/proc", tar_cmd)
        self.assertIn("--exclude=/sys", tar_cmd)
        self.assertIn("--exclude=/dev", tar_cmd)
        self.assertIn("--exclude=/tmp", tar_cmd)
        self.assertIn("--exclude=/run", tar_cmd)
        self.assertIn("--exclude=/mnt", tar_cmd)
        self.assertIn("--exclude=/media", tar_cmd)
        self.assertIn("--exclude=/run/media", tar_cmd)
        self.assertIn("--exclude=/media/volker/setuphelfer-back/backups", tar_cmd)
        self.assertTrue(tar_cmd.endswith(" /"), tar_cmd)
        self.assertEqual(out.get("code"), "backup.failed")

    def test_cancelable_tar_uses_devnull_stdout_and_drains_stderr(self) -> None:
        import app as app_module

        class _FakeStderr:
            def __init__(self):
                self._chunks = ["tar warning 1\n", "tar warning 2\n", ""]

            def read(self, _n: int = -1):
                if self._chunks:
                    return self._chunks.pop(0)
                return ""

        class _FakeProc:
            def __init__(self):
                self.pid = 99999
                self.returncode = None
                self.stderr = _FakeStderr()
                self._poll_calls = 0

            def poll(self):
                self._poll_calls += 1
                if self._poll_calls >= 2:
                    self.returncode = 2
                    return self.returncode
                return None

            def wait(self, timeout=None):
                self.returncode = 2
                return 2

            def terminate(self):
                self.returncode = -15

        popen_kwargs = {}

        def fake_popen(*args, **kwargs):
            popen_kwargs.update(kwargs)
            return _FakeProc()

        with patch.object(app_module, "validate_backup_target"):
            with patch.object(app_module.subprocess, "Popen", side_effect=fake_popen):
                with patch.object(app_module.os, "getpgid", return_value=99999):
                    out = app_module._do_backup_logic(
                        sudo_password="",
                        backup_type="full",
                        backup_dir="/media/volker/setuphelfer-back/backups",
                        timestamp="20260429_223001",
                        cancel_event=threading.Event(),
                        job={},
                    )

        self.assertEqual(popen_kwargs.get("stdout"), app_module.subprocess.DEVNULL)
        self.assertEqual(out.get("code"), "backup.failed")


if __name__ == "__main__":
    unittest.main()
