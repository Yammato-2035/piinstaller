"""ASUS-02: startx on VT7, no systemctl mask, quiet TUI after GUI fail."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMON = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"
WATCHDOG = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-gui-watchdog.sh"
ENTRY = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-entrypoint.sh"
KIOSK = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-kiosk-start"
X11 = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-x11-early.sh"


class Asus02OpenvtVtReleaseTests(unittest.TestCase):
    def test_release_kiosk_vt_stops_without_mask(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_release_kiosk_vt()", text)
        fn = text.split("setuphelfer_rescue_release_kiosk_vt()")[1].split(
            "setuphelfer_rescue_run_on_kiosk_vt_direct()"
        )[0]
        self.assertIn('systemctl stop "getty@tty${vt}.service"', fn)
        self.assertIn("stop_no_mask", fn)
        self.assertNotIn("mask --runtime", fn)

    def test_run_on_kiosk_vt_prefers_startx_before_openvt(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        fn = text.split("setuphelfer_rescue_run_on_kiosk_vt()")[1].split(
            "setuphelfer_rescue_quiet_console_for_tui()"
        )[0]
        self.assertIn("STARTX_VT_EXEC", text)
        self.assertIn("OPENVT_FALLBACK_START", fn)
        startx_pos = fn.find("setuphelfer_rescue_run_on_kiosk_vt_direct")
        openvt_pos = fn.find("OPENVT_FALLBACK_START")
        self.assertGreater(startx_pos, 0)
        self.assertGreater(openvt_pos, startx_pos)
        self.assertIn("7 8 3 4 5 6 2", fn)

    def test_msi_compat_ignores_pci_noaer_when_asus_profile(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        fn = text.split("setuphelfer_rescue_msi_compat_active()")[1].split(
            "setuphelfer_rescue_safe_ui_active()"
        )[0]
        self.assertIn("setuphelfer_asus_profile=", fn)
        self.assertIn("pci=noaer", fn)

    def test_watchdog_defaults_to_vt7(self) -> None:
        text = WATCHDOG.read_text(encoding="utf-8")
        self.assertIn('SETUPHELFER_RESCUE_KIOSK_VT:-7', text)
        self.assertIn("setuphelfer_rescue_restore_tty1_after_gui_fail", text)

    def test_kiosk_start_passes_explicit_vt(self) -> None:
        text = KIOSK.read_text(encoding="utf-8")
        self.assertIn('vt${_kiosk_vt}', text)
        self.assertIn("SETUPHELFER_RESCUE_KIOSK_VT:-7", text)

    def test_entrypoint_restores_tty1_on_gui_fail(self) -> None:
        text = ENTRY.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_restore_tty1_after_gui_fail", text)
        self.assertIn("setuphelfer_rescue_mark_tui_rerender_after_gui_failure", text)

    def test_restore_quiets_console_for_tui(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_quiet_console_for_tui", text)
        fn = text.split("setuphelfer_rescue_restore_tty1_after_gui_fail()")[1].split(
            "setuphelfer_rescue_prepare_x11_env()"
        )[0]
        self.assertIn("setuphelfer_rescue_quiet_console_for_tui", fn)
        self.assertIn("gui_fallback_tui", fn)

    def test_x11_early_no_mask(self) -> None:
        text = X11.read_text(encoding="utf-8")
        self.assertNotIn("mask --runtime", text)
        self.assertIn('vt${KIOSK_VT}', text)


if __name__ == "__main__":
    unittest.main()
