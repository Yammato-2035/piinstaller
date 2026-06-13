"""Phase G.12: System Status Core contract tests."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

CORE_PATH = _BACKEND / "core" / "system_status_core.py"
FACADE_PATH = _BACKEND / "core" / "system_status_facade.py"

PUBLIC_FUNCTIONS = (
    "build_backup_status",
    "build_restore_status",
    "build_security_status",
    "build_update_status",
    "build_overall_status",
    "build_system_status_diagnostics",
    "load_backup_realtest_state",
)


class TestSystemStatusCoreV1(unittest.TestCase):
    def test_core_module_has_version_and_public_api(self) -> None:
        import core.system_status_core as core

        self.assertEqual(core.SYSTEM_STATUS_CORE_VERSION, 1)
        for name in PUBLIC_FUNCTIONS:
            self.assertTrue(hasattr(core, name), f"missing {name}")
            self.assertTrue(callable(getattr(core, name)))

    def test_build_backup_status_green_with_file(self) -> None:
        import core.system_status_core as core

        with mock.patch("pathlib.Path.exists", return_value=True):
            color = core.build_backup_status(
                realtest_state={"last_verify_ok": True, "last_verify_path": "/tmp/backup.tar"},
            )
        self.assertEqual(color, "green")

    def test_build_overall_status_keys(self) -> None:
        import core.system_status_core as core

        with (
            mock.patch.object(core, "build_backup_status", return_value="green"),
            mock.patch.object(core, "build_restore_status", return_value="yellow"),
            mock.patch.object(core, "build_security_status", return_value="red"),
            mock.patch.object(core, "build_update_status", return_value="green"),
        ):
            out = core.build_overall_status(realtest_state={})
        self.assertEqual(out, {"backup": "green", "restore": "yellow", "security": "red", "updates": "green"})

    def test_facade_ampel_delegates_to_core(self) -> None:
        text = FACADE_PATH.read_text(encoding="utf-8")
        self.assertIn("system_status_core", text)
        self.assertIn("build_overall_status", text)
        self.assertNotIn("last_verify_ok", text)
        self.assertNotIn("permitrootlogin", text)

    def test_app_compute_system_status_wrapper(self) -> None:
        text = (_BACKEND / "app.py").read_text(encoding="utf-8")
        start = text.index("def _compute_system_status")
        block = text[start : start + 350]
        self.assertIn("system_status_core", block)
        self.assertIn("build_overall_status", block)


if __name__ == "__main__":
    unittest.main()
