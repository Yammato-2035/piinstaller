"""Tests für devserver.ingest."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from devserver.config import load_dev_server_config
from devserver.ingest import ingest_report
from devserver.storage import DevServerStorage


class DevServerIngestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        self.storage = DevServerStorage(self.root)

    def tearDown(self) -> None:
        self._td.cleanup()

    def _cfg(self, **env: str):
        base = {
            "SETUPHELFER_DEV_SERVER_ENABLED": "true",
            "SETUPHELFER_DEV_SERVER_MODE": "local_lab",
            "SETUPHELFER_DEV_SERVER_TOKEN": "test-token",
        }
        base.update(env)
        with patch.dict(os.environ, base, clear=True):
            return load_dev_server_config(repo_root=self.root.parent)

    def test_disabled_blocks(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            cfg = load_dev_server_config(repo_root=self.root.parent)
        result = ingest_report(
            config=cfg,
            storage=self.storage,
            node_data={"node_id": "n1"},
            report_data={"report_type": "manual", "lab_mode": "local_lab"},
        )
        self.assertEqual(result["code"], "DEV_SERVER_REPORT_BLOCKED")
        self.assertIn("dev_server_disabled", result["errors"])

    def test_local_lab_accepts_raw(self) -> None:
        cfg = self._cfg()
        result = ingest_report(
            config=cfg,
            storage=self.storage,
            node_data={"node_id": "lab-1", "display_name": "Lab VM", "node_kind": "vm"},
            report_data={
                "report_type": "inventory",
                "lab_mode": "local_lab",
                "payload": {"hostname": "raw-host", "cpu": {"cores": 4}},
            },
            auth_token="test-token",
        )
        self.assertEqual(result["code"], "DEV_SERVER_REPORT_ACCEPTED")
        self.assertEqual(result["redaction_status"], "raw_lab")
        report = self.storage.load_report(result["report_id"])
        assert report is not None
        self.assertEqual(report["payload"]["hostname"], "raw-host")

    def test_beta_opt_in_redacted(self) -> None:
        cfg = self._cfg()
        result = ingest_report(
            config=cfg,
            storage=self.storage,
            node_data={"node_id": "beta-1"},
            report_data={
                "report_type": "inventory",
                "lab_mode": "beta_opt_in",
                "payload": {"hostname": "secret", "cpu": {}},
            },
            auth_token="test-token",
        )
        self.assertEqual(result["code"], "DEV_SERVER_REPORT_REDACTED_ACCEPTED")
        report = self.storage.load_report(result["report_id"])
        assert report is not None
        self.assertEqual(report["redaction_status"], "redacted")

    def test_public_rescue_auto_upload_blocked(self) -> None:
        cfg = self._cfg()
        result = ingest_report(
            config=cfg,
            storage=self.storage,
            node_data={"node_id": "pub-1"},
            report_data={"lab_mode": "public_rescue", "payload": {}},
            auth_token="test-token",
        )
        self.assertEqual(result["code"], "DEV_SERVER_REPORT_BLOCKED")
        self.assertIn("public_uploads_blocked", result["errors"])

    def test_node_created(self) -> None:
        cfg = self._cfg()
        ingest_report(
            config=cfg,
            storage=self.storage,
            node_data={"node_id": "new-node", "display_name": "New"},
            report_data={"lab_mode": "local_lab", "payload": {}},
            auth_token="test-token",
        )
        node = self.storage.load_node("new-node")
        self.assertIsNotNone(node)
        self.assertEqual(node["display_name"], "New")

    def test_report_saved(self) -> None:
        cfg = self._cfg()
        result = ingest_report(
            config=cfg,
            storage=self.storage,
            node_data={"node_id": "n-save"},
            report_data={"lab_mode": "local_lab", "payload": {"k": 1}},
            auth_token="test-token",
        )
        self.assertIsNotNone(self.storage.load_report(result["report_id"]))

    def test_audit_event_written(self) -> None:
        cfg = self._cfg()
        ingest_report(
            config=cfg,
            storage=self.storage,
            node_data={"node_id": "n-audit"},
            report_data={"lab_mode": "local_lab", "payload": {}},
            auth_token="test-token",
        )
        audit = self.root / "audit" / "dev_server_events.jsonl"
        self.assertTrue(audit.is_file())
        self.assertIn("report_ingested", audit.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
