"""RS-011K / Master Phase 2 — required rescue package policy."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
POLICY = REPO / "docs/evidence/rescue/RESCUE_REQUIRED_PACKAGE_POLICY_V2.json"
PREPARE = REPO / "scripts/rescue-live/prepare-controlled-live-build-tree.sh"


class RescueRequiredPackagePolicyV2Tests(unittest.TestCase):
    def test_policy_file_exists(self) -> None:
        self.assertTrue(POLICY.is_file())

    def test_rs011k_packages_in_policy(self) -> None:
        data = json.loads(POLICY.read_text(encoding="utf-8"))
        required = set()
        for group in data["required_packages"].values():
            required.update(group)
        for pkg in ("linux-image-amd64", "firmware-linux-nonfree", "lshw", "nvme-cli", "zstd"):
            self.assertIn(pkg, required)

    def test_no_linux_modules_extra(self) -> None:
        data = json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertIn("linux-modules-extra", data["forbidden_package_names"])
        text = PREPARE.read_text(encoding="utf-8")
        self.assertNotIn("linux-modules-extra", text)

    def test_malware_optional_review_required(self) -> None:
        data = json.loads(POLICY.read_text(encoding="utf-8"))
        optional = data["required_packages"]["security_malware_optional_review_required"]
        self.assertIn("clamav", optional)
        chroot_section = PREPARE.read_text(encoding="utf-8").split("setuphelfer.list.chroot")[1][:2000]
        self.assertNotIn("clamav", chroot_section)


if __name__ == "__main__":
    unittest.main()
