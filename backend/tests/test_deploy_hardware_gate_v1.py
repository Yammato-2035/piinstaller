"""Deploy hardware gate tests (read-only and advisory)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

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


mod = _load("deploy/hardware_gate.py", "setuphelfer_hardware_gate_test")
routes_mod = _load("deploy/routes.py", "setuphelfer_hardware_gate_routes_test")


def _inspect(system_type: str = "EMPTY", *, removable: bool = True, transport: str = "usb", device: str = "/dev/sdz", partitions: list[dict] | None = None, ro: bool = False):
    return {
        "classification": {"system_type": system_type},
        "storage": {"devices_classified": [{"device": device, "size": "16GB", "transport": transport, "removable": removable, "ro": ro, "partitions": partitions or []}]},
        "filesystems": {"detected": {}},
    }


def _safety(reason_code: str = "SAFETY_EMPTY_DISK", allowed: bool = True, device: str = "/dev/sdz"):
    return {"policy_code": "safety.summary.v1", "targets": [{"device": device, "reason_code": reason_code, "write_allowed": allowed}]}


def _harness(ok: bool = True):
    if ok:
        return {"execute_code": "DEPLOY_WRITE_HARNESS_COMPLETED", "sha256_matches": True, "single_use_code": "DEPLOY_WRITE_HARNESS_SESSION_ALREADY_USED", "host_changes_detected": False}
    return {"execute_code": "DEPLOY_WRITE_HARNESS_FAILED"}


class TestDeployHardwareGateV1(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        self.client = TestClient(app)

    def _report(self, **kwargs):
        req = {
            "target_device": "/dev/sdz",
            "inspect_result": _inspect(),
            "safety_summary": _safety(),
            "write_harness_result": _harness(True),
            "final_confirmation_result": {"code": "DEPLOY_FINAL_CONFIRMATION_READY"},
            "real_write_guard_result": {"code": "DEPLOY_REAL_WRITE_READY"},
        }
        req.update(kwargs)
        return mod.build_hardware_gate_report(req)

    def test_systemdisk_blocked(self):
        r = self._report(safety_summary=_safety("SAFETY_SYSTEM_DISK", False))
        self.assertEqual(r["report_status"], "blocked")

    def test_mounted_blocked(self):
        r = self._report(inspect_result=_inspect(partitions=[{"device": "/dev/sdz1", "mountpoint": "/mnt/a"}]))
        self.assertIn("DEPLOY_REAL_WRITE_BLOCKED_MOUNTED", r["blocked_reasons"])

    def test_non_removable_blocked(self):
        r = self._report(inspect_result=_inspect(removable=False))
        self.assertIn("DEPLOY_REAL_WRITE_BLOCKED_NON_REMOVABLE", r["blocked_reasons"])

    def test_windows_blocked(self):
        r = self._report(
            inspect_result=_inspect(
                system_type="EMPTY",
                partitions=[{"device": "/dev/sdz1", "fstype": "ntfs"}],
            )
        )
        self.assertIn("DEPLOY_REAL_WRITE_BLOCKED_WINDOWS", r["blocked_reasons"])

    def test_dualboot_blocked(self):
        r = self._report(
            inspect_result=_inspect(
                system_type="EMPTY",
                partitions=[
                    {"device": "/dev/sdz1", "fstype": "ntfs"},
                    {"device": "/dev/sdz2", "fstype": "ext4"},
                ],
            )
        )
        self.assertIn("DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT", r["blocked_reasons"])

    def test_lvm_blocked(self):
        r = self._report(inspect_result=_inspect(device="/dev/mapper/vg-lv"), target_device="/dev/mapper/vg-lv", safety_summary=_safety(device="/dev/mapper/vg-lv"))
        self.assertIn("DEPLOY_REAL_WRITE_BLOCKED_LVM", r["blocked_reasons"])

    def test_raid_blocked(self):
        r = self._report(inspect_result=_inspect(device="/dev/md0"), target_device="/dev/md0", safety_summary=_safety(device="/dev/md0"))
        self.assertIn("DEPLOY_REAL_WRITE_BLOCKED_RAID", r["blocked_reasons"])

    def test_loop_blocked(self):
        r = self._report(inspect_result=_inspect(device="/dev/loop0"), target_device="/dev/loop0", safety_summary=_safety(device="/dev/loop0"))
        self.assertIn("DEPLOY_REAL_WRITE_BLOCKED_LOOP", r["blocked_reasons"])

    def test_readonly_blocked(self):
        r = self._report(inspect_result=_inspect(ro=True))
        self.assertIn("DEPLOY_REAL_WRITE_BLOCKED_READONLY", r["blocked_reasons"])

    def test_valid_usb_stick_eligible(self):
        v = mod.validate_test_device("/dev/sdz", _inspect(transport="usb"), _safety())
        self.assertTrue(v["eligible"])
        self.assertIn(v["device_class"], {"usb_flash", "usb_ssd", "usb_hdd"})

    def test_valid_sd_card_eligible(self):
        v = mod.validate_test_device("/dev/sdz", _inspect(transport="sdcard"), _safety())
        self.assertTrue(v["eligible"])
        self.assertEqual(v["device_class"], "sd_card")

    def test_unknown_media_review_or_block(self):
        r = self._report(inspect_result=_inspect(transport="sata"))
        self.assertIn(r["readiness_level"], {"blocked", "review_required"})

    def test_operator_protocol_stable(self):
        p = mod.build_operator_protocol({"target_device": "/dev/sdz"})
        self.assertTrue(p["protocol_id"])
        self.assertTrue(len(p["protocol_steps"]) >= 10)
        self.assertTrue("ABORT_IF_SNAPSHOT_CHANGED" in p["abort_conditions"])

    def test_no_execute_route(self):
        self.assertEqual(self.client.post("/api/deploy/hardware-gate/execute", json={}).status_code, 404)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "hardware_gate.py").read_text(encoding="utf-8").lower()
        forbidden = ["subprocess.", "os.system(", "dd ", "mkfs", "parted", "fdisk", "sfdisk", "mount(", "umount(", "losetup", "wipefs", "grub-install", "chroot", "systemctl", "sudo"]
        for x in forbidden:
            self.assertNotIn(x, src)


if __name__ == "__main__":
    unittest.main()
