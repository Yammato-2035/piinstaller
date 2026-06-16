"""Offline-first rescue boot flow — network/telemetry decoupling tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NETWORK = REPO / "scripts/rescue-live/image/setuphelfer-rescue-network-onboarding"
TELEMETRY = REPO / "scripts/rescue-live/image/setuphelfer-rescue-telemetry-push"
PREPARE = REPO / "scripts/rescue-live/prepare-controlled-live-build-tree.sh"
START_ASSISTANT = REPO / "scripts/rescue-live/image/setuphelfer-rescue-start-assistant"


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

    def test_default_route_wait_requires_wifi_connected(self) -> None:
        # Regression: the non-interactive boot pass must NOT block in
        # wait_default_route (up to 60s) when no Wi-Fi is configured yet. The wait
        # is only meaningful once WIFI_CONNECTED=true, otherwise it froze the start
        # assistant on a blank screen before the interactive Wi-Fi menu appeared.
        text = NETWORK.read_text(encoding="utf-8")
        guard = 'if [[ "$DEFAULT_ROUTE" != true && "$OFFLINE_MODE" != true && "$WIFI_CONNECTED" == true ]]; then'
        self.assertIn(guard, text)

    def test_start_assistant_reuses_existing_media_check(self) -> None:
        # Regression: the media-check.service already hashes the squashfs (~45s on
        # USB) before the assistant runs; re-running it in _step_media froze the TUI
        # for another ~45s. The assistant must reuse MEDIA_JSON when present.
        text = START_ASSISTANT.read_text(encoding="utf-8")
        media_block = text.split("_step_media()", 1)[1].split("_step_network()", 1)[0]
        self.assertIn('if [[ ! -f "$MEDIA_JSON" ]]; then', media_block)
        run_idx = media_block.index("setuphelfer-rescue-media-check")
        guard_idx = media_block.index('if [[ ! -f "$MEDIA_JSON" ]]; then')
        self.assertLess(guard_idx, run_idx, "media-check must only run when MEDIA_JSON is missing")

    def test_wait_online_neutralized_dropin_present(self) -> None:
        text = PREPARE.read_text(encoding="utf-8")
        self.assertIn("systemd-networkd-wait-online.service.d/10-setuphelfer-rescue.conf", text)
        self.assertIn("ExecStart=/bin/true", text)


if __name__ == "__main__":
    unittest.main()
