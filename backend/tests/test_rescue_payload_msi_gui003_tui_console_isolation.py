"""PI-RS-MSI-GUI-003 TUI console isolation tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.rescue_boot_timeline import (
    plan_boot_progress_steps,
    simulate_msi_compat_boot,
    validate_timeline_for_profile,
)
from core.rescue_console_ownership import (
    AUDIT_WRITE_BLOCKED,
    boot_progress_tty_clear_allowed,
    boot_progress_tty_write_allowed,
    evaluate_tty_write_attempt,
    load_console_ownership,
    transition_console_owner,
)
from core.rescue_msi_boot_profile import resolve_rescue_boot_profile
from core.rescue_payload_version import rescue_payload_version
from core.rescue_session_evidence import (
    build_session_meta,
    evaluate_evidence_freshness,
    init_boot_session,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMON = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"
BOOT_PROGRESS = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-boot-progress"
TUI = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-tui.sh"
GUI_WATCHDOG = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-gui-watchdog.sh"
X11_EARLY = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-x11-early.sh"

MSI_CMDLINE = (
    "boot=live setuphelfer_rescue=1 setuphelfer_msi_compat=1 nomodeset "
    "nouveau.modeset=0 pci=noaer setuphelfer_mode=text setuphelfer_kiosk=0"
)
DEFAULT_CMDLINE = "boot=live setuphelfer_rescue=1 setuphelfer_mode=gui setuphelfer_kiosk=1"


class MsiGui003BootProfileTests(unittest.TestCase):
    def test_msi_compat_yields_tui_only(self) -> None:
        profile = resolve_rescue_boot_profile(MSI_CMDLINE)
        self.assertEqual(profile["boot_mode"], "tui_only")
        self.assertFalse(profile["gui_available"])
        self.assertFalse(profile["gui_progress_allowed"])

    def test_msi_compat_blocks_gui_progress(self) -> None:
        profile = resolve_rescue_boot_profile(MSI_CMDLINE)
        self.assertFalse(profile["gui_progress_allowed"])

    def test_msi_compat_no_x11_starting_phase(self) -> None:
        steps = plan_boot_progress_steps(MSI_CMDLINE)
        phases = [step["phase"] for step in steps]
        self.assertNotIn("x11_starting", phases)

    def test_msi_compat_no_gui_progress_message(self) -> None:
        steps = plan_boot_progress_steps(MSI_CMDLINE)
        messages = [step["message_de"] for step in steps]
        self.assertNotIn("Grafische Oberfläche wird gestartet …", messages)

    def test_msi_compat_emits_tui_mode_selected(self) -> None:
        steps = plan_boot_progress_steps(MSI_CMDLINE)
        phases = [step["phase"] for step in steps]
        self.assertIn("tui_mode_selected", phases)

    def test_non_msi_profile_keeps_x11_starting(self) -> None:
        steps = plan_boot_progress_steps(DEFAULT_CMDLINE)
        phases = [step["phase"] for step in steps]
        self.assertIn("x11_starting", phases)

    def test_gui_unavailable_blocks_gui_progress_before_phase_build(self) -> None:
        profile = resolve_rescue_boot_profile(MSI_CMDLINE)
        self.assertFalse(profile["gui_progress_allowed"])
        steps = plan_boot_progress_steps(MSI_CMDLINE)
        self.assertTrue(all(not step.get("render_tty") for step in steps if step["phase"] == "tui_mode_selected"))


class MsiGui003ConsoleOwnershipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.ownership = Path(self.tmp.name) / "console-ownership.json"
        self.shield = Path(self.tmp.name) / "console-shield.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_boot_progress_blocked_after_tui_handoff(self) -> None:
        transition_console_owner("tui_owned", session_id="s1", boot_id="b1", path=self.ownership, shield_path=self.shield)
        self.assertFalse(boot_progress_tty_write_allowed(path=self.ownership))

    def test_boot_progress_clear_blocked_after_tui_handoff(self) -> None:
        transition_console_owner("tui_owned", session_id="s1", boot_id="b1", path=self.ownership, shield_path=self.shield)
        self.assertFalse(boot_progress_tty_clear_allowed(path=self.ownership))

    def test_gui_transition_blocked_after_tui_owned(self) -> None:
        state = transition_console_owner("tui_owned", path=self.ownership, shield_path=self.shield)
        self.assertFalse(state["gui_transition_allowed"])

    def test_blocked_write_emits_audit_code(self) -> None:
        transition_console_owner("tui_owned", path=self.ownership, shield_path=self.shield)
        state = load_console_ownership(self.ownership)
        result = evaluate_tty_write_attempt(writer="boot_progress", state=state)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["audit_code"], AUDIT_WRITE_BLOCKED)

    def test_console_owner_transition_is_deterministic(self) -> None:
        first = transition_console_owner("tui_initializing", path=self.ownership, shield_path=self.shield)
        second = transition_console_owner("tui_owned", path=self.ownership, shield_path=self.shield)
        self.assertEqual(first["owner"], "tui")
        self.assertEqual(second["lifecycle_state"], "tui_owned")


class MsiGui003SessionEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "sessions"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_session_files_contain_session_and_boot_id(self) -> None:
        meta = init_boot_session(
            session_id="20260712_120000_boot",
            boot_id="boot-1",
            payload_version="1.10.0.16",
            root=self.root,
            pointer_path=Path(self.tmp.name) / "current-session.json",
        )
        session_file = self.root / "20260712_120000_boot" / "gui-availability.json"
        data = json.loads(session_file.read_text(encoding="utf-8"))
        self.assertEqual(data["session_id"], meta["session_id"])
        self.assertEqual(data["boot_id"], meta["boot_id"])

    def test_stale_session_detected(self) -> None:
        current = build_session_meta(session_id="new", boot_id="b2", payload_version="1.10.0.16")
        stale = evaluate_evidence_freshness(
            {"session_id": "old", "boot_id": "b1", "payload_version": "1.10.0.15"},
            current_session=current,
        )
        self.assertTrue(stale["stale_evidence_detected"])
        self.assertFalse(stale["current_session_evidence"])

    def test_timestamp_before_session_start_is_stale(self) -> None:
        current = build_session_meta(
            session_id="new",
            boot_id="b2",
            payload_version="1.10.0.16",
            session_started_at="2026-07-12T12:00:00Z",
        )
        stale = evaluate_evidence_freshness(
            {"session_id": "new", "session_started_at": "2026-07-12T11:00:00Z"},
            current_session=current,
        )
        self.assertTrue(stale["stale_evidence_detected"])

    def test_stale_not_current_gui_start_proof(self) -> None:
        current = build_session_meta(session_id="new", boot_id="b2", payload_version="1.10.0.16")
        stale = evaluate_evidence_freshness({"session_id": "old"}, current_session=current)
        self.assertFalse(stale["current_session_evidence"])


class MsiGui003ShellGuardTests(unittest.TestCase):
    def test_openvt_not_called_under_msi_compat(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        block = text.split("setuphelfer_rescue_should_disable_gui_for_msi_compat", 1)[1]
        self.assertIn("openvt=false", block)

    def test_chvt_blocked_under_msi_compat(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("GUI_VT_BLOCKED", text)
        self.assertIn("chvt=false", text)

    def test_startx_blocked_in_watchdog(self) -> None:
        text = GUI_WATCHDOG.read_text(encoding="utf-8")
        self.assertIn("startx=false", text)

    def test_x11_early_skipped_under_msi_compat(self) -> None:
        text = X11_EARLY.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_should_disable_gui_for_msi_compat", text)

    def test_boot_progress_uses_timeline_plan(self) -> None:
        text = BOOT_PROGRESS.read_text(encoding="utf-8")
        self.assertIn("_load_plan", text)
        self.assertIn("setuphelfer_rescue_boot_progress_tty_write_allowed", text)

    def test_tui_transitions_console_owner(self) -> None:
        text = TUI.read_text(encoding="utf-8")
        self.assertIn("tui_owned", text)
        self.assertIn("setuphelfer_rescue_init_boot_session", text)

    def test_non_msi_common_still_has_gui_path(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_should_start_gui", text)


class MsiGui003VersionTests(unittest.TestCase):
    def test_payload_version_is_1_10_0_21(self) -> None:
        self.assertEqual(rescue_payload_version(), "1.10.0.21")


class MsiGui003SimulatedBootTests(unittest.TestCase):
    def test_simulated_msi_boot_timeline(self) -> None:
        result = simulate_msi_compat_boot(MSI_CMDLINE)
        phases = result["timeline_phases"]
        self.assertIn("tui_mode_selected", phases)
        forbidden = {
            "x11_starting",
            "gui_starting",
            "openvt_starting",
            "startx_starting",
            "xorg_starting",
            "chromium_starting",
        }
        self.assertFalse(forbidden.intersection(phases))
        self.assertTrue(result["timeline_validation"]["ok"])
        self.assertEqual(result["console_state"]["owner"], "tui")
        self.assertFalse(result["console_state"]["boot_progress_write_allowed"])
        self.assertFalse(result["physical_boot_verified"])


if __name__ == "__main__":
    unittest.main()
