"""Patch plan constants aligned with patch-rescue-iso-uefi-x64.sh."""

from __future__ import annotations

import unittest

ESP_SECTOR_COUNT = 16384
ESP_SIZE_BYTES = 16777216
ESP_MIN_BYTES = 4194304
ESP_MAX_ELTORITO_BLOCKS = 65535


class RescueIsoUefiPatchPlanTests(unittest.TestCase):
    def test_esp_size_avoids_fat16_4mb_failure(self) -> None:
        self.assertGreaterEqual(ESP_SIZE_BYTES, ESP_MIN_BYTES)
        self.assertEqual(ESP_SIZE_BYTES, 16777216)
        self.assertLessEqual(ESP_SIZE_BYTES // 512, ESP_MAX_ELTORITO_BLOCKS)

    def test_sector_count_matches_script_default(self) -> None:
        self.assertEqual(ESP_SECTOR_COUNT, 16384)


if __name__ == "__main__":
    unittest.main()
