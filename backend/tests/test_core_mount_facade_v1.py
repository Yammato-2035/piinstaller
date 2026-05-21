"""Core mount facade — plan only, no mount execution."""

from __future__ import annotations

import json
import unittest
from unittest import mock

from core.mount_facade import (
    build_mount_inventory_snapshot,
    classify_mount_safety,
    plan_readonly_source_mount,
    validate_no_untracked_mount_change,
)


class CoreMountFacadeV1Tests(unittest.TestCase):
    def test_mount_inventory_stable(self) -> None:
        fake = json.dumps(
            {
                "filesystems": [
                    {"target": "/", "source": "/dev/nvme0n1p2", "fstype": "ext4", "options": "rw,relatime"}
                ]
            }
        )
        with mock.patch("core.mount_facade.subprocess.run") as m:
            m.return_value = mock.MagicMock(returncode=0, stdout=fake, stderr="")
            snap = build_mount_inventory_snapshot()
        self.assertIsInstance(snap["current_mounts"], list)
        self.assertGreaterEqual(len(snap["current_mounts"]), 1)
        self.assertIsInstance(snap["warnings"], list)

    def test_readonly_plan_plan_only(self) -> None:
        storage = {"lsblk_rows": [{"name": "sda1", "fstype": "ext4"}]}
        plan = plan_readonly_source_mount(storage)
        ops = plan.get("planned_operations") or []
        self.assertGreaterEqual(len(ops), 1)
        self.assertTrue(all(op.get("read_only") for op in ops))
        self.assertTrue(all(op.get("execution") == "plan_only" for op in ops))

    def test_untracked_mount_change_detected(self) -> None:
        base = [{"target": "/media/x", "source": "/dev/sda1"}]
        cur = base + [{"target": "/media/y", "source": "/dev/sdb1"}]
        out = validate_no_untracked_mount_change(base, cur)
        self.assertTrue(out["untracked_mount_change"])
        self.assertEqual(out["status"], "blocked")

    def test_classify_mount_safety_blocks_host_root_rw(self) -> None:
        safety = classify_mount_safety(
            [{"target": "/", "source": "/dev/foo", "fstype": "ext4", "options": "rw,relatime"}]
        )
        self.assertTrue(safety["blocked"])

    def test_no_mount_execution_in_source(self) -> None:
        import inspect

        import core.mount_facade as mod

        src = inspect.getsource(mod)
        self.assertNotIn("subprocess.run([\"mount\"", src)
        self.assertNotIn("subprocess.run(['mount'", src)


if __name__ == "__main__":
    unittest.main()
