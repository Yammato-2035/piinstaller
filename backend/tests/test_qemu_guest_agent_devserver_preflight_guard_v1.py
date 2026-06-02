"""Tests for QEMU guest agent operator devserver preflight guard."""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
OPERATOR = _REPO / "scripts/rescue-live/qemu-guest-agent-smoke-operator.sh"


class QemuGuestAgentDevserverPreflightGuardTests(unittest.TestCase):
    def test_operator_script_has_devserver_preflight(self) -> None:
        text = OPERATOR.read_text(encoding="utf-8")
        self.assertIn("assert_devserver_preflight_ok", text)
        self.assertIn("blocked_profile_route_blocked", text)
        self.assertIn("blocked_fleet_api_unavailable", text)
        self.assertIn("/api/fleet/sessions", text)
        self.assertIn("/api/dev-dashboard/status", text)
        self.assertIn("dev_control_enabled", text)
        self.assertIn("local_lab", text)
        self.assertIn("trap restore_release EXIT", text)


if __name__ == "__main__":
    unittest.main()
