"""
SAFE-DEVICE-1: Schreibschutz, Klassifikation, validate_write_target (ohne echte Writes).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from subprocess import CompletedProcess
_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.safe_device import (
    WriteTargetProtectionError,
    list_classified_devices,
    validate_write_target,
    write_safe_prefixes_resolved,
)


def _lsblk_system_disk() -> dict:
    return {
        "blockdevices": [
            {
                "path": "/dev/nvme0n1",
                "name": "nvme0n1",
                "type": "disk",
                "size": "500G",
                "rm": "0",
                "ro": False,
                "tran": "nvme",
                "children": [
                    {
                        "path": "/dev/nvme0n1p1",
                        "name": "nvme0n1p1",
                        "type": "part",
                        "fstype": "ext4",
                        "mountpoints": ["/"],
                        "size": "500G",
                    }
                ],
            }
        ]
    }


def _lsblk_windows_disk() -> dict:
    return {
        "blockdevices": [
            {
                "path": "/dev/nvme1n1",
                "name": "nvme1n1",
                "type": "disk",
                "size": "500G",
                "rm": "0",
                "ro": False,
                "tran": "nvme",
                "children": [
                    {
                        "path": "/dev/nvme1n1p1",
                        "name": "nvme1n1p1",
                        "type": "part",
                        "fstype": "vfat",
                        "mountpoints": [],
                        "size": "512M",
                    },
                    {
                        "path": "/dev/nvme1n1p2",
                        "name": "nvme1n1p2",
                        "type": "part",
                        "fstype": "ntfs",
                        "mountpoints": [],
                        "size": "400G",
                    },
                ],
            }
        ]
    }


def _lsblk_safe_usb(mount: str) -> dict:
    return {
        "blockdevices": [
            {
                "path": "/dev/sdb",
                "name": "sdb",
                "type": "disk",
                "size": "32G",
                "rm": "1",
                "ro": False,
                "tran": "usb",
                "children": [
                    {
                        "path": "/dev/sdb1",
                        "name": "sdb1",
                        "type": "part",
                        "fstype": "ext4",
                        "mountpoints": [mount],
                        "size": "32G",
                    }
                ],
            }
        ]
    }


class TestSafeDeviceStorageProtectionV1(unittest.TestCase):
    def test_prefixes_include_setuphelfer(self) -> None:
        prefs = write_safe_prefixes_resolved()
        self.assertTrue(any(str(p).startswith("/mnt/setuphelfer") for p in prefs))

    def test_system_disk_classified(self) -> None:
        def fake_run(argv, **kwargs):
            if argv[:2] == ["lsblk", "-J"]:
                return CompletedProcess(argv, 0, json.dumps(_lsblk_system_disk()), "")
            return CompletedProcess(argv, 1, "", "")

        devs = list_classified_devices(runner=fake_run)
        self.assertTrue(any(d.is_system_disk for d in devs))

    def test_windows_disk_classified_foreign(self) -> None:
        def fake_run(argv, **kwargs):
            if argv[:2] == ["lsblk", "-J"]:
                return CompletedProcess(argv, 0, json.dumps(_lsblk_windows_disk()), "")
            return CompletedProcess(argv, 1, "", "")

        devs = list_classified_devices(runner=fake_run)
        foreign = [d for d in devs if d.is_foreign_os_disk]
        self.assertEqual(len(foreign), 1)
        self.assertFalse(foreign[0].is_write_allowed)

    def test_validate_blocks_system_disk_source(self) -> None:
        mount = "/tmp/setuphelfer-test/safe-dev-v1-mnt"
        Path(mount).mkdir(parents=True, exist_ok=True)

        def fake_run(argv, **kwargs):
            if argv[:2] == ["lsblk", "-J"]:
                return CompletedProcess(argv, 0, json.dumps(_lsblk_system_disk()), "")
            if argv[:2] == ["findmnt", "-J"]:
                body = {
                    "filesystems": [
                        {"source": "/dev/nvme0n1p1", "target": mount, "fstype": "ext4"},
                    ]
                }
                return CompletedProcess(argv, 0, json.dumps(body), "")
            return CompletedProcess(argv, 1, "", "")

        with self.assertRaises(WriteTargetProtectionError) as ctx:
            validate_write_target(Path(mount) / "bk" / "a.tar.gz", runner=fake_run)
        self.assertEqual(ctx.exception.diagnosis_id, "STORAGE-PROTECTION-001")

    def test_validate_blocks_windows_nvme(self) -> None:
        mount = "/tmp/setuphelfer-test/safe-dev-v1-win"
        Path(mount).mkdir(parents=True, exist_ok=True)

        def fake_run(argv, **kwargs):
            if argv[:2] == ["lsblk", "-J"]:
                return CompletedProcess(argv, 0, json.dumps(_lsblk_windows_disk()), "")
            if argv[:2] == ["findmnt", "-J"]:
                body = {
                    "filesystems": [
                        {"source": "/dev/nvme1n1p2", "target": mount, "fstype": "ext4"},
                    ]
                }
                return CompletedProcess(argv, 0, json.dumps(body), "")
            return CompletedProcess(argv, 1, "", "")

        with self.assertRaises(WriteTargetProtectionError) as ctx:
            validate_write_target(Path(mount) / "x.tar.gz", runner=fake_run)
        self.assertEqual(ctx.exception.diagnosis_id, "STORAGE-PROTECTION-003")

    def test_validate_blocks_media_mount(self) -> None:
        with self.assertRaises(WriteTargetProtectionError) as ctx:
            validate_write_target("/media/user/MyStick/backup", runner=None)
        self.assertEqual(ctx.exception.diagnosis_id, "STORAGE-PROTECTION-005")

    def test_validate_allows_safe_test_mount(self) -> None:
        mount = "/tmp/setuphelfer-test/safe-dev-v1-ok"
        Path(mount).mkdir(parents=True, exist_ok=True)

        def fake_run(argv, **kwargs):
            if argv[:2] == ["lsblk", "-J"]:
                return CompletedProcess(argv, 0, json.dumps(_lsblk_safe_usb(mount)), "")
            if argv[:2] == ["findmnt", "-J"]:
                body = {
                    "filesystems": [
                        {"source": "/dev/sdb1", "target": mount, "fstype": "ext4"},
                    ]
                }
                return CompletedProcess(argv, 0, json.dumps(body), "")
            return CompletedProcess(argv, 1, "", "")

        validate_write_target(Path(mount) / "arch.tar.gz", runner=fake_run)

    def test_validate_block_device_raises(self) -> None:
        def fake_run(argv, **kwargs):
            if argv[:2] == ["lsblk", "-J"]:
                return CompletedProcess(argv, 0, json.dumps(_lsblk_system_disk()), "")
            return CompletedProcess(argv, 1, "", "")

        with self.assertRaises(WriteTargetProtectionError):
            validate_write_target("/dev/nvme0n1", runner=fake_run)


class TestDiagnosticsMatcherStorageProtection(unittest.TestCase):
    def test_matcher_maps_storage_signal(self) -> None:
        from core.diagnostics.matcher import match_diagnoses
        from core.diagnostics.models import DiagnosticsAnalyzeRequest

        req = DiagnosticsAnalyzeRequest(
            question="x",
            signals={"storage_protection": "STORAGE-PROTECTION-001"},
        )
        hits = match_diagnoses(req)
        self.assertEqual(hits[0].id, "STORAGE-PROTECTION-001")


if __name__ == "__main__":
    unittest.main()
