"""PI-RS-HW-COMPAT-PROVISION-001 Phase 4: cpu_platform_detection.py tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.cpu_platform_detection import (
    build_cpu_platform_details,
    build_cpu_platform_detection_diagnostics,
    detect_cpu_platform,
    detect_microcode_status,
    detect_virtualization_available,
    is_raspberry_pi_soc,
    normalize_architecture,
    parse_cpuinfo_first_block,
    parse_lscpu,
)

LSCPU_INTEL = """Architecture:                       x86_64
Vendor ID:                           GenuineIntel
Model name:                          Intel(R) Core(TM) i7-13700H
CPU family:                          6
Model:                               186
Stepping:                            2
Core(s) per socket:                  14
Socket(s):                           1
Thread(s) per core:                  2
Flags:                               fpu vme de pse tsc msr vmx aes avx2
"""

LSCPU_AMD_NO_VMX = """Architecture:                       x86_64
Vendor ID:                           AuthenticAMD
Model name:                          AMD Ryzen 9 7945HX
Flags:                               fpu vme de pse tsc msr svm aes
"""

CPUINFO_PI5 = """processor\t: 0
model name\t: ARMv8 Processor rev 1 (v8l)
Features\t: fp asimd evtstrm aes pmull sha1 sha2 crc32
"""


class TestArchitectureNormalization(unittest.TestCase):
    def test_known_architectures_normalized(self) -> None:
        self.assertEqual(normalize_architecture("x86_64"), "x86_64")
        self.assertEqual(normalize_architecture("aarch64"), "aarch64")
        self.assertEqual(normalize_architecture("armv7l"), "armv7")
        self.assertEqual(normalize_architecture("i686"), "i686")

    def test_unknown_architecture_stays_unknown_not_guessed(self) -> None:
        self.assertEqual(normalize_architecture("riscv64"), "unknown")
        self.assertEqual(normalize_architecture(None), "unknown")


class TestVirtualizationAndMicrocode(unittest.TestCase):
    def test_intel_vmx_detected(self) -> None:
        fields = parse_lscpu(LSCPU_INTEL)
        self.assertTrue(detect_virtualization_available(fields["Flags"], "x86_64"))

    def test_amd_svm_detected(self) -> None:
        fields = parse_lscpu(LSCPU_AMD_NO_VMX)
        self.assertTrue(detect_virtualization_available(fields["Flags"], "x86_64"))

    def test_no_virt_flags_is_false_not_guessed(self) -> None:
        self.assertFalse(detect_virtualization_available("fpu vme de pse", "x86_64"))

    def test_arm_virt_stays_conservative_false(self) -> None:
        self.assertFalse(detect_virtualization_available("aes pmull", "aarch64"))

    def test_microcode_unknown_without_field(self) -> None:
        self.assertEqual(detect_microcode_status({}), "unknown")

    def test_microcode_present_with_field(self) -> None:
        self.assertEqual(detect_microcode_status({"microcode": "0x1234"}), "present")


class TestRaspberryPiSoc(unittest.TestCase):
    def test_pi_compatible_string_detected(self) -> None:
        self.assertTrue(is_raspberry_pi_soc("raspberrypi,5-model-b\x00brcm,bcm2712"))

    def test_non_pi_compatible_string_not_flagged(self) -> None:
        self.assertFalse(is_raspberry_pi_soc("intel,coffeelake"))
        self.assertFalse(is_raspberry_pi_soc(None))


class TestDetectCpuPlatform(unittest.TestCase):
    def test_intel_desktop_cpu_ready(self) -> None:
        device, missing = detect_cpu_platform(lscpu_raw=LSCPU_INTEL, cpuinfo_raw="", uname_machine_raw="x86_64")
        self.assertEqual(missing, [])
        self.assertEqual(device.device_class, "cpu")
        self.assertEqual(device.operational_status, "ready")
        self.assertIn("i7-13700H", device.model_name)

    def test_pi5_soc_detected_as_soc_subclass(self) -> None:
        device, _ = detect_cpu_platform(
            lscpu_raw="",
            cpuinfo_raw=CPUINFO_PI5,
            uname_machine_raw="aarch64",
            device_tree_compatible="raspberrypi,5-model-b\x00brcm,bcm2712",
        )
        self.assertEqual(device.subclass, "soc")

    def test_missing_lscpu_tool_recorded_not_crashed(self) -> None:
        def _raising_runner(*a, **k):
            raise FileNotFoundError("lscpu missing")

        device, missing = detect_cpu_platform(cpuinfo_raw="", uname_machine_raw="x86_64", runner=_raising_runner)
        self.assertIn("lscpu", missing)
        self.assertIsNotNone(device)  # never crashes


class TestFullDetailsReport(unittest.TestCase):
    def test_details_report_shape(self) -> None:
        report = build_cpu_platform_details(
            lscpu_raw=LSCPU_INTEL, cpuinfo_raw="", uname_machine_raw="x86_64", sysfs_root=Path("/nonexistent-xyz")
        )
        self.assertEqual(report["architecture"], "x86_64")
        self.assertTrue(report["virtualization_available"])
        self.assertEqual(report["thermal_sources"], [])
        self.assertIn("device", report)

    def test_diagnostics_read_only(self) -> None:
        diag = build_cpu_platform_detection_diagnostics()
        self.assertTrue(diag["read_only"])
        self.assertFalse(diag["writes_allowed"])


if __name__ == "__main__":
    unittest.main()
