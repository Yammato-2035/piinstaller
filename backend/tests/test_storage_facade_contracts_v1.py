"""Phase A.1: storage_facade public contracts — imports, types, no shell in contract layer."""

from __future__ import annotations

import inspect
import unittest
from unittest import mock

from core.storage_facade import (
    FACADE_CONTRACT_VERSION,
    BlockDeviceInfo,
    MountInfo,
    StorageTargetClassification,
    StorageTargetRole,
    classify_storage_target,
    get_block_devices,
    get_mount_for_path,
    get_mounts,
    is_external_target,
)


class StorageFacadeContractsV1Tests(unittest.TestCase):
    def test_contract_types_importable(self) -> None:
        self.assertEqual(FACADE_CONTRACT_VERSION, 1)
        dev = BlockDeviceInfo(name="sdb1", device_path="/dev/sdb1", fstype="ext4")
        self.assertEqual(dev.device_path, "/dev/sdb1")
        mnt = MountInfo(source="/dev/sdb1", target="/media/x", fstype="ext4", options="ro")
        self.assertEqual(mnt.options, "ro")
        cls = StorageTargetClassification(
            path_or_device="/dev/sdb1",
            role=StorageTargetRole.BACKUP_TARGET,
            external=True,
        )
        self.assertTrue(cls.external)

    def test_get_block_devices_delegates_without_subprocess_in_test(self) -> None:
        fake_snap = {
            "lsblk_rows": [
                {"name": "sdb1", "fstype": "ext4", "tran": "usb", "type": "part"},
            ],
        }
        with mock.patch("core.storage_facade.build_storage_inventory_snapshot", return_value=fake_snap):
            devices = get_block_devices(mode="live")
        self.assertEqual(len(devices), 1)
        self.assertIsInstance(devices[0], BlockDeviceInfo)
        self.assertEqual(devices[0].name, "sdb1")

    def test_get_mounts_delegates_to_mount_facade(self) -> None:
        fake_mount_snap = {
            "current_mounts": [{"source": "/dev/sda1", "target": "/media/x", "fstype": "ext4", "options": "ro"}],
        }
        with mock.patch("core.mount_facade.build_mount_inventory_snapshot", return_value=fake_mount_snap):
            mounts = get_mounts()
        self.assertEqual(len(mounts), 1)
        self.assertIsInstance(mounts[0], MountInfo)

    def test_get_mount_for_path_longest_prefix(self) -> None:
        mounts = [
            MountInfo(source="/dev/a", target="/media"),
            MountInfo(source="/dev/b", target="/media/setuphelfer"),
        ]
        with mock.patch("core.storage_facade.get_mounts", return_value=mounts):
            hit = get_mount_for_path("/media/setuphelfer/br001")
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit.target, "/media/setuphelfer")

    def test_classify_storage_target_heuristic_mocked(self) -> None:
        fake_snap = {
            "lsblk_rows": [
                {"name": "sdb1", "mountpoint": "/media/usb", "fstype": "ext4", "tran": "usb"},
            ],
        }
        with mock.patch("core.storage_facade.build_storage_inventory_snapshot", return_value=fake_snap):
            out = classify_storage_target("/dev/sdb1")
            external = is_external_target("/dev/sdb1")
        self.assertIsInstance(out, StorageTargetClassification)
        self.assertEqual(out.role, StorageTargetRole.BACKUP_TARGET)
        self.assertTrue(external)

    def test_contract_functions_have_docstrings(self) -> None:
        for fn in (get_block_devices, get_mounts, classify_storage_target, is_external_target):
            self.assertTrue(inspect.getdoc(fn))


if __name__ == "__main__":
    unittest.main()
