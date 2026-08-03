"""PI-RS-HW-COMPAT-PROVISION-001 Phase 11: raspberry_pi_detection.py + boot_plan.py.

Fixture groups per spec PHASE 17: Pi 3, Pi 3B+, Pi 4, Pi 400, Pi 5, Pi with microSD,
Pi with USB boot, Pi 5 with NVMe.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from platforms.raspberry_pi_boot_plan import build_boot_plan, get_boot_medium_support
from platforms.raspberry_pi_detection import detect_raspberry_pi_model, parse_device_tree_compatible

COMPAT_PI3 = "raspberrypi,3-model-b\x00brcm,bcm2837\x00"
COMPAT_PI3B_PLUS = "raspberrypi,3-model-b-plus\x00brcm,bcm2837\x00"
COMPAT_PI4 = "raspberrypi,4-model-b\x00brcm,bcm2711\x00"
COMPAT_PI400 = "raspberrypi,400\x00brcm,bcm2711\x00"
COMPAT_PI5 = "raspberrypi,5-model-b\x00brcm,bcm2712\x00"
COMPAT_NON_PI = "generic,some-arm-board\x00"


class TestCompatibleStringParsing(unittest.TestCase):
    def test_parses_nul_separated_string(self) -> None:
        parts = parse_device_tree_compatible(COMPAT_PI5)
        self.assertIn("raspberrypi,5-model-b", parts)
        self.assertIn("brcm,bcm2712", parts)

    def test_bytes_input_supported(self) -> None:
        parts = parse_device_tree_compatible(COMPAT_PI3.encode("utf-8"))
        self.assertIn("raspberrypi,3-model-b", parts)

    def test_none_input_returns_empty(self) -> None:
        self.assertEqual(parse_device_tree_compatible(None), [])


class TestModelDetection(unittest.TestCase):
    def test_pi3_distinguished_from_pi3b_plus(self) -> None:
        pi3 = detect_raspberry_pi_model(compatible_raw=COMPAT_PI3)
        pi3plus = detect_raspberry_pi_model(compatible_raw=COMPAT_PI3B_PLUS)
        self.assertEqual(pi3["model_id"], "pi3")
        self.assertEqual(pi3plus["model_id"], "pi3b_plus")
        self.assertNotEqual(pi3["model_id"], pi3plus["model_id"])

    def test_pi4_distinguished_from_pi400(self) -> None:
        pi4 = detect_raspberry_pi_model(compatible_raw=COMPAT_PI4)
        pi400 = detect_raspberry_pi_model(compatible_raw=COMPAT_PI400)
        self.assertEqual(pi4["model_id"], "pi4")
        self.assertEqual(pi400["model_id"], "pi400")

    def test_pi5_detected_with_high_confidence(self) -> None:
        pi5 = detect_raspberry_pi_model(compatible_raw=COMPAT_PI5)
        self.assertTrue(pi5["is_raspberry_pi"])
        self.assertEqual(pi5["model_id"], "pi5")
        self.assertEqual(pi5["soc"], "bcm2712")
        self.assertGreater(pi5["detection_confidence"], 0.9)

    def test_non_pi_board_not_flagged(self) -> None:
        result = detect_raspberry_pi_model(compatible_raw=COMPAT_NON_PI)
        self.assertFalse(result["is_raspberry_pi"])
        self.assertIsNone(result["model_id"])

    def test_fallback_model_string_low_confidence(self) -> None:
        result = detect_raspberry_pi_model(compatible_raw="", model_string="Raspberry Pi 5 Model B Rev 1.0")
        self.assertTrue(result["is_raspberry_pi"])
        self.assertIsNone(result["model_id"])  # cannot distinguish exact variant from string alone
        self.assertLess(result["detection_confidence"], 0.5)


class TestBootPlanDiffersByGeneration(unittest.TestCase):
    def test_pi3_and_pi5_get_different_boot_plans(self) -> None:
        """Spec: no blanket 'Pi 3-5 supported' — plans must differ."""
        pi3_support = get_boot_medium_support("pi3")
        pi5_support = get_boot_medium_support("pi5")
        self.assertNotEqual(pi3_support, pi5_support)
        self.assertEqual(pi3_support["usb_mass_storage"], "bootloader_update_required")
        self.assertEqual(pi5_support["usb_mass_storage"], "boot_supported")

    def test_only_pi5_and_cm5_get_nvme_candidate(self) -> None:
        self.assertEqual(get_boot_medium_support("pi3")["nvme"], "unsupported")
        self.assertEqual(get_boot_medium_support("pi4")["nvme"], "unsupported")
        self.assertNotEqual(get_boot_medium_support("pi5")["nvme"], "unsupported")

    def test_boot_plan_never_writes_eeprom(self) -> None:
        plan = build_boot_plan(model_id="pi5")
        self.assertFalse(plan["eeprom_write_performed"])
        for medium in plan["boot_media"]:
            self.assertTrue(medium["physical_validation_required"])

    def test_unknown_model_returns_empty_media(self) -> None:
        plan = build_boot_plan(model_id=None)
        self.assertEqual(plan["boot_media"], [])


if __name__ == "__main__":
    unittest.main()
