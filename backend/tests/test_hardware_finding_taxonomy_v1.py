"""PI-RS-ASUS-ROOTCAUSE-006B — telemetry finding taxonomy."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_finding_taxonomy import classify_hardware_finding_for_telemetry


class TestHardwareFindingTaxonomy(unittest.TestCase):
    def test_mce_decoder_is_informational(self) -> None:
        r = classify_hardware_finding_for_telemetry(code="memory.mce_decoder_enabled", severity="gray", category="informational")
        self.assertEqual(r["finding_type"], "hardware.informational_kernel_event")

    def test_nvidia_intentional_is_expected_profile_state(self) -> None:
        r = classify_hardware_finding_for_telemetry(
            code="gpu.driver_intentionally_disabled", severity="gray", category="expected_by_profile", action_blocking=False
        )
        self.assertEqual(r["finding_type"], "hardware.expected_profile_state")
        self.assertEqual(r["next_test"], "not_required_for_tui_baseline")

    def test_real_mce_is_actual_failure(self) -> None:
        r = classify_hardware_finding_for_telemetry(code="cpu.machine_check_detected", severity="red", category="critical")
        self.assertEqual(r["finding_type"], "hardware.actual_failure")


if __name__ == "__main__":
    unittest.main()
