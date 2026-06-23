"""Core storage facade — read-only, no mounts."""

from __future__ import annotations

import unittest
from unittest import mock

from core.storage_facade import (
    build_storage_inventory_snapshot,
    classify_storage_devices,
    find_candidate_backup_targets,
    find_candidate_restore_targets,
)


class CoreStorageFacadeV1Tests(unittest.TestCase):
    def test_empty_lsblk_review_required(self) -> None:
        with mock.patch("core.storage_facade.discover_block_devices", return_value=[]):
            with mock.patch("core.storage_facade.discover_filesystems", return_value={}):
                with mock.patch(
                    "core.storage_facade._run_lsblk_rescue_rows",
                    return_value=([], "", ["STORAGE_FACADE_LSBLK_NONZERO_OR_EMPTY"]),
                ):
                    with mock.patch(
                        "core.storage_facade._run_blkid_excerpt",
                        return_value=("", []),
                    ):
                        snap = build_storage_inventory_snapshot(mode="rescue")
        self.assertIn(snap["status"], ("review_required", "blocked"))
        self.assertIsInstance(snap["warnings"], list)
        self.assertIsInstance(snap["errors"], list)
        self.assertIn("core.storage_facade", ".".join(snap.get("source_modules") or []))

    def test_known_device_fixture_stable(self) -> None:
        rows = [
            {
                "name": "sdb1",
                "type": "part",
                "fstype": "ext4",
                "label": "setuphelfer-backup",
                "uuid": "U1",
                "mountpoint": "/media/setuphelfer/br001",
                "tran": "usb",
            }
        ]
        with mock.patch("core.storage_facade.discover_block_devices", return_value=[]):
            with mock.patch("core.storage_facade.discover_filesystems", return_value={}):
                with mock.patch(
                    "core.storage_facade._run_lsblk_rescue_rows",
                    return_value=(rows, "{}", []),
                ):
                    with mock.patch(
                        "core.storage_facade._run_blkid_excerpt",
                        return_value=("", []),
                    ):
                        snap = build_storage_inventory_snapshot(mode="live")
        self.assertEqual(snap["status"], "ok")
        self.assertGreaterEqual(len(snap["lsblk_rows"]), 1)
        cls = classify_storage_devices(snap["lsblk_rows"])
        self.assertTrue(cls["flags"]["usb"])
        self.assertTrue(cls["flags"]["backup_candidate"])

    def test_backup_and_restore_candidates_structured(self) -> None:
        rows = [
            {"name": "nvme0n1p2", "fstype": "ext4", "mountpoint": "/", "tran": ""},
            {"name": "sdb1", "fstype": "ext4", "label": "backup", "tran": "usb"},
        ]
        snap = {
            "lsblk_rows": rows,
            "classification": classify_storage_devices(rows),
        }
        bt = find_candidate_backup_targets(snap)
        rt = find_candidate_restore_targets(snap)
        self.assertTrue(any(c.get("role") == "backup_target" for c in bt))
        self.assertTrue(any(c.get("role") == "restore_source_candidate" for c in rt))

    def test_no_mount_subprocess_in_facade_contract(self) -> None:
        import inspect

        import core.storage_facade as mod

        src = inspect.getsource(mod)
        self.assertNotIn('subprocess.run(["mount"', src)
        self.assertNotIn("subprocess.run(['mount'", src)
        self.assertNotIn('subprocess.run(["umount"', src)


if __name__ == "__main__":
    unittest.main()
