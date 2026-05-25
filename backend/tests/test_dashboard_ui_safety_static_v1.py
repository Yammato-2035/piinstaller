from __future__ import annotations

import sys
import unittest
from pathlib import Path

_repo = Path(__file__).resolve().parent.parent.parent
_backend = _repo / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


class DashboardUiSafetyStaticTests(unittest.TestCase):
    def test_rescue_build_panel_shows_usb_blocked_notice(self) -> None:
        text = (_repo / "frontend/src/components/dev-dashboard/RescueBuildPanel.tsx").read_text(encoding="utf-8")
        self.assertIn("rescue-build-usb-blocked", text)

    def test_rescue_build_panel_has_no_dangerous_runtime_steps(self) -> None:
        text = (_repo / "frontend/src/components/dev-dashboard/RescueBuildPanel.tsx").read_text(encoding="utf-8")
        self.assertNotIn("runStep('dd')", text)
        self.assertNotIn('runStep("dd")', text)
        self.assertNotIn("runStep('mkfs')", text)
        self.assertNotIn("runStep('parted_write')", text)
        self.assertNotIn("runStep('usb_write')", text)

    def test_deploy_panel_contains_no_package_manager_actions(self) -> None:
        text = (_repo / "frontend/src/components/dev-dashboard/DeployStatusPanel.tsx").read_text(encoding="utf-8")
        self.assertNotIn("apt install", text)
        self.assertNotIn("apt upgrade", text)
        self.assertNotIn("package_manager_update_allowed: true", text)

    def test_operator_commands_are_displayed_not_executed(self) -> None:
        text = (_repo / "frontend/src/components/dev-dashboard/RescueBuildPanel.tsx").read_text(encoding="utf-8")
        self.assertIn("/api/dev-dashboard/rescue-iso/operator-commands/", text)
        self.assertNotIn("sudo lb build noauto", text)
        self.assertNotIn("lb build noauto", text)

    def test_update_status_card_shows_automatic_update_allowed_flag(self) -> None:
        text = (_repo / "frontend/src/components/dev-dashboard/UpdateStatusCard.tsx").read_text(encoding="utf-8")
        self.assertIn("automatic_update_allowed", text)
        self.assertIn("package_manager_update_allowed", text)


if __name__ == "__main__":
    unittest.main()
