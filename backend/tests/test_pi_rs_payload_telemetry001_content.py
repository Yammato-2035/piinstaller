"""PI-RS-PAYLOAD-TELEMETRY-001 payload content tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from core.rescue_payload_telemetry_content import (
    default_repacked_squashfs_path,
    verify_rescue_payload_telemetry_content,
)


class PayloadTelemetry001ContentTests(unittest.TestCase):
    def test_content_module_markers_defined(self) -> None:
        squashfs = default_repacked_squashfs_path()
        if not squashfs.is_file():
            self.skipTest(f"squashfs not built yet: {squashfs}")
        result = verify_rescue_payload_telemetry_content(squashfs)
        self.assertTrue(result["unsquashfs_ok"])
        self.assertTrue(result["lab_modules_present"], result["lab_modules"])
        self.assertTrue(result["lab_scripts_present"], result["lab_scripts"])
        self.assertEqual(result["version_in_payload"], "1.10.0.16")
        self.assertTrue(result["content_ok"])

    def test_version_file_path(self) -> None:
        expected = Path("build/rescue/filesystem.squashfs.repacked-1.10.0.16")
        self.assertEqual(default_repacked_squashfs_path().name, expected.name)


if __name__ == "__main__":
    unittest.main()
