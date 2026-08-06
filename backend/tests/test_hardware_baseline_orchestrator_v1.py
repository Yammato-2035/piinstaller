"""PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 10: hardware_baseline_orchestrator.py tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_baseline_contracts import BaselineStatus, BaselineSubsystem
from rescue.hardware_baseline_orchestrator import (
    build_hardware_baseline_orchestrator_diagnostics,
    run_hardware_baseline,
)

_NONEXISTENT = Path("/nonexistent-orchestrator-baseline-fs")

_MEMINFO_NORMAL = "MemTotal:       16384000 kB\nMemAvailable:    12000000 kB\n"
_HEALTH_PASSED = "SMART overall-health self-assessment test result: PASSED\n"


def _attr_table_clean() -> str:
    lines = [
        "ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE",
        "  5 Reallocated_Sector_Ct   0x0033   100   100   010    Pre-fail  Always       -       0",
        "194 Temperature_Celsius     0x0022   100   100   000    Old_age   Always       -       30",
        "197 Current_Pending_Sector  0x0012   100   100   000    Old_age   Always       -       0",
        "198 Offline_Uncorrectable   0x0010   100   100   000    Old_age   Offline      -       0",
        "199 UDMA_CRC_Error_Count    0x003e   200   200   000    Old_age   Always       -       0",
    ]
    return "\n".join(lines) + "\n"


class TestRunHardwareBaseline(unittest.TestCase):
    def test_quick_mode_runs_all_four_subsystem_groups(self) -> None:
        result = run_hardware_baseline(
            mode="quick",
            pci_devices=[],
            meminfo_text=_MEMINFO_NORMAL,
            dmidecode_text="",
            dmesg_text="",
            sysfs_root=_NONEXISTENT,
            dev_root=_NONEXISTENT,
            storage_devices=[
                {
                    "device_id": "sda",
                    "device_class": "rotational",
                    "smart_health_raw": _HEALTH_PASSED,
                    "smart_attributes_raw": _attr_table_clean(),
                }
            ],
        )
        subsystems = {s.subsystem for s in result.subsystems}
        self.assertIn(BaselineSubsystem.MEMORY.value, subsystems)
        self.assertIn(BaselineSubsystem.CPU.value, subsystems)
        self.assertIn(BaselineSubsystem.GPU.value, subsystems)
        self.assertIn(BaselineSubsystem.HDD.value, subsystems)
        self.assertEqual(result.mode, "quick")
        self.assertIsNotNone(result.run_id)

    def test_extended_preview_mode_accepted(self) -> None:
        result = run_hardware_baseline(mode="extended_preview", pci_devices=[], meminfo_text=_MEMINFO_NORMAL, dmesg_text="", sysfs_root=_NONEXISTENT, dev_root=_NONEXISTENT)
        self.assertEqual(result.mode, "extended_preview")

    def test_invalid_mode_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_hardware_baseline(mode="full_stress_test")

    def test_virtual_storage_device_excluded(self) -> None:
        result = run_hardware_baseline(
            mode="quick",
            pci_devices=[],
            meminfo_text=_MEMINFO_NORMAL,
            dmesg_text="",
            sysfs_root=_NONEXISTENT,
            dev_root=_NONEXISTENT,
            storage_devices=[{"device_id": "loop0", "device_class": "virtual"}],
        )
        device_ids = [s.device_id for s in result.subsystems if s.device_id]
        self.assertNotIn("loop0", device_ids)

    def test_dispatches_nvme_device_to_nvme_builder(self) -> None:
        result = run_hardware_baseline(
            mode="quick",
            pci_devices=[],
            meminfo_text=_MEMINFO_NORMAL,
            dmesg_text="",
            sysfs_root=_NONEXISTENT,
            dev_root=_NONEXISTENT,
            storage_devices=[{"device_id": "nvme0n1", "device_class": "nvme", "smart_log_raw": "Critical Warning: 0x00\nTemperature: 30 C\n", "id_ctrl_raw": ""}],
        )
        nvme_results = [s for s in result.subsystems if s.subsystem == BaselineSubsystem.NVME.value]
        self.assertEqual(len(nvme_results), 1)

    def test_dispatches_non_rotational_to_sata_ssd_builder(self) -> None:
        result = run_hardware_baseline(
            mode="quick",
            pci_devices=[],
            meminfo_text=_MEMINFO_NORMAL,
            dmesg_text="",
            sysfs_root=_NONEXISTENT,
            dev_root=_NONEXISTENT,
            storage_devices=[{"device_id": "sdb", "device_class": "non_rotational", "smart_health_raw": _HEALTH_PASSED, "smart_attributes_raw": ""}],
        )
        ssd_results = [s for s in result.subsystems if s.subsystem == BaselineSubsystem.SATA_SSD.value]
        self.assertEqual(len(ssd_results), 1)

    def test_gate_is_populated_on_result(self) -> None:
        result = run_hardware_baseline(mode="quick", pci_devices=[], meminfo_text=_MEMINFO_NORMAL, dmesg_text="", sysfs_root=_NONEXISTENT, dev_root=_NONEXISTENT)
        self.assertIn(result.gate.status, ("passed", "review_required", "blocked", "incomplete"))

    def test_never_starts_extended_test_automatically(self) -> None:
        diag = build_hardware_baseline_orchestrator_diagnostics()
        self.assertFalse(diag["starts_extended_test_automatically"])

    def test_run_id_is_stable_when_provided(self) -> None:
        result = run_hardware_baseline(mode="quick", run_id="fixed-run-id", pci_devices=[], meminfo_text=_MEMINFO_NORMAL, dmesg_text="", sysfs_root=_NONEXISTENT, dev_root=_NONEXISTENT)
        self.assertEqual(result.run_id, "fixed-run-id")

    def test_skip_quick_probes_propagates(self) -> None:
        result = run_hardware_baseline(
            mode="quick", pci_devices=[], meminfo_text=_MEMINFO_NORMAL, dmesg_text="", sysfs_root=_NONEXISTENT, dev_root=_NONEXISTENT, skip_quick_probes=True
        )
        memory_result = next(s for s in result.subsystems if s.subsystem == BaselineSubsystem.MEMORY.value)
        self.assertIn("quick_memory_probe", memory_result.checks_skipped)


if __name__ == "__main__":
    unittest.main()
