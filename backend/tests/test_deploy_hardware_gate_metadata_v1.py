"""Deploy hardware gate metadata completeness tests."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load(rel: str, name: str):
    p = _BACKEND / rel
    spec = importlib.util.spec_from_file_location(name, p)
    if not spec or not spec.loader:
        raise ImportError(rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


mod = _load("deploy/hardware_gate.py", "setuphelfer_hardware_gate_metadata_test")


def _base_request(target_device: str, inspect_result: dict, safety_summary: dict) -> dict:
    return {
        "target_device": target_device,
        "inspect_result": inspect_result,
        "safety_summary": safety_summary,
        "write_harness_result": {
            "execute_code": "DEPLOY_WRITE_HARNESS_COMPLETED",
            "sha256_matches": True,
            "single_use_code": "DEPLOY_WRITE_HARNESS_SESSION_ALREADY_USED",
            "host_changes_detected": False,
        },
        "final_confirmation_result": {"code": "DEPLOY_FINAL_CONFIRMATION_READY"},
        "real_write_guard_result": {"code": "DEPLOY_REAL_WRITE_READY"},
    }


def _safety(device: str, reason_code: str = "SAFETY_EMPTY_DISK", write_allowed: bool = True) -> dict:
    return {"policy_code": "safety.summary.v1", "targets": [{"device": device, "reason_code": reason_code, "write_allowed": write_allowed}]}


class TestDeployHardwareGateMetadataV1(unittest.TestCase):
    def test_complete_metadata_results_in_test_ready(self):
        inspect_result = {
            "classification": {"system_type": "EMPTY"},
            "storage": {
                "devices_classified": [
                    {
                        "device": "/dev/sdb",
                        "type": "disk",
                        "size": "64GB",
                        "transport": "usb",
                        "removable": True,
                        "ro": False,
                        "rotational": 0,
                        "model": "USB Flash",
                        "partitions": [{"device": "/dev/sdb1", "fstype": "exfat", "mountpoint": None}],
                    }
                ]
            },
            "filesystems": {"detected": {}},
        }
        out = mod.build_hardware_gate_report(_base_request("/dev/sdb", inspect_result, _safety("/dev/sdb")))
        self.assertEqual(out["readiness_level"], "test_ready")
        self.assertEqual(out["report_status"], "ok")
        self.assertEqual(out["device_class"], "usb_flash")

    def test_missing_optional_fields_can_still_be_test_ready(self):
        inspect_result = {
            "classification": {"system_type": "EMPTY"},
            "storage": {
                "devices_classified": [
                    {
                        "device": "/dev/sdb",
                        "type": "disk",
                        "size": "64GB",
                        "partitions": [{"device": "/dev/sdb1", "mountpoint": None}],
                    }
                ]
            },
            "filesystems": {"detected": {}},
        }
        out = mod.build_hardware_gate_report(_base_request("/dev/sdb", inspect_result, _safety("/dev/sdb")))
        self.assertEqual(out["readiness_level"], "test_ready")
        self.assertFalse(out["blocked_reasons"])

    def test_parent_disk_metadata_is_used_for_child_target(self):
        inspect_result = {
            "classification": {"system_type": "EMPTY"},
            "storage": {
                "devices_classified": [
                    {
                        "device": "/dev/sdb",
                        "type": "disk",
                        "size": "64GB",
                        "transport": "usb",
                        "removable": True,
                        "rotational": 0,
                        "partitions": [{"device": "/dev/sdb1", "mountpoint": None, "fstype": "exfat"}],
                    }
                ],
                "devices_raw": [],
            },
            "filesystems": {"detected": {}},
        }
        out = mod.build_hardware_gate_report(_base_request("/dev/sdb1", inspect_result, _safety("/dev/sdb1")))
        self.assertEqual(out["readiness_level"], "test_ready")
        self.assertEqual((out.get("partition_summary") or {}).get("target_device_resolved"), "/dev/sdb1")

    def test_usb_rotational_zero_classified_as_flash_or_ssd(self):
        inspect_result = {
            "classification": {"system_type": "EMPTY"},
            "storage": {"devices_classified": [{"device": "/dev/sdb", "type": "disk", "size": "64GB", "transport": "usb", "removable": True, "rotational": 0, "partitions": []}]},
            "filesystems": {"detected": {}},
        }
        out = mod.build_hardware_gate_report(_base_request("/dev/sdb", inspect_result, _safety("/dev/sdb")))
        self.assertIn(out["device_class"], {"usb_flash", "usb_ssd"})

    def test_usb_rotational_one_classified_as_hdd(self):
        inspect_result = {
            "classification": {"system_type": "EMPTY"},
            "storage": {"devices_classified": [{"device": "/dev/sdb", "type": "disk", "size": "64GB", "transport": "usb", "removable": True, "rotational": 1, "partitions": []}]},
            "filesystems": {"detected": {}},
        }
        out = mod.build_hardware_gate_report(_base_request("/dev/sdb", inspect_result, _safety("/dev/sdb")))
        self.assertEqual(out["device_class"], "usb_hdd")

    def test_mmc_device_classified_as_sd_card(self):
        inspect_result = {
            "classification": {"system_type": "EMPTY"},
            "storage": {"devices_classified": [{"device": "/dev/mmcblk0", "type": "disk", "size": "64GB", "transport": "", "removable": True, "partitions": []}]},
            "filesystems": {"detected": {}},
        }
        out = mod.build_hardware_gate_report(_base_request("/dev/mmcblk0", inspect_result, _safety("/dev/mmcblk0")))
        self.assertEqual(out["device_class"], "sd_card")

    def test_hard_blocks_still_apply(self):
        cases = [
            (
                {"device": "/dev/sdb", "type": "disk", "size": "64GB", "transport": "usb", "removable": True, "partitions": [{"device": "/dev/sdb1", "mountpoint": "/mnt/x"}]},
                "SAFETY_EMPTY_DISK",
                True,
                "DEPLOY_REAL_WRITE_BLOCKED_MOUNTED",
            ),
            (
                {"device": "/dev/sdb", "type": "disk", "size": "64GB", "transport": "usb", "removable": True, "ro": True, "partitions": []},
                "SAFETY_EMPTY_DISK",
                True,
                "DEPLOY_REAL_WRITE_BLOCKED_READONLY",
            ),
            (
                {"device": "/dev/sdb", "type": "disk", "size": "64GB", "transport": "usb", "removable": True, "partitions": [{"device": "/dev/sdb1", "fstype": "ntfs"}]},
                "SAFETY_WINDOWS_DETECTED",
                False,
                "DEPLOY_REAL_WRITE_BLOCKED_WINDOWS",
            ),
            (
                {"device": "/dev/sdb", "type": "disk", "size": "64GB", "transport": "usb", "removable": True, "partitions": [{"device": "/dev/sdb1", "fstype": "ntfs"}, {"device": "/dev/sdb2", "fstype": "ext4"}]},
                "SAFETY_DUALBOOT",
                False,
                "DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT",
            ),
            (
                {"device": "/dev/md0", "type": "disk", "size": "64GB", "transport": "usb", "removable": True, "partitions": []},
                "SAFETY_EMPTY_DISK",
                True,
                "DEPLOY_REAL_WRITE_BLOCKED_RAID",
            ),
            (
                {"device": "/dev/mapper/vg-lv", "type": "disk", "size": "64GB", "transport": "usb", "removable": True, "partitions": []},
                "SAFETY_EMPTY_DISK",
                True,
                "DEPLOY_REAL_WRITE_BLOCKED_LVM",
            ),
            (
                {"device": "/dev/loop0", "type": "disk", "size": "64GB", "transport": "usb", "removable": True, "partitions": []},
                "SAFETY_EMPTY_DISK",
                True,
                "DEPLOY_REAL_WRITE_BLOCKED_LOOP",
            ),
        ]
        for dev, reason, allowed, code in cases:
            inspect_result = {"classification": {"system_type": "EMPTY"}, "storage": {"devices_classified": [dev]}, "filesystems": {"detected": {}}}
            out = mod.build_hardware_gate_report(_base_request(dev["device"], inspect_result, _safety(dev["device"], reason, allowed)))
            self.assertIn(code, out["blocked_reasons"])


if __name__ == "__main__":
    unittest.main()
