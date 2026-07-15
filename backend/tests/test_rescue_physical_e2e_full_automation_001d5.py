"""Tests for SETUPHELFER-E2E-LIVE-001D5 dedicated SABRENT lab HDD automation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.rescue_physical_e2e_auto_e2e_state import (
    cancel_requested,
    heartbeat_fresh,
    init_auto_e2e_state,
    read_auto_e2e_state,
    request_cancel,
    request_shutdown,
    shutdown_requested,
    update_auto_e2e_state,
)
from dataclasses import replace

from core.rescue_physical_e2e_destructive_target import (
    LAB_PARTITIONS,
    LabDiskCandidate,
    load_destructive_lab_config,
    prepare_destructive_run_paths,
    select_destructive_lab_target,
    verify_destructive_target_identity,
    verify_layout_after_partition,
)
from core.rescue_physical_e2e_msi_evidence_complete import (
    msi_evidence_complete_ok,
    write_msi_evidence_complete,
)
from core.rescue_physical_e2e_run_control import (
    build_destructive_lab_target,
    build_run_control,
    consume_run_control,
    load_run_control,
    write_run_control,
)
from core.rescue_physical_e2e_unattended import is_physical_e2e_success_status


def _sabrent_config() -> dict:
    return build_destructive_lab_target()


def _sabrent_candidate(**overrides) -> LabDiskCandidate:
    base = LabDiskCandidate(
        disk_path="/dev/sdb",
        model="SABRENT USB",
        transport="usb",
        size_bytes=931_000_000_000,
        role="external_backup_hdd",
        partitions=[
            {
                "path": "/dev/sdb1",
                "label": "Backup",
                "uuid": "44ce6f76-7896-4623-87b0-d81aedbed6d5",
                "fstype": "ext4",
                "mountpoint": None,
            }
        ],
    )
    return replace(base, **overrides) if overrides else base


class ServiceIsolationTests(unittest.TestCase):
    def test_msi_evidence_unit_has_no_tty(self):
        unit = Path("scripts/rescue-live/image/systemd/setuphelfer-rescue-auto-msi-evidence.service").read_text(
            encoding="utf-8"
        )
        self.assertIn("StandardInput=null", unit)
        self.assertIn("TTYPath=", unit)

    def test_physical_e2e_unit_has_no_tty(self):
        unit = Path("scripts/rescue-live/image/systemd/setuphelfer-rescue-auto-physical-e2e.service").read_text(
            encoding="utf-8"
        )
        self.assertIn("StandardInput=null", unit)
        self.assertIn("TTYPath=", unit)

    def test_tui_service_owns_tty(self):
        unit = Path("scripts/rescue-live/image/systemd/setuphelfer-rescue-tui.service").read_text(encoding="utf-8")
        self.assertIn("TTYPath=/dev/tty1", unit)


class TuiAutoLockTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._state_dir = self._tmpdir.__enter__()
        self._env_patch = patch.dict("os.environ", {"SETUPHELFER_AUTO_E2E_STATE_DIR": self._state_dir})
        self._env_patch.start()

    def tearDown(self):
        self._env_patch.stop()
        self._tmpdir.__exit__(None, None, None)

    def test_auto_lock_init(self):
        state = init_auto_e2e_state(mode="auto_physical_e2e_locked")
        self.assertEqual(state["mode"], "auto_physical_e2e_locked")

    def test_cancel_request_file(self):
        self.assertFalse(cancel_requested())
        request_cancel()
        self.assertTrue(cancel_requested())

    def test_shutdown_request_file(self):
        request_shutdown()
        self.assertTrue(shutdown_requested())

    def test_tui_script_has_auto_lock_mode(self):
        tui = Path("scripts/rescue-live/image/setuphelfer-rescue-tui.sh").read_text(encoding="utf-8")
        self.assertIn("auto_physical_e2e_locked", tui)
        self.assertIn("--timeout 3", tui)
        self.assertIn("refresh_auto_e2e_phase_from_runtime", tui)


class RuntimeRefreshTests(unittest.TestCase):
    def test_refresh_advances_late_gate_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "auto-e2e"
            rescue_dir = Path(tmp) / "rescue"
            state_dir.mkdir()
            rescue_dir.mkdir()
            with patch.dict(
                "os.environ",
                {
                    "SETUPHELFER_AUTO_E2E_STATE_DIR": str(state_dir),
                    "SETUPHELFER_RESCUE_STATE_DIR": str(rescue_dir),
                },
            ):
                from core.rescue_physical_e2e_auto_e2e_state import (
                    init_auto_e2e_state,
                    refresh_auto_e2e_phase_from_runtime,
                )

                init_auto_e2e_state(mode="auto_physical_e2e_locked")
                with patch("core.rescue_physical_e2e_auto_e2e_state._read_uptime_sec", return_value=60):
                    state = refresh_auto_e2e_phase_from_runtime()
                self.assertEqual(state["phase"], "evidence_collection")
                self.assertIn("Late-Evidence-Gate", state["last_progress"])


class MsiEvidenceGateTests(unittest.TestCase):
    def test_msi_evidence_complete_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            logs = Path(tmp)
            write_msi_evidence_complete(logs)
            self.assertTrue(msi_evidence_complete_ok(logs))

    def test_physical_e2e_waits_for_marker(self):
        script = Path("scripts/rescue-live/image/setuphelfer-rescue-auto-physical-e2e").read_text(encoding="utf-8")
        self.assertIn("msi-evidence-complete.json", script)


class DestructiveTargetIdentityTests(unittest.TestCase):
    def test_model_mismatch_blocks(self):
        cand = _sabrent_candidate(model="OTHER DISK")
        gate = verify_destructive_target_identity(cand, _sabrent_config())
        self.assertFalse(gate["ok"])
        self.assertIn("model_mismatch", gate["errors"])

    def test_size_too_small_blocks(self):
        cand = _sabrent_candidate(size_bytes=100_000_000_000)
        gate = verify_destructive_target_identity(cand, _sabrent_config())
        self.assertFalse(gate["ok"])
        self.assertIn("size_too_small", gate["errors"])

    def test_uuid_mismatch_blocks(self):
        parts = [
            {
                "path": "/dev/sdb1",
                "label": "Backup",
                "uuid": "wrong-uuid",
                "fstype": "ext4",
                "mountpoint": None,
            }
        ]
        cand = _sabrent_candidate(partitions=parts)
        gate = verify_destructive_target_identity(cand, _sabrent_config())
        self.assertFalse(gate["ok"])
        self.assertIn("preformat_uuid_mismatch", gate["errors"])

    def test_label_mismatch_blocks(self):
        parts = [
            {
                "path": "/dev/sdb1",
                "label": "WRONG",
                "uuid": "44ce6f76-7896-4623-87b0-d81aedbed6d5",
                "fstype": "ext4",
                "mountpoint": None,
            }
        ]
        cand = _sabrent_candidate(partitions=parts)
        gate = verify_destructive_target_identity(cand, _sabrent_config())
        self.assertFalse(gate["ok"])
        self.assertIn("label_mismatch", gate["errors"])

    def test_exactly_one_sabrent_allowed(self):
        cfg = _sabrent_config()
        c1 = _sabrent_candidate()
        c2 = _sabrent_candidate(disk_path="/dev/sdc")
        with patch(
            "core.rescue_physical_e2e_destructive_target.discover_lab_disk_candidates",
            return_value=[c1, c2],
        ):
            with patch(
                "core.rescue_physical_e2e_destructive_target.verify_destructive_target_identity",
                side_effect=[{"ok": True}, {"ok": True}],
            ):
                _, gate = select_destructive_lab_target(cfg)
        self.assertFalse(gate["ok"])
        self.assertEqual(gate.get("reason"), "ambiguous")

    def test_single_match_allowed(self):
        cfg = _sabrent_config()
        cand = _sabrent_candidate()
        with patch("core.rescue_physical_e2e_destructive_target.discover_lab_disk_candidates", return_value=[cand]):
            with patch(
                "core.rescue_physical_e2e_destructive_target._flatten",
                return_value=[],
            ):
                selected, gate = select_destructive_lab_target(cfg)
        self.assertTrue(gate["ok"])
        self.assertIsNotNone(selected)


class DestructiveLayoutTests(unittest.TestCase):
    def test_lab_layout_has_three_partitions(self):
        self.assertEqual(len(LAB_PARTITIONS), 3)

    def test_prepare_paths_restore_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            mounts = {
                "source": base / "source",
                "backup": base / "backup",
                "restore": base / "restore",
            }
            for mp in mounts.values():
                mp.mkdir(parents=True)
            paths = prepare_destructive_run_paths(mounts, "e2e-rescue-msi-test-001")
            self.assertEqual(paths["layout_mode"], "dedicated_external_lab_hdd")
            self.assertFalse(any(paths["restore_dir"].iterdir()))

    def test_layout_verification_partition_count(self):
        with patch("core.rescue_physical_e2e_destructive_target._flatten", return_value=[{"path": "/dev/sdb1", "type": "part", "parent_path": "/dev/sdb", "label": "SETUP_E2E_SOURCE", "fstype": "ext4"}]):
            gate = verify_layout_after_partition("/dev/sdb")
        self.assertFalse(gate["ok"])


class RunControl001D5Tests(unittest.TestCase):
    def test_build_includes_destructive_lab_target(self):
        control = build_run_control(expected_payload_version="1.10.0.23")
        self.assertTrue(control["destructive_lab_target"]["enabled"])
        self.assertTrue(control["destructive_lab_target"]["operator_authorized"])

    def test_consume_records_terminal_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            logs = Path(tmp)
            write_run_control(logs, build_run_control())
            consume_run_control(logs, consumed_by_run_id="run-x", terminal_status="passed")
            after = load_run_control(logs)
            self.assertFalse(after["enabled"])
            self.assertTrue(after["consumed"])
            self.assertEqual(after["consumed_by_run_id"], "run-x")
            self.assertEqual(after["terminal_status"], "passed")


class HeartbeatFailsafeTests(unittest.TestCase):
    def test_fresh_heartbeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"SETUPHELFER_AUTO_E2E_STATE_DIR": tmp}):
                from core.rescue_physical_e2e_auto_e2e_state import write_heartbeat

                write_heartbeat(run_id="r1", phase="backup_create")
                self.assertTrue(heartbeat_fresh(max_age=30))

    def test_failsafe_script_checks_heartbeat(self):
        script = Path("scripts/rescue-live/image/setuphelfer-rescue-lab-auto-shutdown-failsafe").read_text(
            encoding="utf-8"
        )
        self.assertIn("heartbeat_fresh", script)


class UnattendedExitStatusTests(unittest.TestCase):
    def test_physical_success_statuses(self):
        self.assertTrue(is_physical_e2e_success_status("physical_rescue_telemetry_diagnostics_e2e_passed"))
        self.assertTrue(is_physical_e2e_success_status("physical_rescue_passed_server_verification_pending"))
        self.assertFalse(is_physical_e2e_success_status("blocked"))

    def test_wrapper_uses_success_helper(self):
        common = Path("scripts/rescue-live/image/setuphelfer-rescue-common.sh").read_text(encoding="utf-8")
        self.assertIn("is_physical_e2e_success_status", common)


class UnattendedDestructiveSmokeTests(unittest.TestCase):
    @patch("core.rescue_physical_e2e_unattended.write_heartbeat")
    @patch("core.rescue_physical_e2e_unattended.run_physical_e2e_workflow")
    @patch("core.rescue_physical_e2e_unattended.create_test_data")
    @patch("core.rescue_physical_e2e_unattended.mount_e2e_partitions")
    @patch("core.rescue_physical_e2e_unattended.verify_layout_after_partition")
    @patch("core.rescue_physical_e2e_unattended.wipe_and_partition_disk")
    @patch("core.rescue_physical_e2e_unattended.select_destructive_lab_target")
    @patch("core.rescue_physical_e2e_unattended.verify_payload_version_gate")
    @patch("core.rescue_physical_e2e_unattended.verify_machine_identity")
    @patch("core.rescue_physical_e2e_unattended.verify_boot_parameters")
    def test_destructive_path_no_smoke_fallback(
        self,
        boot,
        machine,
        payload,
        select_target,
        wipe,
        layout,
        mount,
        create_data,
        workflow,
        hb,
    ):
        hb.return_value = None
        boot.return_value = {"ok": True}
        machine.return_value = {"ok": True, "identity": {}}
        payload.return_value = {"ok": True}
        select_target.return_value = (_sabrent_candidate(), {"ok": True})
        wipe.return_value = {"ok": True}
        layout.return_value = {"ok": True}
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "auto-e2e"
            state_dir.mkdir()
            logs = Path(tmp) / "logs"
            logs.mkdir()
            with patch.dict("os.environ", {"SETUPHELFER_AUTO_E2E_STATE_DIR": str(state_dir)}):
                mounts_base = logs / "mounts"
                source = mounts_base / "source"
                backup = mounts_base / "backup"
                restore = mounts_base / "restore"
                for p in (source, backup, restore):
                    p.mkdir(parents=True)
                mount.return_value = {
                    "ok": True,
                    "mounts": {"source": source, "backup": backup, "restore": restore},
                }
                write_run_control(logs, build_run_control(expected_payload_version="1.10.0.23"))
                workflow.return_value = {
                    "success": True,
                    "status": "physical_rescue_telemetry_diagnostics_e2e_passed",
                    "telemetry": {"receipts_stored": 8},
                    "diagnostics": {"data_received": True, "findings_count": 0},
                }
                from core.rescue_physical_e2e_unattended import run_unattended_msi_physical_e2e

                result = run_unattended_msi_physical_e2e(setup_logs_base=logs, repo_root=Path("."))
                self.assertNotEqual(result["status"], "physical_automation_smoke_passed_external_target_pending")
                self.assertEqual(result["layout_mode"], "dedicated_external_lab_hdd")
                rc = load_run_control(logs)
                self.assertTrue(rc.get("consumed"))


if __name__ == "__main__":
    unittest.main()
