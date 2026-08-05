"""PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 5: gpu_baseline_diagnostics.py tests.

Fixture groups per spec PHASE 18: headless, Intel/AMD ready, NVIDIA driver
missing, kernel errors, firmware missing, nomodeset, DRM/render node
missing, hybrid graphics, optional probe missing tools.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_baseline_contracts import BaselineSeverity, BaselineStatus
from core.hardware_contracts import HardwareDevice, HardwareDriverState
from core.gpu_baseline_diagnostics import (
    build_gpu_baseline_diagnostics,
    build_gpu_baseline_result,
    check_render_node_presence,
    run_optional_display_probe,
    scan_kernel_gpu_errors,
)

_NONEXISTENT = Path("/nonexistent-gpu-baseline-fs")
_DMESG_CLEAN = "[    0.0] Linux version 6.1\n"
_DMESG_HANG = "[  100.0] amdgpu: [gfxhub] ring gfx timeout, signaled seq=100, emitted seq=102\n"
_DMESG_FIRMWARE_MISSING = "[  50.0] amdgpu: failed to load firmware \"amdgpu/navi10_smc.bin\"\n"


def _gpu_device(vendor_id: str, product_name: str, driver: str | None) -> HardwareDevice:
    return HardwareDevice(
        device_id=f"pci:0000:00:02.0",
        device_class="display",
        vendor_id=vendor_id,
        product_name=f"VGA compatible controller: {product_name}",
        driver=HardwareDriverState(kernel_driver_in_use=driver),
    )


class TestCheckRenderNodePresence(unittest.TestCase):
    def test_nonexistent_dev_yields_empty(self) -> None:
        self.assertEqual(check_render_node_presence(dev_root=_NONEXISTENT), [])


class TestScanKernelGpuErrors(unittest.TestCase):
    def test_clean_log(self) -> None:
        scan = scan_kernel_gpu_errors(_DMESG_CLEAN)
        self.assertEqual(scan["gpu_hang_or_reset_count"], 0)

    def test_hang_detected(self) -> None:
        scan = scan_kernel_gpu_errors(_DMESG_HANG)
        self.assertGreaterEqual(scan["gpu_hang_or_reset_count"], 1)

    def test_firmware_missing_detected(self) -> None:
        scan = scan_kernel_gpu_errors(_DMESG_FIRMWARE_MISSING)
        self.assertGreaterEqual(scan["firmware_load_failed_count"], 1)

    def test_missing_dmesg_tool_reported(self) -> None:
        scan = scan_kernel_gpu_errors(None, runner=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
        self.assertIn("dmesg", scan["missing_tools"])


class TestRunOptionalDisplayProbe(unittest.TestCase):
    def test_missing_tool_not_an_error(self) -> None:
        probe = run_optional_display_probe("glxinfo", runner=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
        self.assertFalse(probe["available"])
        self.assertEqual(probe["tool"], "glxinfo")


class TestBuildGpuBaselineResult(unittest.TestCase):
    def test_headless_system_not_tested(self) -> None:
        result = build_gpu_baseline_result(pci_devices=[], sysfs_root=_NONEXISTENT, dev_root=_NONEXISTENT, dmesg_text=_DMESG_CLEAN, run_optional_probes=False)
        self.assertEqual(result.status, BaselineStatus.NOT_TESTED.value)
        self.assertEqual(result.severity, BaselineSeverity.GRAY.value)

    def test_intel_ready_gpu_yields_no_immediate_issue(self) -> None:
        # gpu_status "ready" requires: driver_in_use + drm card present + active connector.
        device = _gpu_device("8086", "Intel Corporation UHD Graphics 630", "i915")

        def fake_runner(argv, **kwargs):
            class R:
                stdout = ""

            return R()

        # Build a fake sysfs with a connected DRM connector for card0.
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drm = root / "sys" / "class" / "drm" / "card0-HDMI-A-1"
            drm.mkdir(parents=True)
            (drm / "status").write_text("connected")
            dri = root / "dev" / "dri"
            dri.mkdir(parents=True)
            (dri / "renderD128").write_text("")
            result = build_gpu_baseline_result(
                pci_devices=[device], sysfs_root=root, dev_root=root, dmesg_text=_DMESG_CLEAN, run_optional_probes=False
            )
        self.assertEqual(result.status, BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)

    def test_nvidia_driver_missing_yields_yellow(self) -> None:
        device = _gpu_device("10de", "NVIDIA Corporation GeForce GTX 1050", None)
        result = build_gpu_baseline_result(pci_devices=[device], sysfs_root=_NONEXISTENT, dev_root=_NONEXISTENT, dmesg_text=_DMESG_CLEAN, run_optional_probes=False)
        self.assertEqual(result.status, BaselineStatus.REVIEW_REQUIRED.value)
        codes = [f.code for f in result.findings]
        self.assertIn("gpu.driver_missing", codes)

    def test_kernel_error_detected_is_red_and_recommends_extended_render_test(self) -> None:
        device = _gpu_device("1002", "Advanced Micro Devices, Inc. [AMD/ATI] Radeon RX 580", "amdgpu")
        result = build_gpu_baseline_result(pci_devices=[device], sysfs_root=_NONEXISTENT, dev_root=_NONEXISTENT, dmesg_text=_DMESG_HANG, run_optional_probes=False)
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        codes = [f.code for f in result.findings]
        self.assertIn("gpu.kernel_error_detected", codes)
        self.assertTrue(result.extended_test.recommended)

    def test_firmware_missing_detected_as_yellow(self) -> None:
        device = _gpu_device("1002", "Advanced Micro Devices, Inc. [AMD/ATI] Radeon RX 580", "amdgpu")
        result = build_gpu_baseline_result(pci_devices=[device], sysfs_root=_NONEXISTENT, dev_root=_NONEXISTENT, dmesg_text=_DMESG_FIRMWARE_MISSING, run_optional_probes=False)
        codes = [f.code for f in result.findings]
        self.assertIn("gpu.firmware_missing", codes)
        self.assertNotEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)

    def test_nomodeset_disabled_by_cmdline(self) -> None:
        device = _gpu_device("8086", "Intel Corporation UHD Graphics 630", "i915")
        result = build_gpu_baseline_result(
            pci_devices=[device], cmdline_raw="quiet nomodeset", sysfs_root=_NONEXISTENT, dev_root=_NONEXISTENT, dmesg_text=_DMESG_CLEAN, run_optional_probes=False
        )
        codes = [f.code for f in result.findings]
        self.assertIn("gpu.disabled_by_cmdline", codes)

    def test_drm_device_missing_detected(self) -> None:
        device = _gpu_device("8086", "Intel Corporation UHD Graphics 630", "i915")
        result = build_gpu_baseline_result(pci_devices=[device], sysfs_root=_NONEXISTENT, dev_root=_NONEXISTENT, dmesg_text=_DMESG_CLEAN, run_optional_probes=False)
        codes = [f.code for f in result.findings]
        self.assertIn("gpu.drm_device_missing", codes)

    def test_render_node_missing_detected(self) -> None:
        device = _gpu_device("8086", "Intel Corporation UHD Graphics 630", "i915")
        result = build_gpu_baseline_result(pci_devices=[device], sysfs_root=_NONEXISTENT, dev_root=_NONEXISTENT, dmesg_text=_DMESG_CLEAN, run_optional_probes=False)
        codes = [f.code for f in result.findings]
        self.assertIn("gpu.render_node_missing", codes)

    def test_hybrid_graphics_two_devices(self) -> None:
        intel = _gpu_device("8086", "Intel Corporation UHD Graphics 630", "i915")
        nvidia = HardwareDevice(
            device_id="pci:0000:01:00.0",
            device_class="display",
            vendor_id="10de",
            product_name="3D controller: NVIDIA Corporation GeForce MX150",
            driver=HardwareDriverState(kernel_driver_in_use=None),
        )
        result = build_gpu_baseline_result(pci_devices=[intel, nvidia], sysfs_root=_NONEXISTENT, dev_root=_NONEXISTENT, dmesg_text=_DMESG_CLEAN, run_optional_probes=False)
        names = {m.name: m.value for m in result.metrics}
        self.assertEqual(names["gpu_device_count"], 2)
        self.assertTrue(names.get("hybrid_graphics"))

    def test_optional_probe_missing_tool_not_an_error(self) -> None:
        device = _gpu_device("8086", "Intel Corporation UHD Graphics 630", "i915")
        result = build_gpu_baseline_result(
            pci_devices=[device],
            sysfs_root=_NONEXISTENT,
            dev_root=_NONEXISTENT,
            dmesg_text=_DMESG_CLEAN,
            run_optional_probes=True,
            runner=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()),
        )
        self.assertTrue(any(c.startswith("optional_probe:") for c in result.checks_skipped))
        # A missing optional tool alone must not push status to red.
        self.assertNotEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)

    def test_never_claims_gpu_fully_stable(self) -> None:
        device = _gpu_device("8086", "Intel Corporation UHD Graphics 630", "i915")
        result = build_gpu_baseline_result(pci_devices=[device], sysfs_root=_NONEXISTENT, dev_root=_NONEXISTENT, dmesg_text=_DMESG_CLEAN, run_optional_probes=False)
        blob = str(result.to_dict()).lower()
        self.assertNotIn("gpu_fully_stable", blob)
        self.assertNotIn("gpu_fully_verified", blob)


class TestDiagnostics(unittest.TestCase):
    def test_diagnostics_never_installs_driver(self) -> None:
        diag = build_gpu_baseline_diagnostics()
        self.assertFalse(diag["installs_driver_or_firmware"])
        self.assertFalse(diag["modifies_kernel_cmdline"])


if __name__ == "__main__":
    unittest.main()
