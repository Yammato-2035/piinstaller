"""Tests for developer-qemu autopilot wants enable in rescue ISO build tree."""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
PREPARE = _REPO / "scripts/rescue-live/prepare-controlled-live-build-tree.sh"
VALIDATE_TREE = _REPO / "scripts/rescue-live/validate-controlled-live-build-tree.sh"
VALIDATE_SQ = _REPO / "scripts/rescue-live/validate-rescue-iso-squashfs.sh"


class DeveloperQemuAutopilotEnableTests(unittest.TestCase):
    def test_prepare_creates_static_autopilot_wants(self) -> None:
        text = PREPARE.read_text(encoding="utf-8")
        self.assertIn("write_developer_qemu_autopilot_wants", text)
        self.assertIn(
            'ln -sf ../setuphelfer-qemu-smoke-autopilot.service',
            text,
        )
        self.assertIn("qemu_autopilot_service_wanted", text)

    def test_validate_tree_checks_autopilot_wants_for_developer_qemu(self) -> None:
        text = VALIDATE_TREE.read_text(encoding="utf-8")
        self.assertIn("setuphelfer-qemu-smoke-autopilot.service", text)
        self.assertIn("../setuphelfer-qemu-smoke-autopilot.service", text)

    def test_squashfs_validator_checks_autopilot_when_ttys0(self) -> None:
        text = VALIDATE_SQ.read_text(encoding="utf-8")
        self.assertIn("_developer_qemu_iso", text)
        self.assertIn("console=ttyS0", text)
        self.assertIn("multi-user.target.wants/setuphelfer-qemu-smoke-autopilot.service", text)
        self.assertIn("10.0.2.2:8001", text)

    def test_standard_profile_does_not_force_autopilot_in_squashfs_validator(self) -> None:
        text = VALIDATE_SQ.read_text(encoding="utf-8")
        self.assertIn('if [[ "$_developer_qemu_iso" == true ]]; then', text)


if __name__ == "__main__":
    unittest.main()
