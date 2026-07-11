"""PI-RS-MSI-FIX-001 common helper presence tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMON = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"


class MsiFix001CommonHelpersTests(unittest.TestCase):
    def test_common_helpers_defined(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        for name in (
            "setuphelfer_rescue_shield_console_early",
            "setuphelfer_rescue_should_auto_msi_evidence",
            "setuphelfer_rescue_tty1_clear_allowed",
            "setuphelfer_rescue_run_msi_rs011b_collect",
            "setuphelfer_rescue_write_gui_fallback_status",
            "setuphelfer_rescue_safe_ui_active",
        ):
            with self.subTest(name=name):
                self.assertIn(f"{name}()", text)


if __name__ == "__main__":
    unittest.main()
