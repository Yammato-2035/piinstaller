from __future__ import annotations

import unittest
from pathlib import Path

_repo = Path(__file__).resolve().parent.parent.parent
_prepare = _repo / "scripts/rescue-live/prepare-controlled-live-build-tree.sh"
_build_root = _repo / "build/rescue/live-build/setuphelfer-rescue-live"
_blist = _build_root / "config/package-lists/setuphelfer.list.binary"


class RescueIsoIsohybridPreflightTests(unittest.TestCase):
    def test_prepare_script_declares_binary_syslinux_utils(self) -> None:
        text = _prepare.read_text(encoding="utf-8")
        self.assertIn("setuphelfer.list.binary", text)
        self.assertIn("syslinux-utils", text)

    def test_prepared_tree_has_binary_package_list_when_present(self) -> None:
        if not _build_root.is_dir():
            self.skipTest("controlled build tree not present")
        if not _blist.is_file():
            self.skipTest("run prepare-controlled-live-build-tree.sh first")
        self.assertIn("syslinux-utils", _blist.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
