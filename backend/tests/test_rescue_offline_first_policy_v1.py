"""Offline-first rescue boot policy tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from rescue import rescue_offline_first_policy as policy  # noqa: E402
from rescue.rescue_boot_status import build_rescue_boot_status, network_is_boot_blocker, telemetry_is_boot_blocker  # noqa: E402

UI_SERVICE = Path(__file__).resolve().parents[2] / "scripts/rescue-live/image/systemd/setuphelfer-rescue-ui.service"
TELEMETRY_SERVICE = Path(__file__).resolve().parents[2] / "scripts/rescue-live/prepare-controlled-live-build-tree.sh"


class RescueOfflineFirstPolicyTests(unittest.TestCase):
    def test_rescue_ui_starts_without_network_requirement(self) -> None:
        text = UI_SERVICE.read_text(encoding="utf-8")
        self.assertNotIn("Requires=network-online.target", text)
        self.assertNotIn("Wants=network-online.target", text)

    def test_network_not_boot_blocker_by_default(self) -> None:
        status = build_rescue_boot_status()
        self.assertFalse(network_is_boot_blocker(status["network"]))

    def test_telemetry_default_disabled_not_blocker(self) -> None:
        status = build_rescue_boot_status()
        self.assertEqual(status["telemetry"]["status"], "disabled")
        self.assertFalse(telemetry_is_boot_blocker(status["telemetry"]))

    def test_missing_network_is_review_not_failed(self) -> None:
        self.assertEqual(policy.optional_network_status("not_configured"), "review_required")

    def test_missing_telemetry_is_skipped_when_not_opt_in(self) -> None:
        self.assertEqual(policy.optional_telemetry_status("failed", opt_in=False), "skipped")

    def test_wifi_failure_must_not_trigger_medium_warning(self) -> None:
        self.assertFalse(policy.live_medium_warning_allowed_causes("wifi_not_found"))

    def test_squashfs_mismatch_may_trigger_medium_warning(self) -> None:
        self.assertTrue(policy.live_medium_warning_allowed_causes("squashfs_hash_mismatch"))

    def test_beginner_ui_hides_systemd_failures(self) -> None:
        status = build_rescue_boot_status()
        self.assertFalse(policy.beginner_ui_may_show_systemd_failure(status["ui"]))

    def test_rs001_stays_yellow_in_boot_status(self) -> None:
        status = build_rescue_boot_status()
        self.assertEqual(status["rs001"]["status"], "yellow")


if __name__ == "__main__":
    unittest.main()
