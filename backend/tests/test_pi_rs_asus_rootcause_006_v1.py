"""PI-RS-ASUS-ROOTCAUSE-TELEMETRY-006 contract tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


class AsusRootcause006Tests(unittest.TestCase):
    def test_tui_baseline_profile_exists_and_forbids_gui(self) -> None:
        from rescue.asus_boot_profiles import get_asus_profile, list_asus_profiles

        self.assertIn("ASUS-TUI-BASELINE", list_asus_profiles())
        self.assertIn("ASUS-XORG-FORENSIC", list_asus_profiles())
        self.assertIn("ASUS-GUI-CONTROLLED", list_asus_profiles())
        p = get_asus_profile("ASUS-TUI-BASELINE")
        self.assertFalse(p["allows_gui"])
        self.assertIn("setuphelfer_tui_baseline=1", p["cmdline_extra"])
        self.assertIn("setuphelfer_mode=text", p["cmdline_extra"])
        self.assertIn("setuphelfer_auto_hw_baseline=1", p["cmdline_extra"])
        self.assertTrue(p.get("auto_hw_baseline"))

    def test_should_start_gui_blocked_helpers_in_common(self) -> None:
        text = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-common.sh").read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_tui_baseline_active", text)
        self.assertIn("setuphelfer_rescue_graphical_browser_start_allowed", text)
        self.assertIn("setuphelfer_rescue_backend_python", text)
        fn = text.split("setuphelfer_rescue_should_start_gui()")[1].split(
            "setuphelfer_rescue_graphical_browser_start_allowed()"
        )[0]
        self.assertIn("setuphelfer_rescue_tui_baseline_active", fn)
        self.assertIn("setuphelfer_rescue_xorg_forensic_active", fn)

    def test_entrypoint_stops_diagnostics_timer_and_owns_tui(self) -> None:
        text = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-entrypoint.sh").read_text(encoding="utf-8")
        self.assertIn("setuphelfer-rescue-boot-diagnostics.timer", text)
        self.assertIn("xorg_forensic", text)
        self.assertIn('setuphelfer_rescue_console_owner_transition "tui_owned"', text)
        self.assertIn("setuphelfer-rescue-tui-baseline-autocapture", text)

    def test_tui_baseline_autocapture_script_exists(self) -> None:
        path = REPO / "scripts/rescue-live/image/setuphelfer-rescue-tui-baseline-autocapture.sh"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("run_hardware_baseline", text)
        self.assertIn('mode="quick"', text)
        self.assertIn("nvme_writes", text)
        self.assertIn("boot-diagnostics", text)
        self.assertIn("setuphelfer_rescue_backend_python", text)

    def test_tui_menu_hides_gui_on_baseline(self) -> None:
        text = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-tui.sh").read_text(encoding="utf-8")
        self.assertIn("TUI-Baseline: Auto-Evidence aktiv", text)
        self.assertIn("setuphelfer_rescue_tui_baseline_active", text)
        self.assertIn("Partitionshelfer (nur Lesen)", text)
        # GUI start must be gated
        fn = text.split("_tui_start_gui()")[1].split("_tui_shell()")[0]
        self.assertIn("setuphelfer_rescue_should_start_gui", fn)

    def test_ui_launch_blocks_chromium_without_gate(self) -> None:
        text = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-ui-launch").read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_graphical_browser_start_allowed", text)
        self.assertIn("chromium_blocked_no_display_or_gate", text)

    def test_startx_forensic_wrapper_captures_exit(self) -> None:
        path = REPO / "scripts/rescue-live/image/setuphelfer-rescue-startx-forensic.sh"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("STARTX_EXIT_CODE", text)
        self.assertIn("-logfile", text)
        self.assertIn("xorg_process_sentinel", text)

    def test_port_ownership_schema(self) -> None:
        from core.rescue_port_ownership import build_port_ownership_report, probe_listening_port

        free = probe_listening_port(59999)
        self.assertEqual(free["state"], "free")
        report = build_port_ownership_report([59999])
        self.assertEqual(report["schema_version"], 1)
        self.assertFalse(report["secrets_exposed"])

    def test_startx_taxonomy(self) -> None:
        from core.rescue_startx_forensics import classify_startx_failure, ISSUE_CODES

        self.assertIn("gui.chromium_started_without_display", ISSUE_CODES)
        c = classify_startx_failure(
            startx_invoked=True,
            startx_exit_code=1,
            xorg_started=False,
            xorg_log_created=False,
            x_socket_created=False,
            stderr_excerpt="no screens found",
        )
        self.assertEqual(c["issue_code"], "gui.xorg.no_screen")

    def test_console_ownership_fallback_tui(self) -> None:
        from core.rescue_console_ownership import transition_console_owner

        with tempfile.TemporaryDirectory() as td:
            own = Path(td) / "own.json"
            shield = Path(td) / "shield.json"
            state = transition_console_owner(
                "fallback_tui",
                session_id="s",
                boot_id="b",
                path=own,
                shield_path=shield,
            )
            self.assertEqual(state["owner"], "tui")
            self.assertEqual(state["lifecycle_state"], "fallback_tui")
            self.assertFalse(state["gui_transition_allowed"])

    def test_grub_default_is_tui_baseline(self) -> None:
        from core.rescue_fat32_esp_usb_writer import generate_fat32_esp_grub_cfg

        cfg = generate_fat32_esp_grub_cfg(fat_label="SETUPHELFER", fat_uuid="ABCD-1234")
        self.assertIn("set default=0", cfg)
        self.assertIn("ASUS-TUI-BASELINE", cfg)
        self.assertIn("ASUS-TUI-BASELINE-HIGHINFO", cfg)
        self.assertIn("ASUS-XORG-FORENSIC", cfg)
        self.assertIn("setuphelfer_tui_baseline=1", cfg)
        self.assertIn("setuphelfer_highinfo=1", cfg)
        # First menuentry after failsafe should be HIGHINFO (007 default).
        first = cfg.split("menuentry ")[1]
        self.assertIn("ASUS-TUI-BASELINE-HIGHINFO", first)

    def test_diagnostics_timer_isolated(self) -> None:
        text = (REPO / "scripts/rescue-live/prepare-controlled-live-build-tree.sh").read_text(encoding="utf-8")
        self.assertIn("ConditionKernelCommandLine=!setuphelfer_tui_baseline=1", text)
        self.assertIn("OnBootSec=3min", text)


    def test_backend_python_helper_prefers_venv(self) -> None:
        text = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-common.sh").read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_backend_python()", text)
        self.assertIn("venv/bin/python3", text)
        ac = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-tui-baseline-autocapture.sh").read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_backend_python", ac)


if __name__ == "__main__":
    unittest.main()
