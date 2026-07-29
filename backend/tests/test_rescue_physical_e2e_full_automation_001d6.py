"""Tests for SETUPHELFER-E2E-LIVE-001D6 TUI refresh, failsafe, SABRENT wait."""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

# Bare relative paths below only resolve when cwd == repo root; anchor them
# explicitly since pytest is normally invoked with cwd == backend/ (see
# .github/workflows/ci.yml `working-directory: backend`).
_REPO_ROOT = Path(__file__).resolve().parents[2]

from core.rescue_physical_e2e_auto_e2e_state import (
    AUTO_E2E_PHASES,
    PHASE_LABELS_DE,
    init_auto_e2e_state,
    update_auto_e2e_state,
    write_heartbeat,
)
from core.rescue_physical_e2e_destructive_target import wait_for_destructive_lab_target
from core.rescue_physical_e2e_failsafe import (
    ABSOLUTE_MAX_UPTIME_SEC,
    INACTIVITY_LIMIT_SEC,
    LEGACY_FAILSAFE_SEC,
    MSI_EVIDENCE_GRACE_SEC,
    evaluate_lab_failsafe,
)
from core.rescue_physical_e2e_msi_evidence_complete import write_msi_evidence_complete
from core.rescue_physical_e2e_run_control import (
    build_run_control,
    consume_run_control,
    load_run_control,
    write_run_control,
)


