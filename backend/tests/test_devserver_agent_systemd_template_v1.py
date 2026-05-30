"""Tests für setuphelfer-dev-agent.service Template."""

from __future__ import annotations

import unittest
from pathlib import Path

from devserver_agent.systemd import read_template, template_path


class DevAgentSystemdTemplateTests(unittest.TestCase):
    def test_template_exists(self) -> None:
        path = template_path()
        self.assertTrue(path.is_file())

    def test_default_disabled(self) -> None:
        text = read_template()
        self.assertIn("SETUPHELFER_DEV_AGENT_ENABLED=false", text)

    def test_mode_public_rescue(self) -> None:
        text = read_template()
        self.assertIn("SETUPHELFER_DEV_AGENT_MODE=public_rescue", text)

    def test_auto_upload_false(self) -> None:
        text = read_template()
        self.assertIn("SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=false", text)

    def test_no_new_privileges(self) -> None:
        text = read_template()
        self.assertIn("NoNewPrivileges=true", text)

    def test_no_dangerous_exec(self) -> None:
        text = read_template()
        for bad in ("dd ", "mkfs", "mount", "backup", "restore"):
            self.assertNotIn(bad, text.lower())

    def test_exec_uses_cli_module(self) -> None:
        text = read_template()
        self.assertIn("backend.devserver_agent.cli", text)


if __name__ == "__main__":
    unittest.main()
