"""PI-RS-HW-COMPAT-PROVISION-001 Phase 5: gpu_detection.py + gpu_driver_resolver.py tests.

Fixture groups per spec PHASE 17: Intel+Intel-GPU, AMD+AMD-GPU, NVIDIA without
matching kernel module, AMD disabled via nomodeset, unknown PCI GPU.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.gpu_detection import build_gpu_detection_diagnostics, build_gpu_report
from core.gpu_driver_resolver import build_gpu_driver_resolver_diagnostics, resolve_gpu_driver_plan
from core.hardware_contracts import Bus, HardwareDevice, HardwareDriverState


def _gpu_device(device_id, vendor_id, product_id, name, driver=None, modules=()) -> HardwareDevice:
    return HardwareDevice(
        device_id=device_id,
        device_class="pci",
        bus=Bus.PCI,
        vendor_id=vendor_id,
        product_id=product_id,
        product_name=name,
        driver=HardwareDriverState(kernel_driver_in_use=driver, kernel_modules_loaded=tuple(modules)),
    )


class TestGpuDetectionFixtures(unittest.TestCase):
    def test_intel_igpu_ready_with_connector(self) -> None:
        devices = [_gpu_device("pci:00:02.0", "8086", "a780", "VGA compatible controller: Intel UHD", driver="i915")]
        reports = build_gpu_report(pci_devices=devices, sysfs_root=Path("/nonexistent-xyz"))
        self.assertEqual(len(reports), 1)
        r = reports[0]
        self.assertEqual(r["vendor"], "intel")
        self.assertEqual(r["gpu_type"], "integrated")
        # No DRM sysfs available under the fake root -> never "ready" without connector evidence.
        self.assertEqual(r["gpu_status"], "limited")
        self.assertTrue(r["physical_test_required"])

    def test_amd_dgpu_driver_missing(self) -> None:
        devices = [_gpu_device("pci:01:00.0", "1002", "73df", "VGA compatible controller: AMD Radeon RX 6700")]
        reports = build_gpu_report(pci_devices=devices, sysfs_root=Path("/nonexistent-xyz"))
        r = reports[0]
        self.assertEqual(r["vendor"], "amd")
        self.assertEqual(r["gpu_type"], "discrete")
        self.assertEqual(r["gpu_status"], "driver_missing")

    def test_nvidia_without_matching_kernel_module(self) -> None:
        devices = [_gpu_device("pci:01:00.0", "10de", "249d", "3D controller: NVIDIA Corporation")]
        reports = build_gpu_report(pci_devices=devices, sysfs_root=Path("/nonexistent-xyz"))
        r = reports[0]
        self.assertEqual(r["vendor"], "nvidia")
        self.assertEqual(r["gpu_status"], "driver_missing")
        self.assertIn("nouveau", r["driver_candidates"])
        self.assertIn("nvidia", r["driver_candidates"])

    def test_amd_disabled_by_nomodeset(self) -> None:
        devices = [_gpu_device("pci:01:00.0", "1002", "73df", "VGA compatible controller: AMD Radeon RX 6700", driver="amdgpu")]
        reports = build_gpu_report(pci_devices=devices, cmdline_raw="root=/dev/sda1 nomodeset quiet", sysfs_root=Path("/nonexistent-xyz"))
        r = reports[0]
        self.assertEqual(r["gpu_status"], "disabled_by_cmdline")
        self.assertIn("nomodeset", r["disabling_cmdline_params"])
        self.assertEqual(r["gui_boot_recommendation"], "safe_tui_only")
        self.assertEqual(r["safe_boot_profile"], "remove_nomodeset_recommended")

    def test_unknown_pci_gpu_stays_unknown_not_guessed(self) -> None:
        devices = [_gpu_device("pci:02:00.0", "ffff", "ffff", "VGA compatible controller: Mystery Chip")]
        reports = build_gpu_report(pci_devices=devices, sysfs_root=Path("/nonexistent-xyz"))
        r = reports[0]
        self.assertEqual(r["vendor"], "unknown")
        self.assertEqual(r["gpu_status"], "unknown")

    def test_non_gpu_pci_devices_are_excluded(self) -> None:
        devices = [
            HardwareDevice(device_id="pci:00:1f.3", device_class="pci", bus=Bus.PCI, product_name="Audio device"),
        ]
        reports = build_gpu_report(pci_devices=devices, sysfs_root=Path("/nonexistent-xyz"))
        self.assertEqual(reports, [])

    def test_diagnostics_never_touches_blacklist(self) -> None:
        diag = build_gpu_detection_diagnostics()
        self.assertFalse(diag["blacklist_modified"])


class TestGpuDriverResolver(unittest.TestCase):
    def test_nvidia_proprietary_is_optional_not_default(self) -> None:
        entry = {
            "device_id": "pci:01:00.0",
            "vendor": "nvidia",
            "driver_in_use": "nouveau",
            "driver_candidates": ["nouveau", "nvidia"],
            "gpu_status": "limited",
        }
        plan = resolve_gpu_driver_plan(entry)
        self.assertEqual(plan["recommended_driver"], "nouveau")
        self.assertIn("nvidia", plan["alternative_drivers"])
        self.assertIn("proprietary_driver_available_as_optional_review_required", plan["warnings"])

    def test_driver_missing_recommends_open_source_first(self) -> None:
        entry = {
            "device_id": "pci:01:00.0",
            "vendor": "nvidia",
            "driver_in_use": None,
            "driver_candidates": ["nouveau", "nvidia"],
            "gpu_status": "driver_missing",
        }
        plan = resolve_gpu_driver_plan(entry)
        self.assertEqual(plan["recommended_driver"], "nouveau")
        self.assertEqual(plan["driver_type"], "kernel_in_tree")
        self.assertFalse(plan["live_activation_possible"])
        self.assertFalse(plan["persistent_install_possible"])

    def test_no_auto_install_no_mok_management(self) -> None:
        diag = build_gpu_driver_resolver_diagnostics()
        self.assertFalse(diag["auto_install"])
        self.assertFalse(diag["mok_key_management"])


if __name__ == "__main__":
    unittest.main()
