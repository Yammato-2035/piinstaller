"""Phase A.1: mount_facade public contracts — plan-only, no mount execution."""

from __future__ import annotations

import inspect
import unittest

from core.mount_facade import (
    FACADE_CONTRACT_VERSION,
    ReadonlyMountPlan,
    build_readonly_mount_plan,
    validate_mount_readonly,
    validate_not_live_root,
    validate_source_not_target,
)


class MountFacadeContractsV1Tests(unittest.TestCase):
    def test_readonly_mount_plan_contract(self) -> None:
        storage = {"lsblk_rows": [{"name": "sda1", "fstype": "ext4"}]}
        plan = build_readonly_mount_plan(storage)
        self.assertIsInstance(plan, ReadonlyMountPlan)
        self.assertEqual(plan.facade_version, FACADE_CONTRACT_VERSION)
        self.assertGreaterEqual(len(plan.planned_operations), 1)
        self.assertTrue(all(op.get("read_only") for op in plan.planned_operations))
        self.assertTrue(all(op.get("execution") == "plan_only" for op in plan.planned_operations))

    def test_validate_mount_readonly_accepts_ro(self) -> None:
        out = validate_mount_readonly({"target": "/media/x", "options": "ro,relatime"})
        self.assertTrue(out["valid"])
        self.assertEqual(out["reason_code"], "MOUNT_FACADE_OK")

    def test_validate_mount_readonly_blocks_host_rw(self) -> None:
        out = validate_mount_readonly({"target": "/", "options": "rw,relatime"})
        self.assertFalse(out["valid"])
        self.assertEqual(out["reason_code"], "MOUNT_FACADE_HOST_RW")

    def test_validate_source_not_target(self) -> None:
        ok = validate_source_not_target(source="/dev/sdb1", target="/dev/sdc1")
        bad = validate_source_not_target(source="/dev/sdb1", target="/dev/sdb1")
        self.assertTrue(ok["valid"])
        self.assertFalse(bad["valid"])

    def test_validate_not_live_root(self) -> None:
        self.assertFalse(validate_not_live_root("/")["valid"])
        self.assertTrue(validate_not_live_root("/media/backup")["valid"])

    def test_no_mount_subprocess_in_contract_validators(self) -> None:
        src = "\n".join(
            inspect.getsource(fn)
            for fn in (
                validate_mount_readonly,
                validate_source_not_target,
                validate_not_live_root,
                build_readonly_mount_plan,
            )
        )
        self.assertNotIn('subprocess.run(["mount"', src)
        self.assertNotIn("subprocess.run(['mount'", src)
        self.assertNotIn("subprocess.run([\"umount\"", src)


if __name__ == "__main__":
    unittest.main()
