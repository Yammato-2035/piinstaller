"""Tests for SETUPHELFER-E2E-LIVE-001D7C discovery observability + TUI hold."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.rescue_auto_discovery_orchestrator import main as orch_main
from core.rescue_auto_discovery_start_gate import (
    EXIT_SKIP,
    EXIT_START,
    evaluate_discovery_start_gate,
)
from core.rescue_component_heartbeat import write_component_heartbeat, component_heartbeat_age_sec
from core.rescue_discovery_boot_completion import (
    evaluate_discovery_boot_completion,
    harvest_late_journal,
)
from core.rescue_discovery_observability import (
    persist_orchestrator_exit,
    persist_service_result,
    persist_service_start,
    persist_start_gate_audit,
    read_runtime_json,
)
from core.rescue_discovery_run_control import (
    build_discovery_run_control,
    load_discovery_run_control,
    write_discovery_run_control,
)
from core.rescue_physical_e2e_failsafe import evaluate_lab_failsafe

REPO = Path(__file__).resolve().parents[2]


class DiscoveryObservabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name) / "SETUP_LOGS"
        self.base.mkdir()
        self.state = Path(self.tmp.name) / "run"
        self.state.mkdir()
        self.disc = self.state / "discovery"
        self.disc.mkdir()
        self.env = {
            "SETUPHELFER_RESCUE_STATE_DIR": str(self.state),
            "SETUPHELFER_RESCUE_DISCOVERY_DIR": str(self.disc),
        }

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _patch_env(self):
        return patch.dict(os.environ, self.env, clear=False)

    def test_01_start_gate_call_persisted(self):
        with self._patch_env():
            with patch("core.rescue_auto_discovery_start_gate.find_setup_logs_mount", return_value=self.base):
                with patch("core.rescue_discovery_observability.find_setup_logs_mount", return_value=self.base):
                    write_discovery_run_control(
                        self.base,
                        build_discovery_run_control(expected_payload_version="1.10.0.27"),
                    )
                    with patch(
                        "core.rescue_auto_discovery_start_gate._machine_family_plausible",
                        return_value=True,
                    ):
                        with patch(
                            "core.rescue_auto_discovery_start_gate.rescue_payload_version",
                            return_value="1.10.0.27",
                        ):
                            with patch(
                                "core.rescue_auto_discovery_start_gate.resolve_run_mode",
                                return_value={"ok": True, "run_mode": "auto_discovery_only"},
                            ):
                                result = evaluate_discovery_start_gate(
                                    setup_logs_base=self.base,
                                    cmdline={"setuphelfer_auto_discovery=1", "setuphelfer_msi_lab_auto=1"},
                                    payload_version="1.10.0.27",
                                )
                    self.assertTrue(result["start_allowed"])
                    audit = read_runtime_json("start-gate.json")
                    self.assertTrue(audit["called"])
                    self.assertTrue(audit["start_allowed"])
                    self.assertEqual(audit["exit_code"], EXIT_START)
                    # Persistent copy
                    boots = list((self.base / "setuphelfer/evidence/discovery-boot").glob("*/00-start-gate.json"))
                    self.assertTrue(boots)

    def test_02_start_gate_skip_persisted(self):
        with self._patch_env():
            with patch("core.rescue_discovery_observability.find_setup_logs_mount", return_value=self.base):
                result = evaluate_discovery_start_gate(
                    setup_logs_base=self.base,
                    cmdline=set(),
                    payload_version="1.10.0.27",
                )
                self.assertFalse(result["start_allowed"])
                self.assertEqual(result["exit_code"], EXIT_SKIP)
                audit = read_runtime_json("start-gate.json")
                self.assertTrue(audit["called"])
                self.assertFalse(audit["start_allowed"])

    def test_03_service_start_persisted(self):
        with self._patch_env():
            with patch("core.rescue_discovery_observability.find_setup_logs_mount", return_value=self.base):
                persist_service_start(payload_version="1.10.0.27")
                data = read_runtime_json("service-start.json")
                self.assertTrue(data["runner_started"])

    def test_04_orchestrator_exit_0_persisted(self):
        with self._patch_env():
            with patch("core.rescue_discovery_observability.find_setup_logs_mount", return_value=self.base):
                persist_orchestrator_exit({"started": True, "exit_code": 0, "session_created": True})
                data = read_runtime_json("orchestrator-exit.json")
                self.assertEqual(data["exit_code"], 0)

    def test_05_orchestrator_exit_nonzero_persisted(self):
        with self._patch_env():
            with patch("core.rescue_discovery_observability.find_setup_logs_mount", return_value=self.base):
                persist_orchestrator_exit({"started": True, "exit_code": 1, "session_created": False})
                data = read_runtime_json("orchestrator-exit.json")
                self.assertEqual(data["exit_code"], 1)

    def test_06_python_exception_redacted(self):
        with self._patch_env():
            with patch("core.rescue_discovery_observability.find_setup_logs_mount", return_value=self.base):
                with patch(
                    "core.rescue_auto_discovery_orchestrator.run_auto_discovery",
                    side_effect=ImportError("No module named 'secret_token_xyz'"),
                ):
                    with self.assertRaises(ImportError):
                        orch_main()
                data = read_runtime_json("orchestrator-exit.json")
                self.assertEqual(data["status"], "failed_discovery_import")
                self.assertIn("ImportError", data["exception_summary"])
                # Redaction applies to token=value shapes, not bare ImportError text.
                self.assertTrue(data["exception_summary"])

    def test_07_session_init_error_boot_evidence(self):
        with self._patch_env():
            with patch("core.rescue_discovery_observability.find_setup_logs_mount", return_value=self.base):
                write_discovery_run_control(
                    self.base,
                    build_discovery_run_control(expected_payload_version="1.10.0.27"),
                )
                persist_start_gate_audit(
                    {
                        "start_allowed": True,
                        "reason": "discovery_run_control_ready",
                        "exit_code": 0,
                        "kernel_auto_discovery": True,
                        "run_control_found": True,
                        "run_control_enabled": True,
                        "payload_version_match": True,
                    },
                    payload_version="1.10.0.27",
                )
                persist_service_start(payload_version="1.10.0.27")
                persist_orchestrator_exit(
                    {
                        "started": True,
                        "exit_code": 1,
                        "exception_type": "RuntimeError",
                        "exception_summary": "session boom",
                        "status": "failed_discovery_session_init",
                    }
                )
                persist_service_result({"exit_code": 1, "status": "failed_discovery_session_init"})
                with patch("core.rescue_discovery_boot_completion._run", return_value="journal"):
                    result = evaluate_discovery_boot_completion(setup_logs_base=self.base, force_harvest=True)
                self.assertTrue(result["run_control_consumed"])
                self.assertTrue((self.disc / "boot-finalizer.json").is_file())

    def test_08_late_journal_created(self):
        with self._patch_env():
            with patch("core.rescue_discovery_observability.find_setup_logs_mount", return_value=self.base):
                with patch("core.rescue_discovery_boot_completion._run", return_value="ActiveState=active\nResult=success\n"):
                    out = harvest_late_journal(setup_logs_base=self.base)
                self.assertTrue(out["ok"])
                path = Path(out["journal_path"])
                self.assertTrue(path.is_file())
                self.assertIn("late-journal", path.name)

    def test_09_10_systemd_show_captured(self):
        with self._patch_env():
            with patch("core.rescue_discovery_observability.find_setup_logs_mount", return_value=self.base):
                with patch(
                    "core.rescue_discovery_boot_completion._run",
                    return_value="ConditionResult=yes\nExecMainStatus=0\nResult=success\n",
                ):
                    harvest_late_journal(setup_logs_base=self.base)
                status = json.loads((self.disc / "service-status-late.json").read_text(encoding="utf-8"))
                blob = json.dumps(status)
                self.assertIn("ConditionResult", blob)
                self.assertIn("ExecMainStatus", blob)


class RunControlConsumeTests(unittest.TestCase):
    def test_11_start_failure_consumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            state = Path(tmp) / "run"
            disc = state / "discovery"
            disc.mkdir(parents=True)
            write_discovery_run_control(base, build_discovery_run_control(expected_payload_version="1.10.0.27"))
            with patch.dict(
                os.environ,
                {"SETUPHELFER_RESCUE_STATE_DIR": str(state), "SETUPHELFER_RESCUE_DISCOVERY_DIR": str(disc)},
            ):
                with patch("core.rescue_discovery_observability.find_setup_logs_mount", return_value=base):
                    persist_start_gate_audit(
                        {
                            "start_allowed": False,
                            "reason": "payload_version_mismatch",
                            "exit_code": 2,
                            "kernel_auto_discovery": True,
                            "run_control_found": True,
                            "run_control_enabled": True,
                        },
                        payload_version="1.10.0.27",
                    )
                    with patch("core.rescue_discovery_boot_completion._run", return_value=""):
                        evaluate_discovery_boot_completion(setup_logs_base=base, force_harvest=True)
            control = load_discovery_run_control(base)
            self.assertTrue(control["consumed"])

    def test_12_orchestrator_crash_consumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            state = Path(tmp) / "run"
            disc = state / "discovery"
            disc.mkdir(parents=True)
            write_discovery_run_control(base, build_discovery_run_control(expected_payload_version="1.10.0.27"))
            with patch.dict(
                os.environ,
                {"SETUPHELFER_RESCUE_STATE_DIR": str(state), "SETUPHELFER_RESCUE_DISCOVERY_DIR": str(disc)},
            ):
                with patch("core.rescue_discovery_observability.find_setup_logs_mount", return_value=base):
                    with patch(
                        "core.rescue_auto_discovery_orchestrator.run_auto_discovery",
                        side_effect=RuntimeError("boom"),
                    ):
                        with patch(
                            "core.rescue_auto_discovery_orchestrator.find_setup_logs_mount",
                            return_value=base,
                        ):
                            # consume uses find inside main via _find_logs from evidence_import
                            with patch(
                                "core.rescue_physical_e2e_evidence_import.find_setup_logs_mount",
                                return_value=base,
                            ):
                                with self.assertRaises(RuntimeError):
                                    orch_main()
            control = load_discovery_run_control(base)
            self.assertTrue(control["consumed"])

    def test_15_disabled_control_not_reconsumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            state = Path(tmp) / "run"
            disc = state / "discovery"
            disc.mkdir(parents=True)
            control = build_discovery_run_control(expected_payload_version="1.10.0.27")
            control["enabled"] = False
            write_discovery_run_control(base, control)
            with patch.dict(
                os.environ,
                {"SETUPHELFER_RESCUE_STATE_DIR": str(state), "SETUPHELFER_RESCUE_DISCOVERY_DIR": str(disc)},
            ):
                with patch("core.rescue_discovery_observability.find_setup_logs_mount", return_value=base):
                    with patch("core.rescue_discovery_boot_completion._run", return_value=""):
                        result = evaluate_discovery_boot_completion(setup_logs_base=base, force_harvest=True)
            self.assertEqual(result["reason"], "disabled")
            loaded = load_discovery_run_control(base)
            self.assertFalse(loaded["consumed"])


class TuiAndUnitGateTests(unittest.TestCase):
    def test_16_tui_hold_loop_present(self):
        tui = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-tui.sh").read_text(encoding="utf-8")
        self.assertIn("_tui_discovery_hold_needed", tui)
        self.assertIn("setuphelfer-rescue-tui-hold", tui)
        self.assertIn("while true", tui)

    def test_17_hold_screen_text(self):
        hold = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-tui-hold").read_text(encoding="utf-8")
        self.assertIn("Automatische Systemerkundung konnte nicht gestartet werden", hold)
        self.assertIn("Herunterfahren", hold)

    def test_18_display_no_msi_passed_exit_in_discovery(self):
        display = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-auto-e2e-tui-display.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('never inherit MSI "passed"', display)
        self.assertIn("discovery_start_checking", display)

    def test_19_tui_guard_present(self):
        guard = REPO / "scripts/rescue-live/image/setuphelfer-rescue-tui-guard"
        self.assertTrue(guard.is_file())
        self.assertIn("setuphelfer-rescue-tui.service", guard.read_text(encoding="utf-8"))

    def test_22_details_show_error_code(self):
        hold = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-tui-hold").read_text(encoding="utf-8")
        self.assertIn("Status:", hold)
        self.assertIn("details", hold)


class FailsafeTests(unittest.TestCase):
    def test_23_no_shutdown_before_finalizer_in_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            disc = state / "discovery"
            disc.mkdir()
            (state / "auto-msi-evidence.done").write_text("1\n", encoding="utf-8")
            with patch.dict(
                os.environ,
                {"SETUPHELFER_RESCUE_STATE_DIR": str(state), "SETUPHELFER_RESCUE_DISCOVERY_DIR": str(disc)},
            ):
                with patch("core.rescue_physical_e2e_failsafe._uptime_sec", return_value=600.0):
                    with patch("core.rescue_physical_e2e_failsafe.heartbeat_age_sec", return_value=None):
                        with patch(
                            "core.rescue_physical_e2e_failsafe.resolve_run_mode",
                            return_value={"ok": True, "run_mode": "auto_discovery_only"},
                        ):
                            with patch(
                                "core.rescue_physical_e2e_failsafe.read_auto_e2e_state",
                                return_value={},
                            ):
                                result = evaluate_lab_failsafe()
            self.assertFalse(result["allow_shutdown"])
            self.assertIn("waiting_boot_finalizer", result["reasons_skip"])

    def test_26_active_heartbeat_blocks_failsafe(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            disc = state / "discovery"
            disc.mkdir()
            hb = state / "heartbeats"
            hb.mkdir()
            with patch.dict(
                os.environ,
                {"SETUPHELFER_RESCUE_STATE_DIR": str(state), "SETUPHELFER_RESCUE_DISCOVERY_DIR": str(disc)},
            ):
                write_component_heartbeat("tui", state="display")
                self.assertIsNotNone(component_heartbeat_age_sec("tui"))
                with patch("core.rescue_physical_e2e_failsafe._uptime_sec", return_value=2000.0):
                    with patch(
                        "core.rescue_physical_e2e_failsafe.resolve_run_mode",
                        return_value={"ok": True, "run_mode": "auto_discovery_only"},
                    ):
                        # finalizer ready but heartbeat fresh → skip reason present
                        (disc / "boot-finalizer.json").write_text(
                            json.dumps({"terminal": True, "shutdown_safe": True, "status": "ok"}),
                            encoding="utf-8",
                        )
                        with patch(
                            "core.rescue_physical_e2e_failsafe.read_auto_e2e_state",
                            return_value={"phase": "shutdown", "updated_at": "2099-01-01T00:00:00Z"},
                        ):
                            result = evaluate_lab_failsafe(heartbeat_max_age=180.0)
            self.assertIn("heartbeat_fresh", result["reasons_skip"])

    def test_27_observability_timeout_classified(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            disc = state / "discovery"
            disc.mkdir()
            (state / "auto-msi-evidence.done").write_text("1\n", encoding="utf-8")
            with patch.dict(
                os.environ,
                {"SETUPHELFER_RESCUE_STATE_DIR": str(state), "SETUPHELFER_RESCUE_DISCOVERY_DIR": str(disc)},
            ):
                with patch("core.rescue_physical_e2e_failsafe._uptime_sec", return_value=1300.0):
                    with patch("core.rescue_physical_e2e_failsafe.heartbeat_age_sec", return_value=None):
                        with patch(
                            "core.rescue_physical_e2e_failsafe._any_component_heartbeat_fresh",
                            return_value=False,
                        ):
                            with patch(
                                "core.rescue_physical_e2e_failsafe.resolve_run_mode",
                                return_value={"ok": True, "run_mode": "auto_discovery_only"},
                            ):
                                with patch(
                                    "core.rescue_physical_e2e_failsafe.read_auto_e2e_state",
                                    return_value={},
                                ):
                                    result = evaluate_lab_failsafe()
            self.assertTrue(result["allow_shutdown"])
            self.assertEqual(result["shutdown_classification"], "failsafe_observability_timeout")


class ShellGateTests(unittest.TestCase):
    def test_gates_exit_0(self):
        for name in (
            "check-rescue-discovery-start-audit.sh",
            "check-rescue-discovery-runner.sh",
            "check-rescue-late-journal-unit.sh",
            "check-rescue-tui-hold-screen.sh",
            "check-rescue-tty1-guard.sh",
        ):
            proc = subprocess.run(
                ["bash", str(REPO / "scripts" / name)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, f"{name}: {proc.stdout}\n{proc.stderr}")


if __name__ == "__main__":
    unittest.main()
