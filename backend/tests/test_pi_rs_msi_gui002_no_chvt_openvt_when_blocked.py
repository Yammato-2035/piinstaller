"""PI-RS-MSI-GUI-002 no chvt/openvt when blocked tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMON = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"
WATCHDOG = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-gui-watchdog.sh"
X11 = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-x11-early.sh"


class MsiGui002NoVtWhenBlockedTests(unittest.TestCase):
    def test_run_on_kiosk_vt_blocks_before_openvt(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        fn = text.split("setuphelfer_rescue_run_on_kiosk_vt()")[1].split("setuphelfer_rescue_prepare_x11_env()")[0]
        self.assertIn("GUI_VT_BLOCKED", fn)
        self.assertIn("openvt=false", fn)
        openvt_pos = fn.find("openvt")
        block_pos = fn.find("setuphelfer_rescue_should_disable_gui_for_msi_compat")
        self.assertLess(block_pos, openvt_pos)

    def test_watchdog_early_block_no_chvt_in_blocked_path(self) -> None:
        text = WATCHDOG.read_text(encoding="utf-8")
        blocked = text.split("GUI_WATCHDOG_BLOCKED")[0]
        early = text[: text.find("[[ -f \"$HTML\" ]]")]
        self.assertIn("setuphelfer_rescue_should_disable_gui_for_msi_compat", early)
        self.assertNotIn("chvt", early.split("GUI_WATCHDOG_BLOCKED")[0].split("setuphelfer_rescue_should_disable_gui_for_msi_compat")[1])

    def test_fail_skips_chvt_under_msi_compat(self) -> None:
        text = WATCHDOG.read_text(encoding="utf-8")
        fail_fn = text.split("_fail()")[1].split("[[ -f \"$HTML\" ]]")[0]
        self.assertIn("setuphelfer_rescue_should_disable_gui_for_msi_compat", fail_fn)

    def test_x11_early_skips_startx_under_msi(self) -> None:
        text = X11.read_text(encoding="utf-8")
        pre_startx = text.split("if ! command -v startx")[0]
        self.assertIn("msi_compat_gui_disabled", pre_startx)


if __name__ == "__main__":
    unittest.main()
