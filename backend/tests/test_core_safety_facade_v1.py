from __future__ import annotations

import unittest

from core.safety_facade import (
    build_safety_decision,
    validate_backup_target_for_write,
    validate_no_system_disk_write,
    validate_restore_target,
)


class CoreSafetyFacadeV1Tests(unittest.TestCase):
    def test_system_disk_blocked(self) -> None:
        out = validate_no_system_disk_write("/dev/sda")
        self.assertFalse(out["allowed"])
        self.assertEqual(out["reason_code"], "SAFETY_SYSTEM_DISK")

    def test_external_like_target_allowed(self) -> None:
        out = validate_no_system_disk_write("/dev/sdb")
        self.assertTrue(out["allowed"])

    def test_restore_target_contract(self) -> None:
        out = validate_restore_target("/dev/sdb1", context="rescue")
        self.assertIn("restore_allowed", out)

    def test_build_safety_decision_contract(self) -> None:
        out = build_safety_decision(target="/dev/sdb", context="rescue")
        self.assertIn("allowed", out)
        self.assertIn("reason_code", out)

    def test_backup_target_for_write_contract(self) -> None:
        out = validate_backup_target_for_write("/dev/sdb1", context="live")
        self.assertIn("context", out)


if __name__ == "__main__":
    unittest.main()

