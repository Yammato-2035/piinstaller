"""PI-RS-HW-COMPAT-PROVISION-001 Phase 3: hardware_inventory.py collector tests.

All tests use injected fixture text / fixture sysfs trees — no real hardware, no
real subprocess calls, safe to run in CI/sandbox.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_contracts import PlatformIdentity
from core.hardware_inventory import (
    build_hardware_inventory_diagnostics,
    build_hardware_inventory_summary,
    collect_firmware_errors,
    collect_hardware_inventory,
    collect_input_devices,
    collect_kernel_driver_state,
    collect_pci_devices,
    collect_platform_devices,
    collect_storage_controllers,
    collect_usb_devices,
)

LSPCI_NVIDIA_MISMATCH = """00:02.0 VGA compatible controller [0300]: Intel Corporation [8086:9a49]
\tKernel driver in use: i915
\tKernel modules: i915
01:00.0 3D controller [0302]: NVIDIA Corporation [10de:249d]
\tKernel modules: nvidia, nouveau
02:00.0 Non-Volatile memory controller [0108]: Samsung Electronics [144d:a808]
\tKernel driver in use: nvme
"""

LSUSB_SAMPLE = """Bus 001 Device 004: ID 046d:c52b Logitech, Inc. Unifying Receiver
Bus 001 Device 005: ID 0000:0000
Bus 002 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
"""

INPUT_DEVICES_SAMPLE = """I: Bus=0003 Vendor=046d Product=c52b Version=0111
N: Name="Logitech Unifying Receiver"
S: Sysfs=/devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2:1.2/0003:046D:C52B.0003/input/input10
H: Handlers=mouse0 event6

