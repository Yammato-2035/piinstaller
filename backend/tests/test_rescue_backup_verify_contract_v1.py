"""RS-P1 backup verify contract tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.rescue_backup_verify_contract import build_backup_verify_plan


class TestRescueBackupVerifyContractV1(unittest.TestCase):
    def test_verify_required_no_writes(self):
        plan = build_backup_verify_plan(image_path="/mnt/backup.img", manifest_path="/mnt/m.json")
        self.assertTrue(plan["verify_required"])
        self.assertFalse(plan["write_operations_required"])
        self.assertFalse(plan["restore_required"])

    def test_missing_image_blocked(self):
        plan = build_backup_verify_plan()
        self.assertEqual(plan["verify_status"], "blocked")


if __name__ == "__main__":
    unittest.main()
