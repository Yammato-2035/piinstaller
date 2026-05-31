"""Tests für devserver_agent.config."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from devserver_agent.config import load_dev_agent_config, validate_server_url


class DevAgentConfigTests(unittest.TestCase):
    def test_default_disabled(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            cfg = load_dev_agent_config()
        self.assertFalse(cfg.enabled)
        self.assertEqual(cfg.mode, "public_rescue")
        self.assertFalse(cfg.auto_upload)

    def test_public_rescue_blocks_auto_upload(self) -> None:
        with patch.dict(
            os.environ,
            {"SETUPHELFER_DEV_AGENT_ENABLED": "true", "SETUPHELFER_DEV_AGENT_AUTO_UPLOAD": "true"},
            clear=True,
        ):
            cfg = load_dev_agent_config()
        self.assertFalse(cfg.auto_upload)
        self.assertFalse(cfg.upload_allowed)

    def test_local_lab_allows_auto_upload_explicitly(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SETUPHELFER_DEV_AGENT_ENABLED": "true",
                "SETUPHELFER_DEV_AGENT_MODE": "local_lab",
                "SETUPHELFER_DEV_AGENT_AUTO_UPLOAD": "true",
            },
            clear=True,
        ):
            cfg = load_dev_agent_config()
        self.assertTrue(cfg.auto_upload)
        self.assertTrue(cfg.upload_allowed)

    def test_public_server_url_blocked(self) -> None:
        ok, err = validate_server_url("https://example.com")
        self.assertFalse(ok)
        self.assertEqual(err, "public_domain_blocked")

    def test_localhost_url_allowed(self) -> None:
        ok, err = validate_server_url("http://127.0.0.1:8000")
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_private_lan_10022_allowed(self) -> None:
        ok, err = validate_server_url("http://10.0.2.2:8000")
        self.assertTrue(ok)
        self.assertIsNone(err)


if __name__ == "__main__":
    unittest.main()
