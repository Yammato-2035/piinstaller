"""Rescue network/telemetry gate derivation tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_network_telemetry_gate import derive_network_telemetry_gate  # noqa: E402


class RescueNetworkTelemetryGateTests(unittest.TestCase):
    def test_network_yes_telemetry_no_blockers(self) -> None:
        gate = {
            "target_laptop_booted_from_stick": True,
            "target_network_link_established": True,
            "target_telemetry_health_reached": False,
            "target_telemetry_ingest_ack": False,
        }
        with patch("core.rescue_network_telemetry_gate.build_compact_telemetry_lan_proxy_status", return_value={"running": True, "lan_health_ok": True}):
            with patch("core.rescue_network_telemetry_gate.build_compact_task_pull_status", return_value={"controlled_task_pull_available": True}):
                out = derive_network_telemetry_gate(gate)
        self.assertIn("RESCUE_TARGET_TELEMETRY_HEALTH_NOT_REACHED", out["blockers"])
        self.assertFalse(out["windows_inspect_executable"])

    def test_full_green_allows_windows_inspect(self) -> None:
        gate = {
            "iso_uefi_validated": True,
            "usb_stick_written": True,
            "usb_write_sha256_verified": True,
            "target_laptop_booted_from_stick": True,
            "target_live_media_runtime_stable": True,
            "target_network_link_established": True,
            "target_telemetry_health_reached": True,
            "target_telemetry_ingest_ack": True,
        }
        with patch("core.rescue_network_telemetry_gate.build_compact_telemetry_lan_proxy_status", return_value={"running": True, "lan_health_ok": True}):
            with patch("core.rescue_network_telemetry_gate.build_compact_task_pull_status", return_value={"controlled_task_pull_available": True}):
                with patch("core.rescue_network_telemetry_gate._ingest_ack_present", return_value=True):
                    out = derive_network_telemetry_gate(gate)
        self.assertTrue(out["windows_inspect_executable"])

    def test_media_error_blocks_windows_inspect(self) -> None:
        gate = {
            "target_live_media_runtime_stable": False,
            "target_laptop_booted_from_stick": True,
            "target_network_link_established": True,
            "target_telemetry_health_reached": True,
            "target_telemetry_ingest_ack": True,
        }
        with patch("core.rescue_network_telemetry_gate.build_compact_telemetry_lan_proxy_status", return_value={"running": True, "lan_health_ok": True}):
            with patch("core.rescue_network_telemetry_gate.build_compact_task_pull_status", return_value={"controlled_task_pull_available": True}):
                out = derive_network_telemetry_gate(gate)
        self.assertIn("RESCUE_TARGET_LIVE_MEDIA_SQUASHFS_IO_ERROR", out["blockers"])
        self.assertFalse(out["windows_inspect_executable"])


if __name__ == "__main__":
    unittest.main()
