"""PI-RS-HW-COMPAT-PROVISION-001 Phase 4: mainboard_chipset_detection.py tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_contracts import Bus, HardwareDevice
from core.mainboard_chipset_detection import (
    build_mainboard_chipset_detection_diagnostics,
    build_mainboard_chipset_report,
    classify_platform_class,
    find_bridge_devices,
    resolve_chipset_from_host_bridge,
)


def _pci(device_id: str, vendor_id: str | None, product_id: str | None, product_name: str) -> HardwareDevice:
    return HardwareDevice(
        device_id=device_id,
        device_class="pci",
        bus=Bus.PCI,
        vendor_id=vendor_id,
        product_id=product_id,
        product_name=product_name,
    )


class TestPlatformClassification(unittest.TestCase):
    def test_raspberry_pi_is_single_board_computer(self) -> None:
        self.assertEqual(classify_platform_class(dmi_fields={}, is_raspberry_pi=True), "single_board_computer")

    def test_laptop_chassis_type(self) -> None:
        self.assertEqual(
            classify_platform_class(dmi_fields={"chassis_type": "10"}, is_raspberry_pi=False), "laptop"
        )

    def test_server_chassis_type(self) -> None:
        self.assertEqual(
            classify_platform_class(dmi_fields={"chassis_type": "23"}, is_raspberry_pi=False), "server"
        )

    def test_no_dmi_fields_is_unknown_not_guessed(self) -> None:
        self.assertEqual(classify_platform_class(dmi_fields={}, is_raspberry_pi=False), "unknown")


class TestChipsetResolution(unittest.TestCase):
    def test_curated_host_bridge_hit_is_identified(self) -> None:
        devices = [_pci("pci:0000:00:00.0", "8086", "7a04", "Host bridge/DRAM registers")]
        name, status = resolve_chipset_from_host_bridge(devices)
        self.assertEqual(status, "identified")
        self.assertIn("Alder Lake", name or "")

    def test_unknown_host_bridge_is_review_required_not_guessed(self) -> None:
        devices = [_pci("pci:0000:00:00.0", "ffff", "ffff", "Host bridge (unknown chip)")]
        name, status = resolve_chipset_from_host_bridge(devices)
        self.assertIsNone(name)
        self.assertEqual(status, "review_required")

    def test_no_host_bridge_found_is_review_required(self) -> None:
        devices = [_pci("pci:0000:01:00.0", "10de", "249d", "3D controller")]
        name, status = resolve_chipset_from_host_bridge(devices)
        self.assertIsNone(name)
        self.assertEqual(status, "review_required")

    def test_bridge_devices_grouped_by_role(self) -> None:
        devices = [
            _pci("pci:00:00.0", "8086", "7a04", "Host bridge/DRAM registers"),
            _pci("pci:00:1f.0", "8086", "7a06", "ISA bridge"),
            _pci("pci:00:1c.0", "8086", "7a0e", "PCI bridge (PCIe Root Port)"),
        ]
        grouped = find_bridge_devices(devices)
        self.assertEqual(len(grouped["host_bridge"]), 1)
        self.assertEqual(len(grouped["isa_lpc_bridge"]), 1)
        self.assertEqual(len(grouped["pcie_root_port"]), 1)


class TestFullReport(unittest.TestCase):
    def test_report_shape_with_known_chipset(self) -> None:
        devices = [_pci("pci:00:00.0", "8086", "7a04", "Host bridge/DRAM registers")]
        report = build_mainboard_chipset_report(
            dmi_fields={"sys_vendor": "ASUSTeK COMPUTER INC.", "product_name": "ROG Strix G513QM_G513QM"},
            pci_devices=devices,
            is_raspberry_pi=False,
        )
        self.assertEqual(report["system_vendor"], "ASUSTeK COMPUTER INC.")
        self.assertEqual(report["chipset_status"], "identified")

    def test_report_never_crashes_without_dmi_or_pci(self) -> None:
        report = build_mainboard_chipset_report(dmi_fields={}, pci_devices=[], is_raspberry_pi=False)
        self.assertEqual(report["chipset_status"], "review_required")
        self.assertEqual(report["platform_class"], "unknown")

    def test_diagnostics_read_only(self) -> None:
        diag = build_mainboard_chipset_detection_diagnostics()
        self.assertTrue(diag["read_only"])
        self.assertFalse(diag["writes_allowed"])


if __name__ == "__main__":
    unittest.main()
