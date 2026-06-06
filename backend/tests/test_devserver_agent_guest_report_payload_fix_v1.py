"""Tests for QEMU guest report payload / ingest failure fixes."""

from __future__ import annotations

import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from devserver.config import load_dev_server_config
from devserver_agent.cli import EXIT_OK, main
from devserver_agent.client import lab_proxy_host_header_for_url, post_report


_REPO = Path(__file__).resolve().parents[2]
AUTOPILOT = (
    _REPO
    / "build/rescue/profiles/developer-qemu/includes.chroot/usr/local/sbin/setuphelfer-qemu-smoke-autopilot.sh"
)
VALIDATOR = _REPO / "scripts/rescue-live/validate-rescue-iso-squashfs.sh"


class DevServerProfileSyncTests(unittest.TestCase):
    def test_local_lab_profile_enables_dev_server_without_env(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "local_lab"}, clear=True):
            cfg = load_dev_server_config()
        self.assertTrue(cfg.enabled)
        self.assertEqual(cfg.mode, "local_lab")
        self.assertFalse(cfg.require_token)

    def test_release_profile_stays_disabled_without_developer_capability(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=True):
            cfg = load_dev_server_config()
        self.assertFalse(cfg.enabled)

    def test_release_profile_enables_dev_server_with_developer_capability(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SETUPHELFER_INSTALL_PROFILE": "release",
                "DCC_DEVELOPER_ENABLED": "1",
                "DCC_DEVELOPER_TOKEN": "dev-laptop",
            },
            clear=True,
        ):
            cfg = load_dev_server_config()
        self.assertTrue(cfg.enabled)
        self.assertEqual(cfg.mode, "local_lab")
        self.assertTrue(cfg.require_token)


class DevAgentProxyHostHeaderTests(unittest.TestCase):
    def test_qemu_proxy_url_gets_lab_host_header(self) -> None:
        self.assertEqual(lab_proxy_host_header_for_url("http://10.0.2.2:8001"), "127.0.0.1:8000")

    def test_localhost_no_override(self) -> None:
        self.assertIsNone(lab_proxy_host_header_for_url("http://127.0.0.1:8000"))

    @patch("devserver_agent.client._request_json")
    def test_post_report_passes_host_header(self, mock_req) -> None:
        mock_req.return_value = (200, {"code": "DEV_SERVER_REPORT_ACCEPTED"}, None)
        post_report("http://10.0.2.2:8001", {"node_id": "n1"}, {"report_id": "r1", "node_id": "n1"})
        _args, kwargs = mock_req.call_args
        self.assertEqual(kwargs.get("host_header"), "127.0.0.1:8000")


class DevAgentCliDryRunTests(unittest.TestCase):
    def test_dry_run_no_network(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SETUPHELFER_DEV_AGENT_ENABLED": "true",
                "SETUPHELFER_DEV_AGENT_MODE": "local_lab",
                "SETUPHELFER_DEV_AGENT_AUTO_UPLOAD": "true",
            },
            clear=True,
        ):
            with patch("devserver_agent.cli.build_dev_report_from_collection", return_value=({"report_id": "r1", "warnings": [], "payload": {}}, {})):
                with patch("devserver_agent.cli.build_dev_node_from_config", return_value={"node_id": "n1"}):
                    with patch("devserver_agent.cli.enforce_mode_redaction", return_value=({"report_id": "r1"}, [], [])):
                        with patch("devserver_agent.cli._resolve_url_for_run", return_value={"selected_url": "http://10.0.2.2:8001"}):
                            buf = io.StringIO()
                            with redirect_stdout(buf):
                                code = main(["--mode", "local_lab", "--dry-run", "--json"])
        self.assertEqual(code, EXIT_OK)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["code"], "DEV_AGENT_DRY_RUN_OK")
        self.assertFalse(data["network"])
        self.assertEqual(data["host_header"], "127.0.0.1:8000")

    def test_print_payload_includes_route(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_DEV_AGENT_MODE": "local_lab"}, clear=True):
            with patch("devserver_agent.cli.build_dev_report_from_collection", return_value=({"report_id": "r1"}, {})):
                with patch("devserver_agent.cli.build_dev_node_from_config", return_value={"node_id": "n1"}):
                    with patch("devserver_agent.cli.enforce_mode_redaction", return_value=({"report_id": "r1"}, [], [])):
                        with patch("devserver_agent.cli._resolve_url_for_run", return_value={"selected_url": "http://127.0.0.1:8000"}):
                            buf = io.StringIO()
                            with redirect_stdout(buf):
                                code = main(["--print-payload", "--json"])
        self.assertEqual(code, EXIT_OK)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["route"], "/api/dev-server/ingest/report")


class AutopilotSerialMarkerTests(unittest.TestCase):
    def test_autopilot_has_send_markers_and_subprocess_cli(self) -> None:
        text = AUTOPILOT.read_text(encoding="utf-8")
        for marker in (
            "SETUPHELFER_DEVSERVER_AGENT_SEND_START",
            "SETUPHELFER_DEVSERVER_AGENT_SEND_TARGET",
            "SETUPHELFER_DEVSERVER_AGENT_SEND_HTTP_STATUS",
            "SETUPHELFER_DEVSERVER_AGENT_SEND_RESPONSE_BODY",
            "SETUPHELFER_DEVSERVER_AGENT_SEND_OK",
            "SETUPHELFER_DEVSERVER_AGENT_SEND_FAILED",
            "devserver_agent.cli",
            "SETUPHELFER_QEMU_SMOKE_RESULT_JSON_BEGIN",
            "SETUPHELFER_QEMU_SMOKE_RESULT_JSON_END",
        ):
            self.assertIn(marker, text)

    def test_validator_accepts_subprocess_cli_pattern(self) -> None:
        text = AUTOPILOT.read_text(encoding="utf-8")
        self.assertRegex(text, r"-m[[:space:]]+devserver_agent\.cli|devserver_agent\.cli")
        validator = VALIDATOR.read_text(encoding="utf-8")
        self.assertIn("devserver_agent\\.cli", validator)


if __name__ == "__main__":
    unittest.main()
