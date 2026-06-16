"""Core facade rescue migration B.3 — inspect, identity, persistence."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from core.device_identity import build_device_identity
from core.mount_facade import get_findmnt_json_by_source, is_block_device_mounted
from core.storage_facade import probe_block_device_identity
from modules.inspect_storage import _parent_disk, detect_filesystems, readonly_fs_check


class CoreFacadeRescueMigrationB3Tests(unittest.TestCase):
    def test_parent_disk_delegates_to_facade(self) -> None:
        with mock.patch("core.storage_facade.get_parent_block_device", return_value="/dev/sda"):
            self.assertEqual(_parent_disk("/dev/sda1"), "/dev/sda")

    def test_probe_block_device_identity_parses_node(self) -> None:
        fake = json.dumps(
            {
                "blockdevices": [
                    {
                        "path": "/dev/sdb1",
                        "size": "64G",
                        "type": "part",
                        "serial": "ABC",
                    }
                ]
            }
        )
        with mock.patch("core.storage_facade._run_subprocess") as m:
            m.return_value = mock.MagicMock(returncode=0, stdout=fake, stderr="")
            node = probe_block_device_identity("/dev/sdb1")
        self.assertEqual(node.get("serial"), "ABC")

    def test_build_device_identity_uses_facade(self) -> None:
        with mock.patch(
            "core.device_identity.probe_block_device_identity",
            return_value={"size": "1G", "serial": "X1", "type": "part"},
        ):
            with mock.patch.object(Path, "exists", return_value=True):
                ident = build_device_identity("/dev/sdb1")
        self.assertFalse(ident["weak_identity"])
        self.assertEqual(ident["serial"], "X1")

    def test_is_block_device_mounted(self) -> None:
        with mock.patch("core.mount_facade._run_subprocess") as m:
            m.return_value = mock.MagicMock(returncode=0, stdout="/media/x\n", stderr="")
            self.assertTrue(is_block_device_mounted("/dev/sdb1"))

    def test_get_findmnt_json_by_source(self) -> None:
        payload = {"filesystems": [{"target": "/media/x", "source": "/dev/sdb1"}]}
        with mock.patch("core.mount_facade._run_subprocess") as m:
            m.return_value = mock.MagicMock(returncode=0, stdout=json.dumps(payload), stderr="")
            data = get_findmnt_json_by_source("/dev/sdb1")
        self.assertIsInstance(data, dict)

    def test_detect_filesystems_delegates(self) -> None:
        with mock.patch(
            "core.storage_facade.detect_filesystems_for_inspect",
            return_value={"/dev/sdb1": {"uuid": "u1"}},
        ):
            fs = detect_filesystems()
        self.assertIn("/dev/sdb1", fs)

    def test_readonly_fs_check_skips_mounted(self) -> None:
        with mock.patch("core.mount_facade.is_block_device_mounted", return_value=True):
            res = readonly_fs_check("/dev/sdb1", "ext4")
        self.assertTrue(res["skipped"])
        self.assertEqual(res["code"], "rescue.fs.skipped_mounted")


if __name__ == "__main__":
    unittest.main()
