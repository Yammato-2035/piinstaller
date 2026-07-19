"""PI-RS-MSI-GUI-003 payload version tests (historical release 1.10.0.16; current payload see 1.10.0.17)."""

from __future__ import annotations

import unittest

from core.rescue_payload_msi_fix_content import default_repacked_squashfs_path
from core.rescue_payload_msi_gui003_content import verify_rescue_payload_msi_gui003_content


class MsiGui003PayloadVersionTests(unittest.TestCase):
    def test_gui003_artifact_path_when_present(self) -> None:
        artifact = default_repacked_squashfs_path().parents[0] / "filesystem.squashfs.repacked-1.10.0.16"
        if not artifact.is_file():
            self.skipTest(f"historical squashfs not present: {artifact}")
        result = verify_rescue_payload_msi_gui003_content(artifact)
        self.assertTrue(result["all_version_carriers_match"], result)
        self.assertTrue(result["content_ok"], result)


if __name__ == "__main__":
    unittest.main()
