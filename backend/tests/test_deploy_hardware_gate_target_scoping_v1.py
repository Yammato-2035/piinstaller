"""Deploy hardware gate target-scoping tests."""

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


mod = _load("deploy/hardware_gate.py", "setuphelfer_hardware_gate_target_scoping_test")


def _inspect(
    *,
    system_type: str = "EMPTY",
    target_device: str = "/dev/sdz",
    removable: bool = True,
    transport: str = "usb",
    partitions: list[dict] | None = None,
    fstype: str | None = None,
) -> dict:
    return {
        "classification": {"system_type": system_type},
        "storage": {
            "devices_classified": [
                {
                    "device": target_device,
                    "type": "disk",
                    "size": "16GB",
                    "transport": transport,
                    "removable": removable,
                    "partitions": partitions or [],
                }
            ],
            "devices_raw": [
                {
                    "device": target_device,
                    "type": "disk",
                    "size": "16GB",
                    "transport": transport,
                    "removable": removable,
                    "partitions": partitions or [],
                }
            ],
        },
        "filesystems": {"detected": ({target_device: {"type": fstype}} if fstype else {})},
    }


def _safety(device: str = "/dev/sdz", reason_code: str = "SAFETY_EMPTY_DISK", write_allowed: bool = True) -> dict:
    return {"policy_code": "safety.summary.v1", "targets": [{"device": device, "reason_code": reason_code, "write_allowed": write_allowed}]}


def _report(inspect_result: dict, safety_summary: dict, target_device: str = "/dev/sdz") -> dict:
    return mod.build_hardware_gate_report(
        {
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
    )


class TestDeployHardwareGateTargetScopingV1(unittest.TestCase):
    def test_global_dualboot_does_not_hard_block_clean_target(self):
        out = _report(_inspect(system_type="DUALBOOT"), _safety())
        self.assertNotEqual(out["report_status"], "blocked")
        self.assertNotIn("DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT", out["blocked_reasons"])

    def test_global_unknown_only_review_required_for_clean_target(self):
        out = _report(_inspect(system_type="UNKNOWN"), _safety())
        self.assertIn(out["readiness_level"], {"review_required", "test_ready"})
        self.assertNotEqual(out["report_status"], "blocked")

    def test_target_dualboot_still_blocked(self):
        inspect_result = _inspect(
            system_type="EMPTY",
            partitions=[
                {"device": "/dev/sdz1", "fstype": "ntfs"},
                {"device": "/dev/sdz2", "fstype": "ext4"},
            ],
        )
        out = _report(inspect_result, _safety())
        self.assertEqual(out["report_status"], "blocked")
        self.assertIn("DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT", out["blocked_reasons"])

    def test_target_windows_still_blocked(self):
        inspect_result = _inspect(
            system_type="EMPTY",
            partitions=[{"device": "/dev/sdz1", "fstype": "ntfs"}],
        )
        out = _report(inspect_result, _safety())
        self.assertEqual(out["report_status"], "blocked")
        self.assertIn("DEPLOY_REAL_WRITE_BLOCKED_WINDOWS", out["blocked_reasons"])

    def test_target_mounted_still_blocked(self):
        inspect_result = _inspect(
            partitions=[{"device": "/dev/sdz1", "mountpoint": "/media/test"}],
        )
        out = _report(inspect_result, _safety())
        self.assertEqual(out["report_status"], "blocked")
        self.assertIn("DEPLOY_REAL_WRITE_BLOCKED_MOUNTED", out["blocked_reasons"])

    def test_clean_removable_target_can_be_test_ready(self):
        out = _report(_inspect(system_type="EMPTY"), _safety())
        self.assertEqual(out["report_status"], "ok")
        self.assertEqual(out["readiness_level"], "test_ready")
        self.assertTrue(out["eligible"])

    def test_partition_target_resolves_parent_disk(self):
        inspect_result = _inspect(
            target_device="/dev/sdz",
            partitions=[{"device": "/dev/sdz1", "fstype": "exfat", "mountpoint": None}],
        )
        safety_summary = _safety(device="/dev/sdz1", reason_code="SAFETY_EMPTY_DISK", write_allowed=True)
        out = _report(inspect_result, safety_summary, target_device="/dev/sdz1")
        self.assertNotEqual(out["report_status"], "blocked")

    def test_multiple_devices_are_scoped_by_target(self):
        inspect_result = {
            "classification": {"system_type": "DUALBOOT"},
            "storage": {
                "devices_classified": [
                    {
                        "device": "/dev/sda",
                        "type": "disk",
                        "size": "512GB",
                        "transport": "sata",
                        "removable": False,
                        "partitions": [{"device": "/dev/sda1", "fstype": "ext4", "mountpoint": "/"}],
                    },
                    {
                        "device": "/dev/sdb",
                        "type": "disk",
                        "size": "32GB",
                        "transport": "usb",
                        "removable": True,
                        "partitions": [{"device": "/dev/sdb1", "fstype": "exfat", "mountpoint": None}],
                    },
                ],
                "devices_raw": [],
            },
            "filesystems": {"detected": {}},
        }
        safety_summary = {
            "policy_code": "safety.summary.v1",
            "targets": [
                {"device": "/dev/sda", "reason_code": "SAFETY_SYSTEM_DISK", "write_allowed": False},
                {"device": "/dev/sdb", "reason_code": "SAFETY_EMPTY_DISK", "write_allowed": True},
            ],
        }
        out = _report(inspect_result, safety_summary, target_device="/dev/sdb")
        self.assertNotEqual(out["report_status"], "blocked")
        self.assertNotIn("DEPLOY_REAL_WRITE_BLOCKED_SYSTEM_DISK", out["blocked_reasons"])


if __name__ == "__main__":
    unittest.main()