I: Bus=0000 Vendor=0000 Product=0000 Version=0000
N: Name="Some Unnamed Ghost Device"
S: Sysfs=/devices/virtual/input/input99
H: Handlers=event99
"""

LSMOD_SAMPLE = """Module                  Size  Used by
nouveau              2334720  1
nvme                   57344  3
i915                 3162112  4
"""

DMESG_FIRMWARE_SAMPLE = """[    1.234] usb 1-2: firmware: failed to load radeon/R600_rlc.bin (-2)
[    2.345] Bluetooth: hci0: Direct firmware load failed with error -2
[    3.456] random unrelated line
"""


class TestPciUsbCollectors(unittest.TestCase):
    def test_pci_parses_ids_driver_and_modules(self) -> None:
        devices, missing = collect_pci_devices(raw_text=LSPCI_NVIDIA_MISMATCH)
        self.assertEqual(missing, [])
        self.assertEqual(len(devices), 3)
        nvidia = next(d for d in devices if d.vendor_id == "10de")
        self.assertEqual(nvidia.product_id, "249d")
        self.assertIsNone(nvidia.driver.kernel_driver_in_use)  # detected, but no bound driver
        self.assertIn("nouveau", nvidia.driver.kernel_modules_loaded)
        intel = next(d for d in devices if d.vendor_id == "8086")
        self.assertEqual(intel.driver.kernel_driver_in_use, "i915")

    def test_pci_missing_tool_is_capability_missing_not_crash(self) -> None:
        def _raising_runner(*a, **k):
            raise FileNotFoundError("lspci not installed")

        devices, missing = collect_pci_devices(runner=_raising_runner)
        self.assertEqual(devices, [])
        self.assertIn("lspci", missing)

    def test_storage_controllers_subset_of_pci(self) -> None:
        controllers, _ = collect_storage_controllers(raw_text=LSPCI_NVIDIA_MISMATCH)
        self.assertEqual(len(controllers), 1)
        self.assertEqual(controllers[0].driver.kernel_driver_in_use, "nvme")

    def test_usb_parses_known_and_unknown_devices(self) -> None:
        devices, missing = collect_usb_devices(raw_text=LSUSB_SAMPLE)
        self.assertEqual(missing, [])
        self.assertEqual(len(devices), 3)
        logitech = next(d for d in devices if d.vendor_id == "046d")
        self.assertEqual(logitech.product_id, "c52b")
        unknown = next(d for d in devices if d.vendor_id == "0000")
        self.assertEqual(unknown.operational_status, "unknown")

    def test_usb_missing_tool_capability_missing(self) -> None:
        def _raising_runner(*a, **k):
            raise FileNotFoundError("lsusb not installed")

        devices, missing = collect_usb_devices(runner=_raising_runner)
        self.assertEqual(devices, [])
        self.assertIn("lsusb", missing)


class TestInputAndPlatformCollectors(unittest.TestCase):
    def test_input_devices_parsed_without_capturing_keystrokes(self) -> None:
        devices, missing = collect_input_devices(raw_text=INPUT_DEVICES_SAMPLE)
        self.assertEqual(missing, [])
        self.assertEqual(len(devices), 2)
        names = {d.product_name for d in devices}
        self.assertIn("Logitech Unifying Receiver", names)
        # Strict privacy: no key-event or coordinate fields exist anywhere on the model.
        for d in devices:
            d_dict = d.to_dict()
            self.assertNotIn("keys_pressed", d_dict)
            self.assertNotIn("pointer_events", d_dict)

    def test_platform_devices_missing_sysfs_is_capability_missing(self, tmp_root: Path | None = None) -> None:
        devices, missing = collect_platform_devices(sysfs_root=Path("/nonexistent-root-xyz"))
        self.assertEqual(devices, [])
        self.assertIn("sysfs:platform_bus", missing)


class TestKernelStateAndFirmware(unittest.TestCase):
    def test_lsmod_parsed_into_module_map(self) -> None:
        result = collect_kernel_driver_state(raw_text=LSMOD_SAMPLE)
        self.assertIn("nouveau", result["modules"])
        self.assertEqual(result["missing_tools"], [])

    def test_dmesg_firmware_errors_capped_and_no_crash_if_missing(self) -> None:
        result = collect_firmware_errors(raw_text=DMESG_FIRMWARE_SAMPLE)
        self.assertTrue(any("firmware" in line.lower() for line in result["missing_firmware_lines"]))

        def _raising_runner(*a, **k):
            raise FileNotFoundError("dmesg not permitted")

        result2 = collect_firmware_errors(runner=_raising_runner)
        self.assertEqual(result2["missing_firmware_lines"], [])
        self.assertIn("dmesg", result2["missing_tools"])


class TestOrchestrationAndSummary(unittest.TestCase):
    def test_collect_hardware_inventory_never_crashes_with_all_tools_missing(self) -> None:
        def _raising_runner(*a, **k):
            raise FileNotFoundError("no tools available")

        inv = collect_hardware_inventory(
            runner=_raising_runner,
            sysfs_root=Path("/nonexistent-root-xyz"),
            platform=PlatformIdentity(platform_class="unknown"),
        )
        self.assertEqual(inv.devices, ())
        self.assertGreater(len(inv.capability_missing_tools), 0)

    def test_collect_hardware_inventory_combines_all_sources(self) -> None:
        inv = collect_hardware_inventory(
            pci_raw_text=LSPCI_NVIDIA_MISMATCH,
            usb_raw_text=LSUSB_SAMPLE,
            input_raw_text=INPUT_DEVICES_SAMPLE,
            sysfs_root=Path("/nonexistent-root-xyz"),
            platform=PlatformIdentity(platform_class="desktop", architecture="x86_64"),
        )
        self.assertEqual(len(inv.devices), 3 + 3 + 2)  # pci + usb + input
        summary = build_hardware_inventory_summary(inv)
        self.assertEqual(summary["device_count"], len(inv.devices))
        self.assertIn("pci", summary["device_count_by_class"])
        self.assertIn("usb", summary["device_count_by_class"])

    def test_diagnostics_is_read_only(self) -> None:
        diag = build_hardware_inventory_diagnostics()
        self.assertTrue(diag["read_only"])
        self.assertFalse(diag["writes_allowed"])
        self.assertFalse(diag["apt_install_in_scan"])


if __name__ == "__main__":
    unittest.main()
