"""PI-RS-TEL-002 reachability API tests."""

from __future__ import annotations

import asyncio
import json
import unittest
from unittest.mock import patch

from core.rescue_lab_telemetry_reachability import reset_reachability_for_tests


class ReachabilityApiTests(unittest.TestCase):
    def tearDown(self) -> None:
        reset_reachability_for_tests()

    def _run(self, coro):  # noqa: ANN001
        return asyncio.run(coro)

    def test_release_profile_403(self) -> None:
        from api.routes.rescue_lab_telemetry import rescue_lab_telemetry_reachability

        with patch("api.routes.rescue_lab_telemetry._lab_profile_allowed", return_value=False):
            resp = self._run(rescue_lab_telemetry_reachability())
        self.assertEqual(resp.status_code, 403)

    def test_lab_profile_200_summary(self) -> None:
        from api.routes.rescue_lab_telemetry import rescue_lab_telemetry_reachability

        with patch("api.routes.rescue_lab_telemetry._lab_profile_allowed", return_value=True):
            with patch("api.routes.rescue_lab_telemetry.build_reachability_summary") as mock_summary:
                mock_summary.return_value = {
                    "network_state": "telemetry_reachable",
                    "telemetry_reachability": "reachable",
                    "production_ready": False,
                    "warnings": [],
                    "errors": [],
                }
                resp = self._run(rescue_lab_telemetry_reachability())
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.body.decode())
        self.assertIn("reachability", body)

    def test_missing_config_blocked(self) -> None:
        from api.routes.rescue_lab_telemetry import rescue_lab_telemetry_reachability

        with patch("api.routes.rescue_lab_telemetry._lab_profile_allowed", return_value=True):
            with patch("api.routes.rescue_lab_telemetry.build_reachability_summary") as mock_summary:
                mock_summary.return_value = {
                    "network_state": "blocked_missing_config",
                    "telemetry_reachability": "skipped_missing_config",
                    "errors": ["lab_base_url_not_configured"],
                    "warnings": [],
                    "production_ready": False,
                }
                resp = self._run(rescue_lab_telemetry_reachability())
        body = json.loads(resp.body.decode())
        self.assertEqual(body["code"], "RESCUE_LAB_TELEMETRY_REACHABILITY_BLOCKED")

    def test_missing_secret_blocked(self) -> None:
        from api.routes.rescue_lab_telemetry import rescue_lab_telemetry_reachability

        with patch("api.routes.rescue_lab_telemetry._lab_profile_allowed", return_value=True):
            with patch("api.routes.rescue_lab_telemetry.build_reachability_summary") as mock_summary:
                mock_summary.return_value = {
                    "network_state": "blocked_missing_secret",
                    "telemetry_reachability": "skipped_missing_secret",
                    "errors": ["lab_secret_not_configured"],
                    "warnings": [],
                    "production_ready": False,
                }
                resp = self._run(rescue_lab_telemetry_reachability())
        body = json.loads(resp.body.decode())
        self.assertEqual(body["code"], "RESCUE_LAB_TELEMETRY_REACHABILITY_BLOCKED")

    def test_reachability_does_not_send_payload(self) -> None:
        from api.routes.rescue_lab_telemetry import rescue_lab_telemetry_reachability

        with patch("api.routes.rescue_lab_telemetry._lab_profile_allowed", return_value=True):
            with patch("core.rescue_lab_telemetry_client.send_rescue_lab_telemetry") as mock_send:
                with patch("core.rescue_lab_telemetry_send_preview_gate.execute_send_preview") as mock_preview:
                    self._run(rescue_lab_telemetry_reachability())
        mock_send.assert_not_called()
        mock_preview.assert_not_called()

    def test_no_secrets_in_response(self) -> None:
        from api.routes.rescue_lab_telemetry import rescue_lab_telemetry_reachability

        with patch("api.routes.rescue_lab_telemetry._lab_profile_allowed", return_value=True):
            with patch("api.routes.rescue_lab_telemetry.build_reachability_summary") as mock_summary:
                mock_summary.return_value = {
                    "network_state": "blocked_missing_secret",
                    "telemetry_reachability": "skipped_missing_secret",
                    "secret_configured": False,
                    "production_ready": False,
                    "warnings": [],
                    "errors": [],
                }
                resp = self._run(rescue_lab_telemetry_reachability())
        text = resp.body.decode()
        self.assertNotIn("test-secret", text)
        self.assertNotIn("BEGIN PRIVATE KEY", text)


if __name__ == "__main__":
    unittest.main()
