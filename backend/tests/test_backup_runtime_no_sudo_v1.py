"""
FIX-1: Backup-Tar läuft ohne sudo (Kompatibilität mit NoNewPrivileges=true).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


class TestBackupRuntimeNoSudoV1(unittest.TestCase):
    def test_run_tar_uses_run_command_without_sudo(self) -> None:
        app_py = _backend / "app.py"
        self.assertTrue(app_py.is_file(), "app.py expected")
        text = app_py.read_text(encoding="utf-8")
        # Nur Ausschnitte prüfen — bei assertIn(needle, gesamtes app.py) werden Fehlermeldungen riesig (716k+),
        # was CI-Logs/Pytest-Ausgabe sprengen kann.
        start = text.find("def _run_tar")
        self.assertGreaterEqual(start, 0, "_run_tar helper not found in app.py")
        cancel = text.find("# cancelable tar", start)
        self.assertGreater(cancel, start, "non-cancelable _run_tar block end marker not found")
        head = text[start:cancel]
        self.assertIn(
            "return run_command(guarded_cmd, sudo=False, sudo_password=None, timeout=7200)",
            head,
            "_run_tar (non-cancel) must invoke tar without sudo (via systemd-inhibit wrapped command)",
        )
        tail = text[cancel : cancel + 3500]
        self.assertIn(
            '["sh", "-c", guarded_cmd]',
            tail,
            "cancelable tar must use plain sh -c without sudo",
        )

    def test_safe_device_allows_setuphelfer_backups(self) -> None:
        from core.safe_device import validate_write_target, write_safe_prefixes_resolved

        prefs = [str(p) for p in write_safe_prefixes_resolved()]
        self.assertTrue(any(p.endswith("/mnt/setuphelfer") for p in prefs))


if __name__ == "__main__":
    unittest.main()
