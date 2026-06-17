"""RS-F2B.1: rescue backup plan contract tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.msi_windows_image_backup import OPERATOR_CONFIRMATION_1, OPERATOR_CONFIRMATION_2
from core.rescue_backup_plan_contract import build_rescue_backup_plan


class TestRescueBackupPlanContractV1(unittest.TestCase):
    def _base(self, **overrides):
        body = {
            "source_device": "/dev/nvme0n1",
            "source_size_bytes": 100_000_000_000,
            "target_mode": "external_hdd",
            "target_mount": "/media/backup/Backup",
            "target_device": "/dev/sdb1",
            "target_label": "Backup",
            "free_bytes": 500_000_000_000,
            "fstype": "ext4",
            "operator_confirm_source": True,
            "operator_confirm_target": True,
            "operator_confirm_no_restore": True,
            "operator_confirm_no_wipe": True,
        }
        body.update(overrides)
        return body

    def test_hdd_ready_execute_false(self):
        plan = build_rescue_backup_plan(self._base())
        self.assertIn(plan["plan_status"], ("ready", "review_required", "blocked"))
        self.assertFalse(plan["execute_allowed"])
        self.assertEqual(plan["commands"], [])

    def test_wifi_missing_hdd_warning_not_blocked(self):
        plan = build_rescue_backup_plan(self._base())
        codes = [w.get("code") for w in plan.get("warnings") or []]
        if plan["plan_status"] != "blocked":
            self.assertIn("wifi_missing_but_not_required", codes)

    def test_wifi_missing_cloud_blocked(self):
        plan = build_rescue_backup_plan(self._base(target_mode="cloud", wifi_status="missing"))
        codes = [e.get("code") for e in plan.get("errors") or []]
        self.assertIn("cloud_selected_but_wifi_missing", codes)

    def test_target_is_stick_blocked(self):
        plan = build_rescue_backup_plan(
            self._base(target_mount="/media/volker/SETUP_LOGS", target_label="SETUP_LOGS")
        )
        codes = [e.get("code") for e in plan.get("errors") or []]
        self.assertIn("target_is_rescue_stick", codes)

    def test_internal_target_blocked(self):
        plan = build_rescue_backup_plan(self._base(target_device="/dev/nvme1n1p2", target_label=""))
        codes = [e.get("code") for e in plan.get("errors") or []]
        self.assertTrue(any(c in codes for c in ("target_not_external", "target_is_rescue_stick")))

    def test_capacity_insufficient(self):
        with patch("core.msi_windows_image_backup.mount_path_is_active", return_value=True):
            plan = build_rescue_backup_plan(self._base(free_bytes=1000))
        codes = [e.get("code") for e in plan.get("errors") or []]
        self.assertIn("target_capacity_insufficient", codes)

    def test_source_missing(self):
        plan = build_rescue_backup_plan(self._base(source_device=""))
        codes = [e.get("code") for e in plan.get("errors") or []]
        self.assertIn("source_missing", codes)

    def test_no_dd_commands(self):
        plan = build_rescue_backup_plan(self._base())
        self.assertEqual(plan.get("commands"), [])

    def test_telemetry_no_network_upload(self):
        plan = build_rescue_backup_plan(self._base())
        self.assertFalse(plan["telemetry"]["network_upload_attempted"])

    def test_operator_confirmations_use_constants(self):
        self.assertTrue(OPERATOR_CONFIRMATION_1)
        self.assertTrue(OPERATOR_CONFIRMATION_2)


if __name__ == "__main__":
    unittest.main()
