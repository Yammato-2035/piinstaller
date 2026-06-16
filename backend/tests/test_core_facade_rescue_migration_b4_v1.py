"""Core facade rescue migration B.4 — inspect list paths and deploy metadata."""

from __future__ import annotations

import unittest
from unittest import mock

from core.mount_facade import discover_mounts_flat
from core.storage_facade import (
    get_readonly_storage_probe_contract,
    list_classified_block_devices_for_inspect,
    list_physical_disk_paths,
)
from deploy.runner_rescue_storage_discovery import build_rescue_storage_discovery_plan
from modules.inspect_storage import list_block_devices, list_physical_disks


class CoreFacadeRescueMigrationB4Tests(unittest.TestCase):
    def test_list_classified_block_devices_delegates(self) -> None:
        fake = [{"device": "/dev/sda", "type": "disk"}]
        with mock.patch("core.storage_facade.detect_block_devices_for_inspect", return_value=fake):
            with mock.patch("core.storage_facade.classify_devices_for_inspect", return_value=fake) as clf:
                out = list_classified_block_devices_for_inspect()
        clf.assert_called_once_with(fake)
        self.assertEqual(out, fake)

    def test_inspect_storage_list_block_devices(self) -> None:
        with mock.patch(
            "core.storage_facade.list_classified_block_devices_for_inspect",
            return_value=[{"device": "/dev/sdb", "type": "disk"}],
        ):
            rows = list_block_devices()
        self.assertEqual(len(rows), 1)

    def test_list_physical_disk_paths(self) -> None:
        with mock.patch(
            "core.storage_facade.list_disk_blockdevice_nodes",
            return_value=[{"name": "sdb", "type": "disk"}],
        ):
            paths = list_physical_disk_paths()
        self.assertEqual(paths, ["/dev/sdb"])

    def test_inspect_list_physical_disks(self) -> None:
        with mock.patch("core.storage_facade.list_physical_disk_paths", return_value=["/dev/sda"]):
            self.assertEqual(list_physical_disks(), ["/dev/sda"])

    def test_discover_mounts_flat_delegates(self) -> None:
        with mock.patch("core.storage_discovery.discover_findmnt_mounts_flat", return_value=[{"target": "/"}]):
            mounts = discover_mounts_flat()
        self.assertEqual(mounts[0]["target"], "/")

    def test_probe_contract_public_safe(self) -> None:
        contract = get_readonly_storage_probe_contract()
        self.assertIn("facade_contract_version", contract)
        self.assertIn("storage_inventory", contract)
        self.assertNotIn("password", str(contract).lower())

    def test_deploy_runner_plan_includes_facade_contract(self) -> None:
        with mock.patch("deploy.runner_rescue_storage_discovery.resolve_handoff_path", return_value=(mock.MagicMock(), None)):
            with mock.patch("deploy.runner_rescue_storage_discovery.guard_handoff_overwrite", return_value=None):
                with mock.patch("deploy.runner_rescue_storage_discovery.write_json_handoff", return_value=None):
                    with mock.patch("deploy.runner_rescue_storage_discovery.ensure_rescue_workspace_dirs"):
                        plan = build_rescue_storage_discovery_plan(explicit_overwrite=True)
        body = plan.get("rescue_storage_discovery_plan") or {}
        self.assertIn("facade_contract", body)


if __name__ == "__main__":
    unittest.main()
