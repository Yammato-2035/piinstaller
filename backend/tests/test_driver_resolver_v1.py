"""PI-RS-HW-COMPAT-PROVISION-001 Phase 9: driver_resolver.py + driver_activation_plan.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.driver_activation_plan import (
    build_driver_activation_plan_diagnostics,
    build_driver_activation_preview,
    validate_activation_plan_is_safe,
)
from core.driver_resolver import (
    build_driver_resolver_diagnostics,
    classify_package_source_trust,
    resolve_driver_plan,
)
from core.hardware_contracts import Bus, HardwareDevice, HardwareDriverState


class TestPackageSourceTrust(unittest.TestCase):
    def test_trusted_sources_ranked_low(self) -> None:
        self.assertEqual(classify_package_source_trust("already_in_rescue_image"), 1)
        self.assertEqual(classify_package_source_trust("official_distribution_repository"), 2)

    def test_unknown_source_is_blocked_level(self) -> None:
        self.assertEqual(classify_package_source_trust("totally_made_up"), 6)
        self.assertEqual(classify_package_source_trust("unknown_source"), 6)


class TestResolveDriverPlan(unittest.TestCase):
    def test_device_with_bound_driver_recommends_it(self) -> None:
        dev = HardwareDevice(
            device_id="pci:00:1f.6",
            device_class="network",
            bus=Bus.PCI,
            driver=HardwareDriverState(kernel_driver_in_use="e1000e", kernel_driver_candidates=("e1000e",)),
        )
        plan = resolve_driver_plan(dev, package_source="official_distribution_repository")
        self.assertEqual(plan["recommended_driver"], "e1000e")
        self.assertFalse(plan["reboot_required"])
        self.assertFalse(plan["live_activation_possible"])

    def test_device_without_any_candidate_warns_no_guessing(self) -> None:
        dev = HardwareDevice(device_id="usb:9-9", device_class="usb", bus=Bus.USB)
        plan = resolve_driver_plan(dev)
        self.assertIsNone(plan["recommended_driver"])
        self.assertIn("no_driver_candidate_known", plan["warnings"])

    def test_unknown_package_source_blocks_package_candidates(self) -> None:
        dev = HardwareDevice(
            device_id="pci:01:00.0",
            device_class="pci",
            bus=Bus.PCI,
            driver=HardwareDriverState(kernel_driver_candidates=("some_driver",)),
        )
        plan = resolve_driver_plan(dev, package_source="shady_website")
        self.assertEqual(plan["package_candidates"], [])
        self.assertIn("package_source_blocked", plan["errors"])
        self.assertIn("package_source_untrusted_blocked", plan["warnings"])

    def test_firmware_missing_flagged_as_warning(self) -> None:
        dev = HardwareDevice(
            device_id="pci:02:00.0",
            device_class="network",
            bus=Bus.PCI,
            driver=HardwareDriverState(kernel_driver_in_use="iwlwifi"),
        )
        plan = resolve_driver_plan(dev, firmware_missing=True)
        self.assertIn("firmware_missing_driver_may_be_limited", plan["warnings"])
        self.assertFalse(plan["kernel_compatible"])

    def test_diagnostics_never_auto_installs(self) -> None:
        diag = build_driver_resolver_diagnostics()
        self.assertFalse(diag["auto_install"])
        self.assertFalse(diag["auto_add_package_source"])
        self.assertFalse(diag["auto_accept_license"])
        self.assertFalse(diag["curl_pipe_bash_used"])


class TestActivationPlanSafety(unittest.TestCase):
    def test_preview_always_forces_write_allowed_false(self) -> None:
        dev = HardwareDevice(device_id="pci:03:00.0", device_class="gpu", bus=Bus.PCI)
        plan = resolve_driver_plan(dev)
        plan["live_activation_possible"] = True  # simulate a misbehaving upstream resolver
        preview = build_driver_activation_preview(plan)
        self.assertFalse(preview["live_activation_possible"])
        self.assertFalse(preview["write_allowed"])
        self.assertTrue(preview["requires_operator_confirmation"])

    def test_validate_flags_unsafe_plan(self) -> None:
        unsafe_plan = {"live_activation_possible": True, "write_allowed": True, "warnings": []}
        violations = validate_activation_plan_is_safe(unsafe_plan)
        self.assertIn("live_activation_possible_must_be_false_in_this_phase", violations)
        self.assertIn("write_allowed_must_be_false_in_this_phase", violations)

    def test_validate_passes_clean_preview(self) -> None:
        dev = HardwareDevice(device_id="pci:04:00.0", device_class="gpu", bus=Bus.PCI)
        plan = resolve_driver_plan(dev)
        preview = build_driver_activation_preview(plan)
        self.assertEqual(validate_activation_plan_is_safe(preview), [])

    def test_diagnostics_shape(self) -> None:
        diag = build_driver_activation_plan_diagnostics()
        self.assertFalse(diag["write_allowed"])
        self.assertFalse(diag["live_activation_possible"])
        self.assertFalse(diag["persistent_install_possible"])


if __name__ == "__main__":
    unittest.main()