class TuiLiveRefreshTests(unittest.TestCase):
    def test_tui_display_script_exists(self):
        path = (_REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-auto-e2e-tui-display.py")
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("REFRESH_SEC", text)
        self.assertIn("select.select", text)
        self.assertIn("request_cancel", text)
        self.assertIn("request_shutdown", text)

    def test_tui_shell_invokes_python_display(self):
        tui = (_REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-tui.sh").read_text(encoding="utf-8")
        self.assertIn("setuphelfer-rescue-auto-e2e-tui-display.py", tui)

    def test_phase_labels_cover_001d6_states(self):
        required = (
            "msi_evidence_waiting",
            "msi_evidence_running",
            "sabrent_waiting",
            "sabrent_detected",
            "shutdown_pending",
        )
        for key in required:
            self.assertIn(key, AUTO_E2E_PHASES)
            self.assertIn(key, PHASE_LABELS_DE)

    def test_msi_evidence_waiting_not_generic_only(self):
        self.assertNotEqual(PHASE_LABELS_DE["msi_evidence_waiting"], PHASE_LABELS_DE["msi_hardware_check"])


class Failsafe001D6Tests(unittest.TestCase):
    def test_legacy_420_disabled_flag(self):
        with patch("core.rescue_physical_e2e_failsafe._uptime_sec", return_value=500.0):
            with patch("core.rescue_physical_e2e_failsafe.heartbeat_age_sec", return_value=5.0):
                with patch("core.rescue_physical_e2e_failsafe.read_auto_e2e_state", return_value={"phase": "msi_evidence_running", "updated_at": "2026-07-15T10:00:00Z", "status": "running"}):
                    with patch("core.rescue_physical_e2e_failsafe._marker", return_value=False):
                        with patch(
                            "core.rescue_physical_e2e_failsafe.resolve_run_mode",
                            return_value={"ok": True, "run_mode": "auto_physical_e2e"},
                        ):
                            with patch(
                                "core.rescue_physical_e2e_failsafe._any_component_heartbeat_fresh",
                                return_value=False,
                            ):
                                result = evaluate_lab_failsafe()
        self.assertTrue(result["legacy_420_disabled"])
        self.assertFalse(result["allow_shutdown"])

    def test_fresh_heartbeat_blocks_shutdown(self):
        with patch("core.rescue_physical_e2e_failsafe._uptime_sec", return_value=500.0):
            with patch("core.rescue_physical_e2e_failsafe.heartbeat_age_sec", return_value=10.0):
                with patch("core.rescue_physical_e2e_failsafe.read_auto_e2e_state", return_value={"phase": "backup_create", "updated_at": "2026-07-15T10:00:00Z", "status": "running"}):
                    with patch("core.rescue_physical_e2e_failsafe._marker", side_effect=lambda n: n == "auto-msi-evidence.done"):
                        with patch(
                            "core.rescue_physical_e2e_failsafe.resolve_run_mode",
                            return_value={"ok": True, "run_mode": "auto_physical_e2e"},
                        ):
                            with patch(
                                "core.rescue_physical_e2e_failsafe._any_component_heartbeat_fresh",
                                return_value=False,
                            ):
                                result = evaluate_lab_failsafe()
        self.assertFalse(result["allow_shutdown"])
        self.assertIn("heartbeat_fresh", result["reasons_skip"])

    def test_stale_heartbeat_can_allow_shutdown_after_grace(self):
        with patch("core.rescue_physical_e2e_failsafe._uptime_sec", return_value=1000.0):
            with patch("core.rescue_physical_e2e_failsafe.heartbeat_age_sec", return_value=600.0):
                with patch("core.rescue_physical_e2e_failsafe._state_age_sec", return_value=600.0):
                    with patch("core.rescue_physical_e2e_failsafe.read_auto_e2e_state", return_value={"phase": "msi_evidence_running", "status": "running"}):
                        with patch("core.rescue_physical_e2e_failsafe._marker", return_value=False):
                            with patch(
                                "core.rescue_physical_e2e_failsafe.resolve_run_mode",
                                return_value={"ok": True, "run_mode": "auto_physical_e2e"},
                            ):
                                with patch(
                                    "core.rescue_physical_e2e_failsafe._any_component_heartbeat_fresh",
                                    return_value=False,
                                ):
                                    result = evaluate_lab_failsafe()
        self.assertTrue(result["allow_shutdown"])

    def test_failsafe_script_uses_evaluate_lab_failsafe(self):
        script = (_REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-lab-auto-shutdown-failsafe").read_text(encoding="utf-8")
        self.assertIn("evaluate_lab_failsafe", script)
        self.assertNotIn("420", script)

    def test_main_timer_is_3600_not_420(self):
        timer = (_REPO_ROOT / "scripts/rescue-live/image/systemd/setuphelfer-rescue-lab-auto-shutdown-failsafe.timer").read_text(encoding="utf-8")
        self.assertIn("OnBootSec=3600s", timer)
        self.assertNotIn("OnBootSec=420s", timer)

    def test_watchdog_timer_present(self):
        timer = (_REPO_ROOT / "scripts/rescue-live/image/systemd/setuphelfer-rescue-lab-auto-shutdown-watchdog.timer").read_text(encoding="utf-8")
        self.assertIn("OnBootSec=300s", timer)

    def test_timing_constants(self):
        self.assertEqual(INACTIVITY_LIMIT_SEC, 300.0)
        self.assertEqual(ABSOLUTE_MAX_UPTIME_SEC, 3600.0)
        self.assertEqual(MSI_EVIDENCE_GRACE_SEC, 900.0)
        self.assertEqual(LEGACY_FAILSAFE_SEC, 420.0)


class MsiEvidenceMarkerTests(unittest.TestCase):
    def test_atomic_write_with_payload_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            path = write_msi_evidence_complete(
                base,
                status="passed",
                session_id="sess-1",
                payload_version="1.10.0.24",
            )
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "passed")
            self.assertEqual(data["session_id"], "sess-1")
            self.assertEqual(data["payload_version"], "1.10.0.24")
            self.assertTrue(data["late_gate_completed"])
            self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_non_writable_setup_logs_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            base.chmod(0o555)
            try:
                with self.assertRaises(OSError):
                    write_msi_evidence_complete(base)
            finally:
                base.chmod(0o755)


class SabrentWaitTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._state_dir = self._tmpdir.__enter__()
        self._env_patch = patch.dict("os.environ", {"SETUPHELFER_AUTO_E2E_STATE_DIR": self._state_dir})
        self._env_patch.start()

    def tearDown(self):
        self._env_patch.stop()
        self._tmpdir.__exit__(None, None, None)

    @patch("core.rescue_physical_e2e_destructive_target.select_destructive_lab_target")
    @patch("core.rescue_physical_e2e_destructive_target.time.sleep")
    def test_wait_up_to_120_seconds(self, sleep_mock, select_mock):
        select_mock.return_value = (None, {"ok": False, "code": "blocked_sabrent_not_detected"})
        config = {"enabled": True}
        candidate, gate = wait_for_destructive_lab_target(config, max_wait_sec=120)
        self.assertIsNone(candidate)
        self.assertEqual(gate["code"], "blocked_sabrent_not_detected")
        self.assertGreaterEqual(sleep_mock.call_count, 1)

    @patch("core.rescue_physical_e2e_destructive_target.select_destructive_lab_target")
    @patch("core.rescue_physical_e2e_destructive_target.time.sleep")
    def test_sabrent_waiting_phase_set(self, sleep_mock, select_mock):
        from core.rescue_physical_e2e_auto_e2e_state import read_auto_e2e_state

        select_mock.return_value = (None, {"ok": False})
        wait_for_destructive_lab_target({"enabled": True}, max_wait_sec=4)
        state = read_auto_e2e_state()
        self.assertEqual(state.get("phase"), "sabrent_waiting")


class RunControlConsumptionTests(unittest.TestCase):
    def test_consume_on_timeout_failsafe(self):
        with tempfile.TemporaryDirectory() as tmp:
            logs = Path(tmp)
            write_run_control(logs, build_run_control(expected_payload_version="1.10.0.24"))
            consume_run_control(logs, terminal_status="timeout_failsafe")
            after = load_run_control(logs)
            self.assertTrue(after["consumed"])
            self.assertEqual(after["terminal_status"], "timeout_failsafe")

    def test_default_expected_payload_1_10_0_24(self):
        control = build_run_control()
        self.assertEqual(control["expected_payload_version"], "1.10.0.24")


class FsckEvidenceRedactionTests(unittest.TestCase):
    def test_redacted_evidence_files_exist_after_generation(self):
        for name in (
            "setup_logs_pre_fsck_backup.redacted.json",
            "setup_logs_fsck_precheck.redacted.json",
            "setup_logs_fsck_result.redacted.json",
        ):
            path = (_REPO_ROOT / "docs/evidence/e2e_live_001d") / name
            self.assertTrue(path.is_file(), f"missing {name}")


if __name__ == "__main__":
    unittest.main()
