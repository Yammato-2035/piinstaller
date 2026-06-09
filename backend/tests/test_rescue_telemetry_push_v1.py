"""Telemetry must not block offline-first rescue boot."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from rescue.rescue_boot_status import build_rescue_boot_status, telemetry_is_boot_blocker  # noqa: E402

PREPARE = Path(__file__).resolve().parents[2] / "scripts/rescue-live/prepare-controlled-live-build-tree.sh"


class RescueTelemetryPushTests(unittest.TestCase):
    def test_telemetry_default_not_required(self) -> None:
        status = build_rescue_boot_status()
        self.assertFalse(status["telemetry"]["required"])
        self.assertFalse(telemetry_is_boot_blocker(status["telemetry"]))

    def test_proposed_ui_service_does_not_enable_telemetry_before_menu(self) -> None:
        ui = (Path(__file__).resolve().parents[2] / "scripts/rescue-live/image/systemd/setuphelfer-rescue-ui.service")
        text = ui.read_text(encoding="utf-8")
        self.assertNotIn("telemetry-push", text)

    def test_legacy_telemetry_unit_documented_as_optional_blocker(self) -> None:
        text = PREPARE.read_text(encoding="utf-8")
        self.assertIn("setuphelfer-rescue-telemetry-push.service", text)
        # Foundation documents migration away from boot-time telemetry — legacy still in prepare tree.
        self.assertIn("network-online.target", text)


if __name__ == "__main__":
    unittest.main()
