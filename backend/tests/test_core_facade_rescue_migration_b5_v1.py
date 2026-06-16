"""Core facade rescue migration B.5 — app.py storage/safety delegation."""

from __future__ import annotations

import unittest
from unittest import mock

from core.mount_facade import discover_mountpoints_for_disk, discover_mounts_flat, flatten_findmnt_filesystems
from core.safety_facade import WriteTargetProtectionError, validate_write_target
from core.storage_facade import (
    disk_has_system_mount,
    find_disk_by_name,
    find_lsblk_node_by_name,
    get_device_fstype,
    get_lsblk_json_tree,
    list_devices_for_api,
)


class CoreFacadeRescueMigrationB5Tests(unittest.TestCase):
    def test_get_lsblk_json_tree_delegates(self) -> None:
        fake = {"blockdevices": [{"name": "sda", "type": "disk"}]}
        with mock.patch("core.storage_discovery.discover_lsblk_json_tree", return_value=fake):
            self.assertEqual(get_lsblk_json_tree(), fake)

    def test_find_lsblk_node_by_name_delegates(self) -> None:
        node = {"name": "sda1", "type": "part"}
        with mock.patch("core.storage_discovery.discover_lsblk_node_by_name", return_value=node):
            self.assertEqual(find_lsblk_node_by_name("sda1"), node)

    def test_find_disk_by_name_delegates(self) -> None:
        disk = {"name": "sda", "type": "disk"}
        with mock.patch("core.storage_discovery.discover_disk_by_name", return_value=disk):
            self.assertEqual(find_disk_by_name("sda"), disk)

    def test_disk_has_system_mount_delegates(self) -> None:
        with mock.patch("core.storage_discovery.disk_has_system_mount", return_value=True):
            self.assertTrue(disk_has_system_mount({"name": "nvme0n1"}))

    def test_get_device_fstype_delegates(self) -> None:
        with mock.patch("core.storage_discovery.discover_device_fstype", return_value="ext4") as fn:
            out = get_device_fstype("/dev/sda1")
        fn.assert_called_once()
        self.assertEqual(out, "ext4")

    def test_list_devices_for_api_delegates(self) -> None:
        with mock.patch("core.safe_device.devices_for_api", return_value=[{"device": "/dev/sda"}]):
            self.assertEqual(list_devices_for_api(), [{"device": "/dev/sda"}])

    def test_discover_mounts_flat_delegates(self) -> None:
        with mock.patch("core.storage_discovery.discover_findmnt_mounts_flat", return_value=[{"target": "/"}]):
            self.assertEqual(discover_mounts_flat()[0]["target"], "/")

    def test_flatten_findmnt_filesystems_delegates(self) -> None:
        nested = {"filesystems": [{"target": "/"}]}
        with mock.patch("core.storage_discovery._flatten_findmnt_filesystems", return_value=[{"target": "/"}]):
            self.assertEqual(flatten_findmnt_filesystems(nested)[0]["target"], "/")

    def test_discover_mountpoints_for_disk_delegates(self) -> None:
        with mock.patch("core.storage_discovery.discover_mountpoints_for_disk", return_value=["/mnt/usb"]):
            self.assertEqual(discover_mountpoints_for_disk("/dev/sdb"), ["/mnt/usb"])

    def test_app_lsblk_wrappers_use_facades(self) -> None:
        import app as app_module

        with mock.patch("core.storage_facade.get_lsblk_json_tree", return_value={"blockdevices": []}) as tree:
            app_module._lsblk_tree()
        tree.assert_called_once()
        with mock.patch("core.mount_facade.discover_mounts_flat", return_value=[]) as mounts:
            app_module._findmnt_mounts()
        mounts.assert_called_once()

    def test_app_validate_backup_dir_uses_safety_facade(self) -> None:
        import app as app_module

        with mock.patch("core.safety_facade.validate_write_target") as val:
            with mock.patch("core.backup_target_service_access.assert_backup_target_writable_for_service"):
                app_module._validate_backup_dir("/mnt/setuphelfer/backups")
        val.assert_called_once()

    def test_safety_facade_reexports_write_target_error(self) -> None:
        self.assertTrue(issubclass(WriteTargetProtectionError, Exception))


if __name__ == "__main__":
    unittest.main()
