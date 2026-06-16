"""Core facade rescue migration B.2 — delegation helpers."""

from __future__ import annotations

import unittest
from unittest import mock

from core.mount_facade import get_mount_source_for_path
from core.storage_facade import (
    get_block_device_size_bytes,
    get_parent_block_device,
    get_root_block_parent,
    list_disk_blockdevice_nodes,
)


class CoreFacadeRescueMigrationB2Tests(unittest.TestCase):
    def test_get_parent_block_device_from_pkname(self) -> None:
        with mock.patch("core.storage_facade.subprocess.run") as m:
            m.return_value = mock.MagicMock(returncode=0, stdout="/dev/sdb\n", stderr="")
            parent = get_parent_block_device("/dev/sdb1")
        self.assertEqual(parent, "/dev/sdb")

    def test_get_block_device_size_bytes(self) -> None:
        with mock.patch("core.storage_facade.subprocess.run") as m:
            m.return_value = mock.MagicMock(returncode=0, stdout="64023257088\n", stderr="")
            size = get_block_device_size_bytes("/dev/sdb")
        self.assertEqual(size, 64023257088)

    def test_get_mount_source_for_path(self) -> None:
        with mock.patch("core.mount_facade.subprocess.run") as m:
            m.return_value = mock.MagicMock(returncode=0, stdout="/dev/nvme0n1p2\n", stderr="")
            src = get_mount_source_for_path("/")
        self.assertEqual(src, "/dev/nvme0n1p2")

    def test_get_root_block_parent_delegates(self) -> None:
        with mock.patch("core.mount_facade.get_mount_source_for_path", return_value="/dev/sda2"):
            with mock.patch("core.storage_facade.get_parent_block_device", return_value="/dev/sda"):
                self.assertEqual(get_root_block_parent(), "/dev/sda")

    def test_list_disk_blockdevice_nodes_filters_disks(self) -> None:
        with mock.patch(
            "core.storage_facade.build_storage_inventory_snapshot",
            return_value={
                "status": "ok",
                "lsblk_tree": [
                    {"name": "sdb", "type": "disk"},
                    {"name": "sda", "type": "disk", "children": [{"name": "sda1", "type": "part"}]},
                ],
            },
        ):
            disks = list_disk_blockdevice_nodes()
        self.assertEqual(len(disks), 2)
        self.assertTrue(all(d.get("type") == "disk" for d in disks))


if __name__ == "__main__":
    unittest.main()
