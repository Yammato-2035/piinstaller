"""Offline-first rescue boot flow — network/telemetry decoupling tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NETWORK = REPO / "scripts/rescue-live/image/setuphelfer-rescue-network-onboarding"
TELEMETRY = REPO / "scripts/rescue-live/image/setuphelfer-rescue-telemetry-push"
PREPARE = REPO / "scripts/rescue-live/prepare-controlled-live-build-tree.sh"


class RescueBootFlowOfflineFirstTests(unittest.TestCase):
    def test_network_onboarding_skips_boot_without_cmdline(self) -> None:
        text = NETWORK.read_text(encoding="utf-8")
        self.assertIn("SKIPPED_BOOT_WAIT_USER", text)
        self.assertIn("network_onboarding_waits_for_user_action", text)
        self.assertIn("exit 0", text.split("SKIPPED_BOOT_WAIT_USER", 1)[1])

    def test_telemetry_push_skips_without_opt_in(self) -> None:
        text = TELEMETRY.read_text(encoding="utf-8")
        self.assertIn("telemetry_disabled_or_no_consent", text)
        self.assertIn("exit 0", text.split("telemetry_disabled_or_no_consent", 1)[1])

    def test_network_service_not_wanted_by_multi_user_in_prepare(self) -> None:
        text = PREPARE.read_text(encoding="utf-8")
        block = text.split("Description=Setuphelfer Rescue Network Onboarding", 1)[1].split("EOF", 1)[0]
        self.assertIn("network-user-requested", block)
        self.assertNotIn("WantedBy=multi-user.target", block)
        self.assertNotIn("network-online.target", block)

    def test_telemetry_service_not_wanted_by_multi_user(self) -> None:
        text = PREPARE.read_text(encoding="utf-8")
        block = text.split("Description=Setuphelfer Rescue Telemetry Push", 1)[1].split("EOF", 1)[0]
        self.assertIn("telemetry-opt-in", block)
        self.assertNotIn("WantedBy=multi-user.target", block)
        self.assertNotIn("Wants=network-online.target", block)

    def test_wait_online_neutralized_dropin_present(self) -> None:
        text = PREPARE.read_text(encoding="utf-8")
        self.assertIn("systemd-networkd-wait-online.service.d/10-setuphelfer-rescue.conf", text)
        self.assertIn("ExecStart=/bin/true", text)


if __name__ == "__main__":
    unittest.main()
