"""Tests für devserver_agent.cli."""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from devserver_agent.cli import EXIT_DISABLED, EXIT_OK, EXIT_PUBLIC_BLOCKED, main


class DevAgentCliTests(unittest.TestCase):
    def test_collect_only_ok(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_DEV_AGENT_MODE": "local_lab"}, clear=True):
            with patch("devserver_agent.cli.build_dev_report_from_collection", return_value=({"report_id": "r1"}, {})):
                with patch("devserver_agent.cli.build_dev_node_from_config", return_value={"node_id": "n1"}):
                    buf = io.StringIO()
                    with redirect_stdout(buf):
                        code = main(["--collect-only", "--json"])
        self.assertEqual(code, EXIT_OK)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["code"], "DEV_AGENT_COLLECT_OK")

    def test_send_disabled_exit_10(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(["--send", "--json"])
        self.assertEqual(code, EXIT_DISABLED)

    def test_public_send_exit_11(self) -> None:
        with patch.dict(
            os.environ,
            {"SETUPHELFER_DEV_AGENT_ENABLED": "true", "SETUPHELFER_DEV_AGENT_MODE": "public_rescue"},
            clear=True,
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(["--send", "--json"])
        self.assertEqual(code, EXIT_PUBLIC_BLOCKED)

    def test_local_lab_send_mocked_ok(self) -> None:
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
                    with patch("devserver_agent.cli.health_check", return_value={"ok": True, "health": {"enabled": True, "mode": "local_lab"}}):
                        with patch("devserver_agent.cli.validate_server_health", return_value={"ok": True, "errors": []}):
                            with patch("devserver_agent.cli.post_report", return_value={"ok": True, "response": {"node_id": "n1", "report_id": "r1"}}):
                                buf = io.StringIO()
                                with redirect_stdout(buf):
                                    code = main(["--mode", "local_lab", "--send", "--json"])
        self.assertEqual(code, EXIT_OK)

    def test_json_output(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with patch("devserver_agent.cli.build_dev_report_from_collection", return_value=({"report_id": "r1"}, {})):
                with patch("devserver_agent.cli.build_dev_node_from_config", return_value={"node_id": "n1"}):
                    buf = io.StringIO()
                    with redirect_stdout(buf):
                        main(["--collect-only", "--json"])
        self.assertTrue(buf.getvalue().strip().startswith("{"))


if __name__ == "__main__":
    unittest.main()
