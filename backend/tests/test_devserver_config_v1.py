"""Tests für devserver.config."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from devserver.config import load_dev_server_config


class DevServerConfigTests(unittest.TestCase):
    def test_default_disabled(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            cfg = load_dev_server_config()
        self.assertFalse(cfg.enabled)
        self.assertEqual(cfg.mode, "disabled")
        self.assertFalse(cfg.allow_remote_ssh)
        self.assertFalse(cfg.accept_public_uploads)
        self.assertTrue(cfg.require_token)

    def test_local_lab_only_when_explicitly_enabled(self) -> None:
        with patch.dict(
            os.environ,
            {"SETUPHELFER_DEV_SERVER_ENABLED": "true", "SETUPHELFER_DEV_SERVER_MODE": "local_lab"},
            clear=True,
        ):
            cfg = load_dev_server_config()
        self.assertTrue(cfg.enabled)
        self.assertEqual(cfg.mode, "local_lab")

    def test_public_uploads_default_false(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_DEV_SERVER_ENABLED": "true"}, clear=True):
            cfg = load_dev_server_config()
        self.assertFalse(cfg.accept_public_uploads)

    def test_ssh_default_false(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_DEV_SERVER_ENABLED": "true"}, clear=True):
            cfg = load_dev_server_config()
        self.assertFalse(cfg.allow_remote_ssh)
        self.assertFalse(cfg.ssh_allowed)

    def test_storage_root_relative_to_repo(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch.dict(os.environ, {}, clear=True):
                cfg = load_dev_server_config(repo_root=root)
            self.assertTrue(str(cfg.storage_root).endswith("dev-server"))

if __name__ == "__main__":
    unittest.main()
