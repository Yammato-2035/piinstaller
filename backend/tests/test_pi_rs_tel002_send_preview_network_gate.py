"""PI-RS-TEL-002 send-preview network gate tests."""

from __future__ import annotations

import asyncio
import json
import os
import unittest
from unittest.mock import patch

from core.rescue_lab_telemetry_config import ENV_LIVE_TEST
from core.rescue_lab_telemetry_send_preview_gate import (
    SendPreviewOptions,
    execute_send_preview,
    reset_send_preview_for_tests,
)
from core.rescue_lab_telemetry_status import reset_last_send_status_for_tests


class SendPreviewNetworkGateTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_send_preview_for_tests()
        reset_last_send_status_for_tests()

    def tearDown(self) -> None:
        reset_send_preview_for_tests()
        reset_last_send_status_for_tests()

    def test_default_no_live_send(self) -> None:
        with patch("core.rescue_lab_telemetry_send_preview_gate.load_rescue_lab_telemetry_config") as mock_cfg:
            from core.rescue_lab_telemetry_model import RescueLabTelemetryConfig

            mock_cfg.return_value = RescueLabTelemetryConfig(
                lab_base_url="http://lab.example.test",
                client_id="fake-rescue-stick-lab-client",
                secret="test-secret",
            )
            with patch(
                "core.rescue_lab_telemetry_send_preview_gate.build_reachability_summary",
                return_value={
                    "network_state": "telemetry_reachable",
                    "telemetry_reachability": "reachable",
                    "warnings": [],
                    "errors": [],
                },
            ):
                with patch("core.rescue_lab_telemetry_send_preview_gate.send_rescue_lab_telemetry") as mock_send:
                    result = execute_send_preview(profile_allowed=True, options=SendPreviewOptions())
        mock_send.assert_not_called()
        self.assertFalse(result["result"]["send_executed"])
        self.assertEqual(result["result"]["send_mode"], "dry_run")

    def test_allow_send_without_live_env_flag_no_send(self) -> None:
        with patch.dict(os.environ, {ENV_LIVE_TEST: ""}, clear=False):
            with patch("core.rescue_lab_telemetry_send_preview_gate.load_rescue_lab_telemetry_config") as mock_cfg:
                from core.rescue_lab_telemetry_model import RescueLabTelemetryConfig

                mock_cfg.return_value = RescueLabTelemetryConfig(
                    lab_base_url="http://lab.example.test",
                    client_id="fake-rescue-stick-lab-client",
                    secret="test-secret",
                )
                with patch(
                    "core.rescue_lab_telemetry_send_preview_gate.build_reachability_summary",
                    return_value={
                        "network_state": "telemetry_reachable",
                        "telemetry_reachability": "reachable",
                        "warnings": [],
                        "errors": [],
                    },
                ):
                    with patch("core.rescue_lab_telemetry_send_preview_gate.send_rescue_lab_telemetry") as mock_send:
                        result = execute_send_preview(
                            profile_allowed=True,
                            options=SendPreviewOptions(allow_send_when_reachable=True),
                        )
        mock_send.assert_not_called()
        self.assertFalse(result["result"]["send_executed"])

    def test_missing_secret_blocks_before_network(self) -> None:
        with patch("core.rescue_lab_telemetry_send_preview_gate.load_rescue_lab_telemetry_config") as mock_cfg:
            from core.rescue_lab_telemetry_model import RescueLabTelemetryConfig

            mock_cfg.return_value = RescueLabTelemetryConfig(
                lab_base_url="http://lab.example.test",
                client_id="fake-rescue-stick-lab-client",
                secret=None,
            )
            with patch("core.rescue_lab_telemetry_send_preview_gate.build_reachability_summary") as mock_reach:
                result = execute_send_preview(profile_allowed=True, options=SendPreviewOptions())
        mock_reach.assert_not_called()
        self.assertEqual(result["result"]["network_state"], "blocked_missing_secret")

    def test_missing_url_blocks_before_network(self) -> None:
        with patch("core.rescue_lab_telemetry_send_preview_gate.load_rescue_lab_telemetry_config") as mock_cfg:
            from core.rescue_lab_telemetry_model import RescueLabTelemetryConfig

            mock_cfg.return_value = RescueLabTelemetryConfig(
                lab_base_url=None,
                client_id="fake-rescue-stick-lab-client",
                secret="test-secret",
            )
            with patch("core.rescue_lab_telemetry_send_preview_gate.build_reachability_summary") as mock_reach:
                result = execute_send_preview(profile_allowed=True, options=SendPreviewOptions())
        mock_reach.assert_not_called()
        self.assertEqual(result["result"]["network_state"], "blocked_missing_config")

    def test_offline_creates_queue_preview(self) -> None:
        with patch("core.rescue_lab_telemetry_send_preview_gate.load_rescue_lab_telemetry_config") as mock_cfg:
            from core.rescue_lab_telemetry_model import RescueLabTelemetryConfig

            mock_cfg.return_value = RescueLabTelemetryConfig(
                lab_base_url="http://lab.example.test",
                client_id="fake-rescue-stick-lab-client",
                secret="test-secret",
            )
            with patch(
                "core.rescue_lab_telemetry_send_preview_gate.build_reachability_summary",
                return_value={
                    "network_state": "telemetry_unreachable",
                    "telemetry_reachability": "unreachable",
                    "warnings": [],
                    "errors": [],
                },
            ):
                with patch("core.rescue_lab_telemetry_send_preview_gate.write_offline_queue_preview_item") as mock_write:
                    mock_write.return_value = "/tmp/preview.redacted.json"
                    result = execute_send_preview(profile_allowed=True, options=SendPreviewOptions())
        mock_write.assert_called_once()
        self.assertTrue(result["result"]["offline_queue_preview_created"])

    def test_reachable_env_flag_allows_live_send(self) -> None:
        with patch.dict(os.environ, {ENV_LIVE_TEST: "1"}, clear=False):
            with patch("core.rescue_lab_telemetry_send_preview_gate.load_rescue_lab_telemetry_config") as mock_cfg:
                from core.rescue_lab_telemetry_model import RescueLabTelemetryConfig, RescueLabTelemetryResult

                mock_cfg.return_value = RescueLabTelemetryConfig(
                    lab_base_url="http://lab.example.test",
                    client_id="fake-rescue-stick-lab-client",
                    secret="test-secret",
                )
                with patch(
                    "core.rescue_lab_telemetry_send_preview_gate.build_reachability_summary",
                    return_value={
                        "network_state": "telemetry_reachable",
                        "telemetry_reachability": "reachable",
                        "warnings": [],
                        "errors": [],
                    },
                ):
                    with patch("core.rescue_lab_telemetry_send_preview_gate.send_rescue_lab_telemetry") as mock_send:
                        mock_send.return_value = RescueLabTelemetryResult(
                            status="accepted_rescue_lab_telemetry",
                            client_id="fake-rescue-stick-lab-client",
                            product="setuphelfer-rescue-stick",
                            source="rescue_stick_lab_preview",
                            environment="lab",
                            payload_kind="rescue_preview",
                            http_status=202,
                            server_status="accepted_rescue_lab_telemetry",
                            nonce_status="new",
                            sent_at="2026-07-05T12:00:00Z",
                        )
                        result = execute_send_preview(
                            profile_allowed=True,
                            options=SendPreviewOptions(allow_send_when_reachable=True),
                        )
        mock_send.assert_called_once()
        self.assertTrue(result["result"]["send_executed"])
        self.assertEqual(result["result"]["send_mode"], "live_lab_send")

    def test_release_profile_api_403(self) -> None:
        from api.routes.rescue_lab_telemetry import rescue_lab_telemetry_send_preview

        with patch("api.routes.rescue_lab_telemetry._lab_profile_allowed", return_value=False):
            resp = asyncio.run(rescue_lab_telemetry_send_preview())
        self.assertEqual(resp.status_code, 403)

    def test_no_auto_send_on_import(self) -> None:
        import importlib

        mod = importlib.import_module("core.rescue_lab_telemetry_send_preview_gate")
        self.assertTrue(callable(mod.execute_send_preview))
        self.assertFalse(hasattr(mod, "_startup_send_executed"))


if __name__ == "__main__":
    unittest.main()
