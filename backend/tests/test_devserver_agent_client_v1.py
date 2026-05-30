"""Tests für devserver_agent.client."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from devserver_agent.client import health_check, post_report, validate_server_health


class DevAgentClientTests(unittest.TestCase):
    def test_health_ok(self) -> None:
        body = json.dumps({"enabled": True, "mode": "local_lab"}).encode()
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("devserver_agent.client.urllib.request.urlopen", return_value=mock_resp):
            result = health_check("http://127.0.0.1:8000")
        self.assertTrue(result["ok"])

    def test_ingest_payload_structure(self) -> None:
        captured = {}

        def fake_urlopen(req, timeout=5):
            captured["url"] = req.full_url
            captured["data"] = json.loads(req.data.decode())
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = json.dumps({"code": "DEV_SERVER_REPORT_ACCEPTED"}).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            return mock_resp

        with patch("devserver_agent.client.urllib.request.urlopen", side_effect=fake_urlopen):
            post_report("http://127.0.0.1:8000", {"node_id": "n1"}, {"report_id": "r1"}, None)
        self.assertIn("node", captured["data"])
        self.assertIn("report", captured["data"])

    def test_unreachable_returns_error(self) -> None:
        import urllib.error
        with patch(
            "devserver_agent.client.urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            result = post_report("http://127.0.0.1:8000", {}, {})
        self.assertFalse(result["ok"])

    def test_public_rescue_send_blocked_at_cli_level(self) -> None:
        validated = validate_server_health({"health": {"enabled": False}}, "public_rescue")
        self.assertFalse(validated["ok"])

    def test_token_not_in_logs(self) -> None:
        import logging
        with patch("devserver_agent.client.logger") as mock_log:
            import urllib.error
            with patch(
                "devserver_agent.client.urllib.request.urlopen",
                side_effect=urllib.error.URLError("fail"),
            ):
                post_report("http://127.0.0.1:8000", {}, {}, "super-secret-token")
            for call in mock_log.warning.call_args_list:
                self.assertNotIn("super-secret-token", str(call))


if __name__ == "__main__":
    unittest.main()
