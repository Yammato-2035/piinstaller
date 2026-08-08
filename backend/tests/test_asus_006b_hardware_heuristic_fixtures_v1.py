"""PI-RS-ASUS-ROOTCAUSE-006B — physical ASUS regression fixtures for heuristics.

Fixtures are derived from Boot1/Boot2 dmesg on ROG Strix G513QM (payload 1.10.5.0):
- MCE decoder-enabled line must not block restore
- MODE2 reset alone must not be a critical GPU defect
- NVIDIA modprobe.blacklist in ASUS-TUI-BASELINE is intentional, not driver_missing

Negative controls keep real faults red/yellow as required.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.cpu_baseline_diagnostics import build_cpu_baseline_result, scan_kernel_cpu_errors
from core.gpu_baseline_diagnostics import build_gpu_baseline_result, scan_kernel_gpu_errors
from core.hardware_baseline_contracts import BaselineSeverity, BaselineStatus
from core.hardware_contracts import HardwareDevice, HardwareDriverState
from core.kernel_event_classification import classify_gpu_reset_dmesg, classify_mce_dmesg
from core.memory_baseline_diagnostics import build_memory_baseline_result, scan_kernel_memory_errors
from rescue.hardware_baseline_gate import build_hardware_baseline_gate

# Exact physical lines observed on ASUS TUI baseline boots.
_ASUS_MCE_DECODER = "[    7.348305] MCE: In-kernel MCE decoding enabled.\n"
_ASUS_MODE2 = "[    8.376802] amdgpu 0000:06:00.0: amdgpu: MODE2 reset\n"
_ASUS_TUI_CMDLINE = (
    "BOOT_IMAGE=/live/vmlinuz boot=live components init=/lib/systemd/systemd "
    "setuphelfer_rescue=1 setuphelfer_mode=text setuphelfer_tui_baseline=1 "
    "modprobe.blacklist=nvidia,nvidia_drm,nvidia_modeset,nvidia_uvm,nouveau "
    "setuphelfer_asus_profile=ASUS-TUI-BASELINE"
)

_DMESG_REAL_MCE_UNCORRECTED = "[  100.0] mce: [Hardware Error]: Machine check events logged\n"
_DMESG_REAL_MCE_CORRECTED = "[  100.0] mce: Corrected error reported by CPU\n"
_DMESG_REAL_GPU_HANG = "[  100.0] amdgpu: [gfxhub] ring gfx timeout, signaled seq=100, emitted seq=102\n"
_DMESG_NVME_BAD_RESET = "[  200.0] nvme nvme0: controller reset with I/O error\n"

_MEMINFO = """MemTotal:       16384000 kB
MemFree:         9000000 kB
MemAvailable:    12000000 kB
SwapTotal:        2000000 kB
SwapFree:         2000000 kB
HugePages_Total:        0
HugePages_Free:         0
"""


def _gpu(vendor_id: str, name: str, driver: str | None, device_id: str) -> HardwareDevice:
    return HardwareDevice(
        device_id=device_id,
        device_class="display",
        vendor_id=vendor_id,
        product_name=f"VGA compatible controller: {name}",
        driver=HardwareDriverState(kernel_driver_in_use=driver),
    )


class TestMceClassificationFromAsusEvidence(unittest.TestCase):
    def test_decoder_enabled_is_informational_not_event(self) -> None:
        c = classify_mce_dmesg(_ASUS_MCE_DECODER)
        self.assertEqual(c["mce_event_count"], 0)
        self.assertGreaterEqual(c["informational_count"], 1)
        scan = scan_kernel_memory_errors(_ASUS_MCE_DECODER)
        self.assertEqual(scan["mce_count"], 0)
        cpu = scan_kernel_cpu_errors(_ASUS_MCE_DECODER)
        self.assertEqual(cpu["machine_check_count"], 0)

    def test_decoder_enabled_does_not_block_restore(self) -> None:
        mem = build_memory_baseline_result(
            meminfo_text=_MEMINFO, dmesg_text=_ASUS_MCE_DECODER, skip_quick_probe=True
        )
        cpu = build_cpu_baseline_result(dmesg_text=_ASUS_MCE_DECODER, skip_quick_probe=True)
        self.assertNotEqual(mem.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        self.assertNotEqual(cpu.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        self.assertIn("memory.mce_decoder_enabled", [f.code for f in mem.findings])
        self.assertIn("cpu.mce_decoder_enabled", [f.code for f in cpu.findings])
        gate = build_hardware_baseline_gate(
            memory=mem,
            cpu=cpu,
            gpu=build_gpu_baseline_result(pci_devices=[], dmesg_text="", run_optional_probes=False),
            storage=[],
        )
        # GPU not_tested makes restore false via incomplete — pass a green stub gpu via ready device.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drm = root / "sys" / "class" / "drm" / "card0-eDP-1"
            drm.mkdir(parents=True)
            (drm / "status").write_text("connected")
            pci_drm = root / "sys" / "bus" / "pci" / "devices" / "0000:06:00.0" / "drm" / "card0"
            pci_drm.mkdir(parents=True)
            dri = root / "dev" / "dri"
            dri.mkdir(parents=True)
            (dri / "renderD128").write_text("")
            gpu = build_gpu_baseline_result(
                pci_devices=[_gpu("1002", "AMD Radeon", "amdgpu", "pci:0000:06:00.0")],
                sysfs_root=root,
                dev_root=root,
                dmesg_text=_ASUS_MODE2,
                run_optional_probes=False,
            )
        gate = build_hardware_baseline_gate(memory=mem, cpu=cpu, gpu=gpu, storage=[])
        self.assertTrue(gate.restore_allowed)
        self.assertNotEqual(gate.status, "blocked")

    def test_real_uncorrected_mce_stays_red_and_blocks_restore(self) -> None:
        mem = build_memory_baseline_result(
            meminfo_text=_MEMINFO, dmesg_text=_DMESG_REAL_MCE_UNCORRECTED, skip_quick_probe=True
        )
        cpu = build_cpu_baseline_result(dmesg_text=_DMESG_REAL_MCE_UNCORRECTED, skip_quick_probe=True)
        self.assertEqual(mem.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        self.assertEqual(cpu.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drm = root / "sys" / "class" / "drm" / "card0-eDP-1"
            drm.mkdir(parents=True)
            (drm / "status").write_text("connected")
            pci_drm = root / "sys" / "bus" / "pci" / "devices" / "0000:06:00.0" / "drm" / "card0"
            pci_drm.mkdir(parents=True)
            dri = root / "dev" / "dri"
            dri.mkdir(parents=True)
            (dri / "renderD128").write_text("")
            gpu = build_gpu_baseline_result(
                pci_devices=[_gpu("1002", "AMD Radeon", "amdgpu", "pci:0000:06:00.0")],
                sysfs_root=root,
                dev_root=root,
                dmesg_text=_ASUS_MODE2,
                run_optional_probes=False,
            )
        gate = build_hardware_baseline_gate(memory=mem, cpu=cpu, gpu=gpu, storage=[])
        self.assertFalse(gate.restore_allowed)

    def test_corrected_mce_is_yellow_not_restore_block(self) -> None:
        mem = build_memory_baseline_result(
            meminfo_text=_MEMINFO, dmesg_text=_DMESG_REAL_MCE_CORRECTED, skip_quick_probe=True
        )
        self.assertIn("memory.kernel_corrected_mce", [f.code for f in mem.findings])
        self.assertEqual(
            next(f for f in mem.findings if f.code == "memory.kernel_corrected_mce").severity,
            BaselineSeverity.YELLOW.value,
        )


class TestMode2ResetClassification(unittest.TestCase):
    def test_mode2_alone_is_expected_not_critical(self) -> None:
        c = classify_gpu_reset_dmesg(_ASUS_MODE2)
        self.assertEqual(c["critical_count"], 0)
        self.assertGreaterEqual(c["expected_reset_count"], 1)
        scan = scan_kernel_gpu_errors(_ASUS_MODE2)
        self.assertEqual(scan["gpu_hang_or_reset_count"], 0)
        self.assertEqual(scan["fence_timeout_count"], 0)

    def test_mode2_does_not_emit_kernel_error_finding(self) -> None:
        device = _gpu("1002", "AMD Radeon", "amdgpu", "pci:0000:06:00.0")
        result = build_gpu_baseline_result(
            pci_devices=[device],
            sysfs_root=Path("/nonexistent-mode2"),
            dev_root=Path("/nonexistent-mode2"),
            dmesg_text=_ASUS_MODE2,
            run_optional_probes=False,
        )
        codes = [f.code for f in result.findings]
        self.assertIn("gpu.expected_reset", codes)
        self.assertNotIn("gpu.kernel_error_detected", codes)
        self.assertNotEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)

    def test_real_hang_stays_critical(self) -> None:
        scan = scan_kernel_gpu_errors(_DMESG_REAL_GPU_HANG)
        self.assertGreaterEqual(scan["gpu_hang_or_reset_count"], 1)
        result = build_gpu_baseline_result(
            pci_devices=[_gpu("1002", "AMD Radeon", "amdgpu", "pci:0000:06:00.0")],
            sysfs_root=Path("/nonexistent-hang"),
            dev_root=Path("/nonexistent-hang"),
            dmesg_text=_DMESG_REAL_GPU_HANG,
            run_optional_probes=False,
        )
        self.assertIn("gpu.kernel_error_detected", [f.code for f in result.findings])
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)

    def test_io_error_reset_still_critical_pattern(self) -> None:
        # Bad reset classifier is GPU-oriented; ensure I/O error text is not swallowed as MODE2.
        c = classify_gpu_reset_dmesg(_DMESG_NVME_BAD_RESET + _ASUS_MODE2)
        self.assertGreaterEqual(c["expected_reset_count"], 1)
        self.assertGreaterEqual(c["fence_timeout_count"] + c["gpu_hang_or_reset_count"], 0)


class TestNvidiaIntentionalBlacklist(unittest.TestCase):
    def test_asus_tui_blacklist_is_intentional_not_missing(self) -> None:
        nvidia = _gpu("10de", "NVIDIA Corporation GA104M [GeForce RTX 3060 Mobile]", None, "pci:0000:01:00.0")
        result = build_gpu_baseline_result(
            pci_devices=[nvidia],
            cmdline_raw=_ASUS_TUI_CMDLINE,
            sysfs_root=Path("/nonexistent-nvidia"),
            dev_root=Path("/nonexistent-nvidia"),
            dmesg_text=_ASUS_MCE_DECODER,
            run_optional_probes=False,
        )
        codes = [f.code for f in result.findings]
        self.assertIn("gpu.driver_intentionally_disabled", codes)
        self.assertNotIn("gpu.driver_missing", codes)
        finding = next(f for f in result.findings if f.code == "gpu.driver_intentionally_disabled")
        self.assertEqual(finding.category, "expected_by_profile")
        self.assertFalse(finding.action_blocking)
        self.assertIn("not_tested", finding.message or "")

    def test_nvidia_missing_without_blacklist_still_driver_missing(self) -> None:
        nvidia = _gpu("10de", "NVIDIA Corporation GeForce GTX 1050", None, "pci:0000:01:00.0")
        result = build_gpu_baseline_result(
            pci_devices=[nvidia],
            cmdline_raw="quiet splash",
            sysfs_root=Path("/nonexistent-nvidia2"),
            dev_root=Path("/nonexistent-nvidia2"),
            dmesg_text="",
            run_optional_probes=False,
        )
        self.assertIn("gpu.driver_missing", [f.code for f in result.findings])


if __name__ == "__main__":
    unittest.main()
