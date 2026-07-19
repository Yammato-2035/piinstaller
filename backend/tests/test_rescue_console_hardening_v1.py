"""GUI/TUI console hardening: VT7 kiosk, getty stop, honest openvt errors."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COMMON = REPO / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"
WATCHDOG = REPO / "scripts/rescue-live/image/setuphelfer-rescue-gui-watchdog.sh"
TUI_UNIT = REPO / "scripts/rescue-live/image/systemd/setuphelfer-rescue-tui.service"
X11 = REPO / "scripts/rescue-live/image/setuphelfer-rescue-x11-early.sh"


class RescueConsoleHardeningTests(unittest.TestCase):
    def test_default_kiosk_vt_is_7(self) -> None:
        common = COMMON.read_text(encoding="utf-8")
        self.assertIn('SETUPHELFER_RESCUE_KIOSK_VT="${SETUPHELFER_RESCUE_KIOSK_VT:-7}"', common)
        watchdog = WATCHDOG.read_text(encoding="utf-8")
        self.assertIn("SETUPHELFER_RESCUE_KIOSK_VT:-7", watchdog)
        x11 = X11.read_text(encoding="utf-8")
        self.assertIn("SETUPHELFER_RESCUE_KIOSK_VT:-7", x11)

    def test_prepare_kiosk_vt_stops_getty(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_prepare_kiosk_vt()", text)
        block = text.split("setuphelfer_rescue_prepare_kiosk_vt()", 1)[1].split(
            "setuphelfer_rescue_chromium_running()", 1
        )[0]
        self.assertIn("getty@tty", block)
        self.assertIn("mask --runtime", block)

    def test_openvt_does_not_switch_before_spawn(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        fn = text.split("setuphelfer_rescue_run_on_kiosk_vt()", 1)[1].split(
            "setuphelfer_rescue_prepare_x11_env()", 1
        )[0]
        self.assertIn("openvt -f -w -c", fn)
        self.assertIn("CHVT_KIOSK", fn)
        self.assertIn("x11_ready", fn)
        self.assertIn("prepare_kiosk_vt", fn)

    def test_failure_code_keeps_startx_honest(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        fn = text.split("setuphelfer_rescue_gui_failure_code()", 1)[1].split(
            "setuphelfer_rescue_show_start_assistant_fallback()", 1
        )[0]
        self.assertIn("startx_not_started", fn)
        self.assertNotIn("openvt_console_2_not_released", fn)
        self.assertIn("openvt_console_busy", fn)

    def test_tui_conflicts_getty_and_no_hangup(self) -> None:
        text = TUI_UNIT.read_text(encoding="utf-8")
        self.assertIn("Conflicts=", text)
        self.assertIn("getty@tty1.service", text)
        self.assertIn("TTYVHangup=no", text)
        self.assertIn("Before=", text)

    def test_tui_mark_active_masks_getty(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        fn = text.split("setuphelfer_rescue_tui_mark_active()", 1)[1].split(
            "setuphelfer_rescue_prepare_kiosk_vt()", 1
        )[0]
        self.assertIn("getty@tty1.service", fn)
        self.assertIn("mask --runtime", fn)

    def test_watchdog_classifies_openvt_busy(self) -> None:
        text = WATCHDOG.read_text(encoding="utf-8")
        self.assertIn("openvt_console_busy", text)
        self.assertIn("prepare_kiosk_vt", text)
        pre = text.split("KIOSK_FOREGROUND_VT", 1)[0]
        self.assertNotIn('chvt "$SETUPHELFER_RESCUE_KIOSK_VT"', pre)


if __name__ == "__main__":
    unittest.main()
