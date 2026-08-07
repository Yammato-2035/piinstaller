"""Rescue systemd unit policy tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SYSTEMD = REPO / "scripts/rescue-live/image/systemd"
UPDATE_SCRIPT = REPO / "scripts/rescue-live/update-fat32-esp-live-payload.sh"


class RescueSystemdUnitsTests(unittest.TestCase):
    def test_ui_service_has_no_network_online_requires(self) -> None:
        text = (SYSTEMD / "setuphelfer-rescue-ui.service").read_text(encoding="utf-8")
        self.assertNotIn("Requires=network-online.target", text)
        self.assertNotIn("Wants=network-online.target", text)

    def test_ui_service_is_kiosk_opt_in_and_skips_text_exit(self) -> None:
        text = (SYSTEMD / "setuphelfer-rescue-ui.service").read_text(encoding="utf-8")
        self.assertIn("ConditionKernelCommandLine=setuphelfer_kiosk=1", text)
        # Multiple ConditionKernelCommandLine= lines are ORed by systemd — keep exactly one.
        self.assertEqual(text.count("ConditionKernelCommandLine="), 1)
        self.assertIn("SuccessExitStatus=0 5", text)
        self.assertNotIn("ExecStartPre=", text)
        self.assertNotRegex(text, r"(?m)^TTYPath=")
        self.assertIn("Type=oneshot", text)

    def test_prepare_does_not_autostart_ui_service(self) -> None:
        prepare = (REPO / "scripts/rescue-live/prepare-controlled-live-build-tree.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("Do not enable setuphelfer-rescue-ui.service", prepare)
        self.assertNotIn("systemctl enable setuphelfer-rescue-ui.service", prepare)

    def test_gui_start_defers_when_start_assistant_owns_console(self) -> None:
        text = (
            Path(__file__).resolve().parents[2]
            / "scripts/rescue-live/image/setuphelfer-rescue-gui-start.sh"
        ).read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_cmdline_has_start_assistant", text)
        self.assertIn("deferred_to_start_assistant", text)

    def test_evidence_spool_best_effort_oneshot(self) -> None:
        text = (SYSTEMD / "setuphelfer-rescue-evidence-spool.service").read_text(encoding="utf-8")
        self.assertIn("Type=oneshot", text)
        self.assertNotIn("network-online", text)

    def test_payload_update_no_destructive_commands(self) -> None:
        from core import rescue_fat32_esp_payload_update as payload

        hits = payload.script_has_forbidden_destructive_commands(UPDATE_SCRIPT.read_text(encoding="utf-8"))
        self.assertEqual(hits, [])

    def test_network_onboarding_unit_not_boot_autostart(self) -> None:
        prepare = (REPO / "scripts/rescue-live/prepare-controlled-live-build-tree.sh").read_text(encoding="utf-8")
        block = prepare.split("Description=Setuphelfer Rescue Network Onboarding", 1)[1].split("EOF", 1)[0]
        self.assertIn("network-user-requested", block)
        self.assertNotIn("--boot-trigger", block)


if __name__ == "__main__":
    unittest.main()
