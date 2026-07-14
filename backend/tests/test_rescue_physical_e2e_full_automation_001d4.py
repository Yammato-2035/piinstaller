"""Tests for SETUPHELFER-E2E-LIVE-001D4 full automation gates."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.rescue_physical_e2e_physical_import import (
    DEV_LAB_RUN_ID,
    is_physical_msi_run,
    select_physical_msi_run,
)
from core.rescue_physical_e2e_run_control import (
    build_run_control,
    consume_run_control,
    load_run_control,
    validate_run_control,
    write_run_control,
)
from core.rescue_physical_e2e_state_machine import PhysicalE2EStateMachine
from core.rescue_physical_e2e_test_target import (
    build_e2e_target_marker,
    discover_registered_test_targets,
    validate_e2e_target_marker,
    write_e2e_target_marker,
)
from core.rescue_physical_e2e_unattended import new_msi_physical_e2e_run_id


class RunControlTests(unittest.TestCase):
    def test_build_and_consume_one_shot(self):
        with tempfile.TemporaryDirectory() as tmp:
            logs = Path(tmp)
            control = build_run_control()
            write_run_control(logs, control)
            loaded = load_run_control(logs)
            self.assertTrue(validate_run_control(loaded)["ok"])
            consume_run_control(logs)
            after = load_run_control(logs)
            self.assertFalse(after.get("enabled"))
            self.assertTrue(after.get("consumed"))


class TestTargetTests(unittest.TestCase):
    def test_marker_uuid_mismatch_blocked(self):
        marker = build_e2e_target_marker(filesystem_uuid="aaa-bbb")
        gate = validate_e2e_target_marker(marker, mount_point=Path("/mnt"), partition_uuid="ccc-ddd")
        self.assertFalse(gate["ok"])
        self.assertIn("filesystem_uuid_mismatch", gate["errors"])

    def test_internal_transport_blocked(self):
        marker = build_e2e_target_marker(filesystem_uuid="u1")
        gate = validate_e2e_target_marker(
            marker, mount_point=Path("/mnt"), partition_uuid="u1", transport="nvme", removable=False
        )
        self.assertFalse(gate["ok"])

    def test_ambiguous_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for name in ("a", "b"):
                mount = base / name
                mount.mkdir()
                write_e2e_target_marker(mount, build_e2e_target_marker(filesystem_uuid=f"uuid-{name}"))
                candidates = [{"mount": str(mount), "uuid": f"uuid-{name}", "transport": "usb", "removable": True, "label": "TEST"}]
            all_cands = [
                {"mount": str(base / "a"), "uuid": "uuid-a", "transport": "usb", "removable": True, "label": "T1"},
                {"mount": str(base / "b"), "uuid": "uuid-b", "transport": "usb", "removable": True, "label": "T2"},
            ]
            valid, amb = discover_registered_test_targets(all_cands)
            self.assertEqual(len(valid), 2)
            self.assertEqual(amb["code"], "blocked_ambiguous_test_target")


class StateMachineTests(unittest.TestCase):
    def test_transition_and_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = Path(tmp)
            sm = PhysicalE2EStateMachine(journal, e2e_run_id="run-1", correlation_id="corr-1")
            sm.transition("initialized")
            sm.transition("boot_verified")
            state = sm.load()
            self.assertEqual(state["state"], "boot_verified")
            self.assertTrue((journal / "journal.jsonl").is_file())


class PhysicalImportTests(unittest.TestCase):
    def test_dev_lab_run_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / DEV_LAB_RUN_ID
            run.mkdir()
            (run / "auto-physical-e2e-result.json").write_text(
                json.dumps({"source": "physical_msi", "e2e_run_id": DEV_LAB_RUN_ID}) + "\n",
                encoding="utf-8",
            )
            self.assertFalse(is_physical_msi_run(run))

    def test_select_msi_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            logs = Path(tmp)
            e2e = logs / "setuphelfer/evidence/e2e"
            msi = e2e / "e2e-rescue-msi-20260714-120000-deadbeef"
            msi.mkdir(parents=True)
            (msi / "auto-physical-e2e-result.json").write_text(
                json.dumps({"source": "physical_msi", "payload_version": "1.10.0.22"}) + "\n",
                encoding="utf-8",
            )
            sel = select_physical_msi_run(logs)
            self.assertTrue(sel["ok"])
            self.assertEqual(sel["e2e_run_id"], msi.name)


class RunIdTests(unittest.TestCase):
    def test_msi_run_id_format(self):
        run_id = new_msi_physical_e2e_run_id()
        self.assertTrue(run_id.startswith("e2e-rescue-msi-"))


class UnattendedSmokeTests(unittest.TestCase):
    @patch("core.rescue_physical_e2e_unattended.find_setup_logs_mount")
    def test_blocked_without_run_control(self, find_logs):
        find_logs.return_value = Path("/tmp/logs")
        from core.rescue_physical_e2e_unattended import run_unattended_msi_physical_e2e

        with patch("core.rescue_physical_e2e_unattended.load_run_control", return_value=None):
            result = run_unattended_msi_physical_e2e(setup_logs_base=Path("/tmp/logs"))
            self.assertEqual(result["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
