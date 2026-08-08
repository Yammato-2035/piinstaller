"""PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007: driver_firmware_gap_engine tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from rescue.driver_firmware_gap_engine import build_driver_gap_report


class TestDriverFirmwareGapEngineV1(unittest.TestCase):
    def test_nvidia_intentional_blacklist_not_tested(self) -> None:
        report = build_driver_gap_report(
            [
                {
                    "device_id": "pci:0000:01:00.0",
                    "device_class": "gpu",
                    "vendor_id": "10de",
                    "product_id": "2520",
                    "modalias": "pci:v000010DEd00002520sv00001043sd00001C8Cbc03sc00i00",
                    "bound_driver": "",
                    "candidate_modules": ["nvidia", "nouveau"],
                    "module_present": True,
                    "module_loaded": False,
                    "firmware_present": True,
                    "firmware_requested": "",
                    "package_candidates": ["nvidia-driver"],
                    "pci_address": "0000:01:00.0",
                }
            ],
            cmdline="quiet splash modprobe.blacklist=nvidia,nvidia_drm,nvidia_modeset,nouveau",
            kernel_release="6.8.0-rog",
        )
        self.assertEqual(len(report["devices"]), 1)
        entry = report["devices"][0]
        self.assertEqual(entry["status"], "driver_intentionally_disabled")
        self.assertEqual(entry["operational_validation"], "not_tested")
        self.assertEqual(entry["hardware_id"], "pci:0000:01:00.0")
        self.assertTrue(entry["modalias"])
        self.assertIn(entry["expected_module"], ("nvidia", "nouveau"))
        self.assertNotIn("nvidia broken", (entry.get("technical_summary") or "").lower())
        self.assertFalse(report["writes_allowed"])

    def test_operational_amdgpu_concrete_fields(self) -> None:
        report = build_driver_gap_report(
            [
                {
                    "device_id": "pci:0000:06:00.0",
                    "vendor_id": "1002",
                    "product_id": "1638",
                    "modalias": "pci:v00001002d00001638",
                    "bound_driver": "amdgpu",
                    "candidate_modules": ["amdgpu"],
                    "module_present": True,
                    "module_loaded": True,
                    "firmware_present": True,
                    "firmware_requested": "amdgpu/green_sardine_dmcub.bin",
                    "package_candidates": ["firmware-amd-graphics"],
                }
            ],
            cmdline="setuphelfer_asus_profile=ASUS-01",
            kernel_release="6.8.0-rog",
        )
        entry = report["devices"][0]
        for key in (
            "hardware_id",
            "modalias",
            "expected_module",
            "module_present",
            "module_loaded",
            "firmware_request",
            "firmware_file_present",
            "package_candidates",
            "risk",
            "confidence",
            "status",
        ):
            self.assertIn(key, entry)
        self.assertEqual(entry["status"], "operational")
        self.assertEqual(entry["expected_module"], "amdgpu")
        self.assertTrue(entry["module_present"])
        self.assertTrue(entry["module_loaded"])
        self.assertTrue(entry["firmware_file_present"])
        self.assertIn("firmware-amd-graphics", entry["package_candidates"])

    def test_driver_missing_names_module(self) -> None:
        report = build_driver_gap_report(
            [
                {
                    "device_id": "pci:0000:03:00.0",
                    "vendor_id": "14e4",
                    "modalias": "pci:v000014E4d000043F0",
                    "candidate_modules": ["brcmfmac"],
                    "module_present": False,
                    "module_loaded": False,
                    "package_candidates": ["broadcom-sta-dkms"],
                }
            ]
        )
        entry = report["devices"][0]
        self.assertEqual(entry["status"], "driver_missing")
        self.assertEqual(entry["expected_module"], "brcmfmac")
        self.assertFalse(entry["module_present"])
        self.assertGreaterEqual(report["gap_count"], 1)

    def test_firmware_missing_status(self) -> None:
        report = build_driver_gap_report(
            [
                {
                    "device_id": "pci:0000:04:00.0",
                    "vendor_id": "8086",
                    "bound_driver": "iwlwifi",
                    "candidate_modules": ["iwlwifi"],
                    "module_present": True,
                    "module_loaded": False,
                    "firmware_requested": "iwlwifi-ty-a0-gf-a0-72.ucode",
                    "firmware_present": False,
                    "package_candidates": ["linux-firmware"],
                }
            ]
        )
        entry = report["devices"][0]
        self.assertEqual(entry["status"], "firmware_missing")
        self.assertEqual(entry["firmware_request"], "iwlwifi-ty-a0-gf-a0-72.ucode")
        self.assertFalse(entry["firmware_file_present"])


if __name__ == "__main__":
    unittest.main()
