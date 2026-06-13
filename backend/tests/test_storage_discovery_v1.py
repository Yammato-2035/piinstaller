"""Phase P.1: Storage Discovery Canonical contract tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

PUBLIC_FUNCTIONS = (
    "discover_block_devices",
    "discover_mounts",
    "discover_filesystems",
    "discover_partitions",
    "discover_storage_roles",
    "discover_lsblk_node_by_mountpoint",
    "discover_lsblk_node_by_name",
    "discover_disk_by_name",
    "discover_mountpoints_for_disk",
    "disk_has_system_mount",
    "build_storage_discovery_diagnostics",
)


class TestStorageDiscoveryV1(unittest.TestCase):
    def test_discovery_module_has_version_and_public_api(self) -> None:
        import core.storage_discovery as discovery

        self.assertEqual(discovery.STORAGE_DISCOVERY_VERSION, 1)
        for name in PUBLIC_FUNCTIONS:
            self.assertTrue(hasattr(discovery, name), f"missing {name}")
            self.assertTrue(callable(getattr(discovery, name)))

    def test_discover_partitions_from_tree(self) -> None:
        import core.storage_discovery as discovery

        fake_tree = [
            {
                "device": "/dev/sda",
                "partitions": [{"device": "/dev/sda1", "partitions": []}],
            }
        ]
        with mock.patch.object(discovery, "discover_block_devices", return_value=fake_tree):
            parts = discovery.discover_partitions()
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]["device"], "/dev/sda1")

    def test_discover_lsblk_json_tree_returns_dict(self) -> None:
        import core.storage_discovery as discovery

        with mock.patch.object(discovery, "_run_shell_capture", return_value=(0, '{"blockdevices":[]}')):
            out = discovery.discover_lsblk_json_tree()
        self.assertEqual(out, {"blockdevices": []})

    def test_discover_findmnt_mounts_flat(self) -> None:
        import core.storage_discovery as discovery

        payload = '{"filesystems":[{"target":"/","source":"/dev/sda1"}]}'
        with mock.patch.object(discovery, "_run_shell_capture", return_value=(0, payload)):
            mounts = discovery.discover_findmnt_mounts_flat()
        self.assertEqual(len(mounts), 1)
        self.assertEqual(mounts[0]["target"], "/")

    def test_storage_facade_uses_storage_discovery(self) -> None:
        text = (_BACKEND / "core" / "storage_facade.py").read_text(encoding="utf-8")
        self.assertIn("core.storage_discovery", text)
        self.assertIn("discover_block_devices", text)
        self.assertIn("discover_filesystems", text)


if __name__ == "__main__":
    unittest.main()
