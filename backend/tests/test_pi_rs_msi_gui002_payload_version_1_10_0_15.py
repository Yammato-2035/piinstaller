"""PI-RS-MSI-GUI-002 payload version 1.10.0.15 tests."""

from __future__ import annotations

import unittest

from core.rescue_payload_msi_fix_content import default_repacked_squashfs_path
from core.rescue_payload_msi_gui002_content import verify_rescue_payload_msi_gui002_content
from core.rescue_payload_version import previous_rescue_payload_version, rescue_payload_version


class MsiGui002PayloadVersionTests(unittest.TestCase):
    def test_version_bumped(self) -> None:
        self.assertEqual(rescue_payload_version(), "1.10.0.38")
        self.assertEqual(previous_rescue_payload_version(), "1.10.0.37")

    def test_repacked_path_name(self) -> None:
        self.assertEqual(default_repacked_squashfs_path().name, "filesystem.squashfs.repacked-1.10.0.38")

    def test_payload_content_when_built(self) -> None:
        squashfs = default_repacked_squashfs_path()
        if not squashfs.is_file():
            self.skipTest(f"squashfs not built yet: {squashfs}")
        result = verify_rescue_payload_msi_gui002_content(squashfs)
        self.assertTrue(result["version_match"], result)
        self.assertTrue(result["content_ok"], result)


if __name__ == "__main__":
    unittest.main()
