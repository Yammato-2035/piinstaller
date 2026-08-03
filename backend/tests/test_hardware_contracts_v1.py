"""PI-RS-HW-COMPAT-PROVISION-001 Phase 2: hardware_contracts.py model tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_contracts import (
    Bus,
    FirmwareStatus,
    HardwareCapability,
    HardwareDevice,
    HardwareDriverState,
    HardwareEvidenceReference,
    HardwareFirmwareState,
    HardwareInventory,
    HardwareIssue,
    HardwarePrivacyFlags,
    HardwareRecommendation,
    PeripheralCapability,
    PlatformIdentity,
    build_hardware_contracts_diagnostics,
)


class TestHardwareContracts(unittest.TestCase):
    def test_hardware_device_default_is_unknown_not_ready(self) -> None:
        dev = HardwareDevice(device_id="pci:0000:00:02.0", device_class="gpu")
        self.assertEqual(dev.operational_status, "unknown")
        self.assertEqual(dev.firmware.status, FirmwareStatus.UNKNOWN)
        self.assertEqual(dev.bus, Bus.UNKNOWN)

    def test_detected_is_not_ready(self) -> None:
        """'erkannt' != 'betriebsbereit' — detection alone must not imply readiness."""
        dev = HardwareDevice(
            device_id="pci:0000:01:00.0",
            device_class="gpu",
            vendor_name="NVIDIA",
            operational_status="driver_missing",
            driver=HardwareDriverState(kernel_driver_candidates=("nouveau", "nvidia")),
        )
        self.assertNotEqual(dev.operational_status, "ready")
        self.assertIn("nouveau", dev.driver.kernel_driver_candidates)

    def test_device_to_dict_roundtrip_shape(self) -> None:
        dev = HardwareDevice(
            device_id="usb:1-2",
            device_class="printer",
            bus=Bus.USB,
            capabilities=(HardwareCapability(name="color_print", supported=False, confidence="low"),),
            issues=(HardwareIssue(code="driver_missing", severity="warning"),),
            recommendations=(HardwareRecommendation(code="show_driver_plan"),),
            evidence=(HardwareEvidenceReference(kind="doc", path="docs/x.md"),),
            privacy=HardwarePrivacyFlags(contains_serial=False),
        )
        d = dev.to_dict()
        self.assertEqual(d["bus"], "usb")
        self.assertEqual(d["capabilities"][0]["name"], "color_print")
        self.assertEqual(d["issues"][0]["code"], "driver_missing")
        self.assertEqual(d["recommendations"][0]["code"], "show_driver_plan")
        self.assertEqual(d["evidence"][0]["path"], "docs/x.md")
        self.assertFalse(d["privacy"]["contains_serial"])

    def test_peripheral_capability_is_independent_per_function(self) -> None:
        printer_fn = PeripheralCapability(function="printer", operational_status="ready")
        scanner_fn = PeripheralCapability(function="scanner", operational_status="unknown")
        self.assertNotEqual(printer_fn.operational_status, scanner_fn.operational_status)

    def test_hardware_inventory_serializes_devices_and_platform(self) -> None:
        platform = PlatformIdentity(platform_class="laptop", architecture="x86_64")
        inv = HardwareInventory(
            run_id="run-1",
            collected_at="2026-08-03T00:00:00Z",
            platform=platform,
            devices=(HardwareDevice(device_id="d1", device_class="cpu"),),
            capability_missing_tools=("dmidecode",),
        )
        d = inv.to_dict()
        self.assertEqual(d["device_count"], 1)
        self.assertEqual(d["platform"]["platform_class"], "laptop")
        self.assertIn("dmidecode", d["capability_missing_tools"])

    def test_diagnostics_is_read_only_self_description(self) -> None:
        diag = build_hardware_contracts_diagnostics()
        self.assertTrue(diag["read_only"])
        self.assertFalse(diag["writes_allowed"])
        self.assertFalse(diag["shell_execution"])
        self.assertIn("HardwareDevice", diag["models"])


if __name__ == "__main__":
    unittest.main()
