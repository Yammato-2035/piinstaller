"""Tests for SETUPHELFER-E2E-LIVE-001D7B discovery start-gate and TUI routing."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.rescue_auto_discovery_orchestrator import run_auto_discovery
from core.rescue_auto_discovery_start_gate import (
    EXIT_CONFIG_ERROR,
    EXIT_SKIP,
    EXIT_START,
    evaluate_discovery_start_gate,
)
from core.rescue_discovery_boot_completion import evaluate_discovery_boot_completion
from core.rescue_discovery_run_control import (
    build_discovery_run_control,
    consume_discovery_run_control,
    load_discovery_run_control,
    write_discovery_run_control,
)
from core.rescue_physical_e2e_start_gate import evaluate_physical_e2e_start_gate
from core.rescue_run_mode import physical_e2e_start_allowed, resolve_run_mode
from core.rescue_session_state import PHASE_LABELS_DE, init_session_state, read_session_state


REPO = Path(__file__).resolve().parents[2]
DISCOVERY_UNIT = REPO / "scripts/rescue-live/image/systemd/setuphelfer-rescue-auto-discovery.service"
TUI_UNIT = REPO / "scripts/rescue-live/image/systemd/setuphelfer-rescue-tui.service"
PHYSICAL_UNIT = REPO / "scripts/rescue-live/image/systemd/setuphelfer-rescue-auto-physical-e2e.service"
TUI_DISPLAY = REPO / "scripts/rescue-live/image/setuphelfer-rescue-auto-e2e-tui-display.py"
AUTO_E2E_STATE = REPO / "backend/core/rescue_physical_e2e_auto_e2e_state.py"


class SystemdAndStartGateTests(unittest.TestCase):
    def _write_control(self, base: Path, **overrides):
        control = build_discovery_run_control(expected_payload_version="1.10.0.26")
        control.update(overrides)
        write_discovery_run_control(base, control)
        return control

    def test_01_auto_discovery_flag_starts_with_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_control(base)
            with patch("core.rescue_auto_discovery_start_gate._machine_family_plausible", return_value=True):
                result = evaluate_discovery_start_gate(
                    setup_logs_base=base,
                    cmdline={"setuphelfer_auto_discovery=1"},
                    payload_version="1.10.0.26",
                )
        self.assertTrue(result["start_allowed"])
        self.assertEqual(result["exit_code"], EXIT_START)
        self.assertEqual(result["reason"], "discovery_run_control_ready")

    def test_02_msi_lab_auto_plus_control_starts(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_control(base)
            with patch("core.rescue_auto_discovery_start_gate._machine_family_plausible", return_value=True):
                result = evaluate_discovery_start_gate(
                    setup_logs_base=base,
                    cmdline={"setuphelfer_msi_lab_auto=1"},
                    payload_version="1.10.0.26",
                )
        self.assertTrue(result["start_allowed"])
        self.assertEqual(result["exit_code"], EXIT_START)

    def test_03_missing_run_control_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            result = evaluate_discovery_start_gate(
                setup_logs_base=base,
                cmdline={"setuphelfer_auto_discovery=1"},
                payload_version="1.10.0.26",
            )
        self.assertFalse(result["start_allowed"])
        self.assertEqual(result["exit_code"], EXIT_SKIP)

    def test_04_disabled_run_control_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_control(base, enabled=False)
            with patch("core.rescue_auto_discovery_start_gate._machine_family_plausible", return_value=True):
                result = evaluate_discovery_start_gate(
                    setup_logs_base=base,
                    cmdline={"setuphelfer_auto_discovery=1"},
                    payload_version="1.10.0.26",
                )
        self.assertFalse(result["start_allowed"])
        self.assertEqual(result["exit_code"], EXIT_SKIP)

    def test_05_consumed_run_control_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_control(base, consumed=True, enabled=True)
            with patch("core.rescue_auto_discovery_start_gate._machine_family_plausible", return_value=True):
                result = evaluate_discovery_start_gate(
                    setup_logs_base=base,
                    cmdline={"setuphelfer_auto_discovery=1"},
                    payload_version="1.10.0.26",
                )
        self.assertFalse(result["start_allowed"])
        self.assertEqual(result["exit_code"], EXIT_SKIP)

    def test_06_wrong_payload_version_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_control(base, expected_payload_version="1.10.0.26")
            with patch("core.rescue_auto_discovery_start_gate._machine_family_plausible", return_value=True):
                result = evaluate_discovery_start_gate(
                    setup_logs_base=base,
                    cmdline={"setuphelfer_auto_discovery=1"},
                    payload_version="1.10.0.25",
                )
        self.assertFalse(result["start_allowed"])
        self.assertEqual(result["exit_code"], EXIT_CONFIG_ERROR)
        self.assertEqual(result["reason"], "payload_version_mismatch")

    def test_07_no_combined_condition_line(self):
        unit = DISCOVERY_UNIT.read_text(encoding="utf-8")
        self.assertNotIn(
            "ConditionKernelCommandLine=|setuphelfer_msi_lab_auto=1 setuphelfer_auto_discovery=1",
            unit,
        )
        self.assertNotIn("ConditionKernelCommandLine=|setuphelfer_msi_e2e_auto=1 setuphelfer_msi_lab_auto=1", unit)
        phys = PHYSICAL_UNIT.read_text(encoding="utf-8")
        self.assertNotIn(
            "ConditionKernelCommandLine=|setuphelfer_msi_e2e_auto=1 setuphelfer_msi_lab_auto=1",
            phys,
        )

    def test_08_execcondition_points_to_gate(self):
        unit = DISCOVERY_UNIT.read_text(encoding="utf-8")
        self.assertIn(
            "ExecCondition=/usr/local/sbin/setuphelfer-rescue-auto-discovery-start-gate",
            unit,
        )
        gate = REPO / "scripts/rescue-live/image/setuphelfer-rescue-auto-discovery-start-gate"
        self.assertTrue(gate.is_file())


class TuiPathTests(unittest.TestCase):
    def test_09_unit_execstart_exists(self):
        unit = TUI_UNIT.read_text(encoding="utf-8")
        self.assertIn("ExecStart=/usr/local/sbin/setuphelfer-rescue-entrypoint", unit)
        self.assertTrue((REPO / "scripts/rescue-live/image/setuphelfer-rescue-entrypoint.sh").is_file())

    def test_10_unit_paths_have_shebang_sources(self):
        tui = REPO / "scripts/rescue-live/image/setuphelfer-rescue-tui.sh"
        self.assertTrue(tui.read_text(encoding="utf-8").startswith("#!/"))

    def test_11_no_sh_path_mismatch(self):
        unit = TUI_UNIT.read_text(encoding="utf-8")
        self.assertNotIn("setuphelfer-rescue-tui.sh", unit)
        self.assertNotIn("setuphelfer-rescue-entrypoint.sh", unit)
        self.assertIn("ConditionPathExists=/usr/local/sbin/setuphelfer-rescue-tui", unit)

    def test_12_check_script_and_no_duplicate_sh(self):
        script = REPO / "scripts/check-rescue-tui-runtime-path.sh"
        self.assertTrue(script.is_file())
        import subprocess

        proc = subprocess.run(["bash", str(script)], capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("duplicate_tui_start_paths=0", proc.stdout)


class RunModeTests(unittest.TestCase):
    def test_13_discovery_phase_labels_only(self):
        self.assertIn("Automatische Systemerkundung startet", PHASE_LABELS_DE.get("discovery_starting", ""))
        self.assertIn("Datenträger werden erkannt", PHASE_LABELS_DE["storage_collecting"])
        banned = ("Backup startet", "Restore startet", "physischer E2E", "Testfestplatte")
        for label in PHASE_LABELS_DE.values():
            for token in banned:
                self.assertNotIn(token, label)

    def test_14_physical_e2e_skipped_in_discovery_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            write_discovery_run_control(
                base,
                build_discovery_run_control(expected_payload_version="1.10.0.26"),
            )
            decision = physical_e2e_start_allowed(setup_logs_base=base)
            gate = evaluate_physical_e2e_start_gate(setup_logs_base=base)
        self.assertFalse(decision["physical_e2e_start_allowed"])
        self.assertEqual(decision["reason"], "run_mode_auto_discovery_only")
        self.assertEqual(decision["skip_class"], "skipped_by_run_mode")
        self.assertEqual(gate["exit_code"], EXIT_SKIP)

    def test_15_16_no_backup_restore_text_in_discovery_refresh(self):
        text = AUTO_E2E_STATE.read_text(encoding="utf-8")
        self.assertIn("Automatische Systemerkundung startet", text)
        display = TUI_DISPLAY.read_text(encoding="utf-8")
        self.assertIn("physischer E2E", display)  # banned filter present
        self.assertIn("discovery_mode", display)

    def test_17_run_control_wins_over_e2e_cmdline(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            write_discovery_run_control(
                base,
                build_discovery_run_control(expected_payload_version="1.10.0.26"),
            )
            with patch("core.rescue_run_mode._cmdline_tokens", return_value={"setuphelfer_msi_e2e_auto=1"}):
                resolved = resolve_run_mode(setup_logs_base=base)
        self.assertTrue(resolved["ok"])
        self.assertEqual(resolved["run_mode"], "auto_discovery_only")

    def test_18_conflicting_modes_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            control = build_discovery_run_control(expected_payload_version="1.10.0.26")
            control["run_mode"] = "interactive"
            write_discovery_run_control(base, control)
            with patch(
                "core.rescue_run_mode._cmdline_tokens",
                return_value={"setuphelfer_auto_discovery=1"},
            ):
                resolved = resolve_run_mode(setup_logs_base=base)
        self.assertFalse(resolved["ok"])
        self.assertEqual(resolved["code"], "blocked_run_mode_conflict")


class SessionShutdownTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._env = patch.dict(
            "os.environ",
            {
                "SETUPHELFER_RESCUE_SESSION_DIR": str(Path(self._tmpdir.name) / "session"),
                "SETUPHELFER_RESCUE_STATE_DIR": str(Path(self._tmpdir.name) / "state"),
            },
        )
        self._env.start()
        Path(self._tmpdir.name, "state").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self._env.stop()
        self._tmpdir.cleanup()

    def test_19_20_discovery_creates_session_and_heartbeat(self):
        state = init_session_state(payload_version="1.10.0.26", run_mode="auto_discovery_only")
        self.assertTrue(str(state["session_id"]).startswith("rescue-session-"))
        self.assertTrue(Path(self._tmpdir.name, "session", "state.json").is_file())
        self.assertTrue(Path(self._tmpdir.name, "session", "journal.jsonl").is_file())
        self.assertIsNotNone(state.get("last_heartbeat_at"))
        self.assertEqual(state.get("run_mode"), "auto_discovery_only")

    def test_21_22_run_control_consumed_on_success_and_failure(self):
        with tempfile.TemporaryDirectory() as logs:
            base = Path(logs)
            write_discovery_run_control(
                base,
                build_discovery_run_control(expected_payload_version="1.10.0.26"),
            )
            consume_discovery_run_control(base, consumed_by_session_id="s1", terminal_status="passed")
            c1 = load_discovery_run_control(base)
            self.assertTrue(c1["consumed"])
            self.assertFalse(c1["enabled"])
            self.assertEqual(c1["terminal_status"], "passed")

            write_discovery_run_control(
                base,
                build_discovery_run_control(expected_payload_version="1.10.0.26"),
            )
            consume_discovery_run_control(base, consumed_by_session_id="s2", terminal_status="failed")
            c2 = load_discovery_run_control(base)
            self.assertTrue(c2["consumed"])
            self.assertEqual(c2["terminal_status"], "failed")

    def test_23_not_started_discovery_creates_failure_evidence(self):
        with tempfile.TemporaryDirectory() as logs:
            base = Path(logs)
            write_discovery_run_control(
                base,
                build_discovery_run_control(expected_payload_version="1.10.0.26"),
            )
            # force harvest + state dirs via env for boot_completion STATE writes
            state = Path(logs) / "run-state"
            disc = state / "discovery"
            disc.mkdir(parents=True)
            with patch.dict(
                os.environ,
                {
                    "SETUPHELFER_RESCUE_STATE_DIR": str(state),
                    "SETUPHELFER_RESCUE_DISCOVERY_DIR": str(disc),
                },
            ):
                with patch("core.rescue_discovery_boot_completion._run", return_value=""):
                    with patch(
                        "core.rescue_discovery_observability.find_setup_logs_mount",
                        return_value=base,
                    ):
                        result = evaluate_discovery_boot_completion(setup_logs_base=base)
            self.assertIn(result["action"], {"failed_and_consumed", "finalized"})
            self.assertIn(
                result["status"],
                {
                    "failed_discovery_service_not_started",
                    "failed_discovery_observability_incomplete",
                },
            )
            control = load_discovery_run_control(base)
            self.assertTrue(control["consumed"])
            self.assertIn(
                control["terminal_status"],
                {
                    "failed_discovery_service_not_started",
                    "failed_discovery_observability_incomplete",
                },
            )

    def test_24_shutdown_requires_terminal_state_in_wrapper(self):
        script = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-auto-discovery").read_text(
            encoding="utf-8"
        )
        self.assertIn("terminal", script)
        self.assertIn("evidence_complete", script)
        self.assertIn("shutdown_safe", script)

    def test_25_no_legacy_420_shutdown(self):
        for path in (
            REPO / "scripts/rescue-live/image/setuphelfer-rescue-lab-auto-shutdown-failsafe",
            REPO / "scripts/rescue-live/image/systemd/setuphelfer-rescue-lab-auto-shutdown-failsafe.timer",
            DISCOVERY_UNIT,
        ):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("420", text)
        self.assertIn("TimeoutStartSec=2700", DISCOVERY_UNIT.read_text(encoding="utf-8"))


class OrchestratorSmokeTests(unittest.TestCase):
    def test_run_auto_discovery_persists_and_consumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            logs = root / "SETUP_LOGS"
            logs.mkdir()
            state_dir = root / "state"
            session_dir = root / "session"
            state_dir.mkdir()
            session_dir.mkdir()
            write_discovery_run_control(
                logs,
                build_discovery_run_control(expected_payload_version="1.10.0.26"),
            )
            # Pre-write MSI evidence marker.
            marker = logs / "setuphelfer/evidence/msi-rs011b/msi-evidence-complete.json"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(
                json.dumps(
                    {
                        "status": "passed",
                        "late_gate_completed": True,
                        "tui_owned": True,
                        "evidence_synced": True,
                        "payload_version": "1.10.0.26",
                    }
                ),
                encoding="utf-8",
            )

            fake_storage = {
                "targets": [{"path": "/dev/sdb"}],
                "classified": [{"type": "disk", "path": "/dev/sdb", "fstype": "", "label": ""}],
            }

            with patch.dict(
                "os.environ",
                {
                    "SETUPHELFER_RESCUE_SESSION_DIR": str(session_dir),
                    "SETUPHELFER_RESCUE_STATE_DIR": str(state_dir),
                },
            ), patch(
                "core.rescue_auto_discovery_orchestrator.rescue_payload_version",
                return_value="1.10.0.26",
            ), patch(
                "core.rescue_auto_discovery_orchestrator.resolve_run_mode",
                return_value={"ok": True, "run_mode": "auto_discovery_only", "code": "ok"},
            ), patch(
                "core.rescue_auto_discovery_orchestrator.ensure_setup_logs_rw",
                return_value={"writable": True, "mount_point": str(logs), "status": "ok", "fallback_used": False},
            ), patch(
                "core.rescue_auto_discovery_orchestrator.find_setup_logs_mount",
                return_value=logs,
            ), patch(
                "core.rescue_auto_discovery_orchestrator.discover_rescue_storage",
                return_value=fake_storage,
            ), patch(
                "core.rescue_auto_discovery_orchestrator.build_network_connectivity_v2",
                return_value={"ok": True},
            ), patch(
                "core.rescue_auto_discovery_orchestrator.build_privacy_summary",
                return_value={"secret_detected": False},
            ), patch(
                "core.rescue_auto_discovery_orchestrator.validate_session_evidence",
                return_value={"status": "complete"},
            ), patch(
                "core.rescue_auto_discovery_orchestrator._run",
                return_value=(0, ""),
            ):
                result = run_auto_discovery(allow_destructive=False)
                self.assertEqual(result["status"], "rescue_auto_discovery_evidence_complete")
                self.assertTrue((session_dir / "state.json").is_file())
                sid = result["session_id"]
                evidence = logs / "setuphelfer/evidence/sessions" / sid
                self.assertTrue((evidence / "00-session.json").is_file())
                self.assertTrue((evidence / "state.json").is_file())
                self.assertTrue((evidence / "journal.jsonl").is_file())
                control = load_discovery_run_control(logs)
                self.assertTrue(control["consumed"])
                loaded = read_session_state()
                self.assertIsNotNone(loaded)
                self.assertTrue(loaded["terminal"])
                self.assertTrue(loaded["shutdown_safe"])


class GrubFlagTests(unittest.TestCase):
    def test_grub_includes_auto_discovery(self):
        from core.rescue_msi_lab_auto_boot import MSI_LAB_CMDLINE_FLAGS

        self.assertIn("setuphelfer_auto_discovery=1", MSI_LAB_CMDLINE_FLAGS)
        self.assertIn("setuphelfer_msi_e2e_auto=0", MSI_LAB_CMDLINE_FLAGS)
        self.assertNotIn("setuphelfer_msi_e2e_auto=1", MSI_LAB_CMDLINE_FLAGS)


if __name__ == "__main__":
    unittest.main()
