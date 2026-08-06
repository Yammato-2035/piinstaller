"""PI-RS-MSI-GUI-003 payload version 1.10.0.16 tests."""

from __future__ import annotations

import unittest

from core.rescue_payload_msi_fix_content import default_repacked_squashfs_path
from core.rescue_payload_msi_gui003_content import verify_rescue_payload_msi_gui003_content
from core.rescue_payload_version import previous_rescue_payload_version, rescue_payload_version


class MsiGui003PayloadVersionTests(unittest.TestCase):
    def test_version_bumped(self) -> None:
        self.assertEqual(rescue_payload_version(), "1.10.0.17")
        self.assertEqual(previous_rescue_payload_version(), "1.10.0.16")

    def test_repacked_path_name(self) -> None:
        self.assertEqual(default_repacked_squashfs_path().name, "filesystem.squashfs.repacked-1.10.0.17")

    def test_payload_content_when_built(self) -> None:
        squashfs = default_repacked_squashfs_path()
        if not squashfs.is_file():
            self.skipTest(f"squashfs not built yet: {squashfs}")
        result = verify_rescue_payload_msi_gui003_content(squashfs)
        self.assertTrue(result["all_version_carriers_match"], result)
        self.assertTrue(result["content_ok"], result)


if __name__ == "__main__":
    unittest.main()
