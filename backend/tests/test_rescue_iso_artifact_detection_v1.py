from __future__ import annotations

import unittest
from pathlib import Path

_repo = Path(__file__).resolve().parent.parent.parent
_wrapper = _repo / "scripts/rescue-live/run-controlled-iso-build-with-logging.sh"
_prepare = _repo / "scripts/rescue-live/prepare-controlled-live-build-tree.sh"
_iso = _repo / "build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"


class RescueIsoArtifactDetectionTests(unittest.TestCase):
    def test_wrapper_lists_binary_hybrid_iso_basename(self) -> None:
        text = _wrapper.read_text(encoding="utf-8")
        self.assertIn("binary.hybrid.iso", text)
        self.assertIn("RESCUE-BUILD-ZSYNC-STALE-001", text)

    def test_prepare_disables_zsync(self) -> None:
        text = _prepare.read_text(encoding="utf-8")
        self.assertIn("--zsync false", text)
        self.assertIn("binary*.zsync*", text)

    def test_hybrid_iso_present_on_disk_when_built(self) -> None:
        if not _iso.is_file():
            self.skipTest("binary.hybrid.iso not present — operator build required")
        self.assertGreater(_iso.stat().st_size, 400_000_000)


if __name__ == "__main__":
    unittest.main()
