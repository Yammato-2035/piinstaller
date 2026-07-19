"""PI-RS-MSI-AUTO-EVIDENCE-001 payload version tests (tracks rescue_payload_version.json)."""

from __future__ import annotations

import unittest

from core.rescue_payload_msi_fix_content import default_repacked_squashfs_path
from core.rescue_payload_version import previous_rescue_payload_version, rescue_payload_version


class MsiAutoEvidence001PayloadVersionTests(unittest.TestCase):
    def test_rescue_payload_version_current(self) -> None:
        self.assertEqual(rescue_payload_version(), "1.10.0.38")

    def test_previous_rescue_payload_version(self) -> None:
        self.assertEqual(previous_rescue_payload_version(), "1.10.0.37")

    def test_default_repacked_squashfs_path(self) -> None:
        self.assertEqual(default_repacked_squashfs_path().name, "filesystem.squashfs.repacked-1.10.0.38")


if __name__ == "__main__":
    unittest.main()
