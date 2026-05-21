"""Rescue boot context — read-only envelope (no mounts/writes)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from rescue.boot_context import build_rescue_boot_context  # noqa: E402


class RescueBootContextTests(unittest.TestCase):
    def test_stable_envelope_keys(self) -> None:
        res = build_rescue_boot_context(
            source_root="/mnt/source",
            rescue_mode_hint=True,
            live_system_hint=False,
            network_available_hint=False,
            ui_mode_hint="headless",
        )
        self.assertIn(res["status"], ("ok", "review_required", "blocked"))
        self.assertIsInstance(res["boot_context"], dict)
        self.assertIsInstance(res["warnings"], list)
        self.assertIsInstance(res["errors"], list)
        self.assertIn("rescue.boot_context", res["source_modules"])

    def test_unknown_context_without_crash(self) -> None:
        with patch("rescue.boot_context._read_os_release_live_hint", return_value=None):
            with patch("rescue.boot_context._hints_from_env", return_value=(None, None, [])):
                res = build_rescue_boot_context(source_root="/mnt/x")
        bc = res["boot_context"]
        self.assertEqual(bc["live_system"], "unknown")
        self.assertEqual(bc["rescue_mode"], "unknown")

    def test_rescue_mode_via_hint(self) -> None:
        res = build_rescue_boot_context(
            source_root="/mnt/source",
            rescue_mode_hint=True,
            live_system_hint=False,
        )
        self.assertEqual(res["boot_context"]["rescue_mode"], "true")
        self.assertEqual(res["boot_context"]["live_system"], "false")

    def test_no_subprocess_mount_or_tar(self) -> None:
        import rescue.boot_context as mod

        src = Path(mod.__file__).read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)
        self.assertNotIn("mount(", src)
        self.assertNotIn("tar ", src)


if __name__ == "__main__":
    unittest.main()
