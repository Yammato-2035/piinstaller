"""Historical PI-RS-E2E-LIVE-001D7 payload artifact checks (1.10.0.25)."""

from __future__ import annotations

import unittest
from pathlib import Path


class E2ELive001D7PayloadArtifactTests(unittest.TestCase):
    def test_legacy_squashfs_artifact_present_or_skip(self) -> None:
        artifact = (
            Path(__file__).resolve().parents[2]
            / "build"
            / "rescue"
            / "filesystem.squashfs.repacked-1.10.0.25"
        )
        if not artifact.is_file():
            self.skipTest(f"legacy squashfs not present: {artifact}")
        self.assertGreater(artifact.stat().st_size, 1_000_000)


if __name__ == "__main__":
    unittest.main()
