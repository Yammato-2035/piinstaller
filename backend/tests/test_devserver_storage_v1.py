"""Tests für devserver.storage."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from devserver.models import default_dev_action, default_dev_node, default_dev_report, new_id
from devserver.storage import DevServerStorage, DevServerStorageError


class DevServerStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        self.storage = DevServerStorage(self.root)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_allowed_root_enforced(self) -> None:
        node = default_dev_node(node_id="lab-node-1")
        self.storage.save_node(node)
        loaded = self.storage.load_node("lab-node-1")
        assert loaded is not None
        self.assertEqual(loaded["node_id"], "lab-node-1")

    def test_traversal_blocked(self) -> None:
        with self.assertRaises(DevServerStorageError):
            self.storage.load_node("../etc/passwd")

    def test_symlink_blocked_on_write_target(self) -> None:
        self.storage.ensure_layout()
        link = self.root / "nodes" / "evil.json"
        link.parent.mkdir(parents=True, exist_ok=True)
        outside = self.root.parent / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        os.symlink(outside, link)
        with self.assertRaises(DevServerStorageError):
            self.storage.load_node("evil")

    def test_atomic_write(self) -> None:
        node = default_dev_node(node_id="atomic-1")
        self.storage.save_node(node)
        path = self.root / "nodes" / "atomic-1.json"
        self.assertFalse(path.with_suffix(".json.tmp").exists())
        self.assertTrue(path.is_file())

    def test_summaries_generated(self) -> None:
        self.storage.save_node(default_dev_node(node_id="n1"))
        self.storage.save_report(
            default_dev_report(report_id=new_id("report"), node_id="n1"),
        )
        self.storage.save_action(
            default_dev_action(action_id=new_id("action"), node_id="n1", action_type="ssh_check"),
        )
        ns = self.storage.build_nodes_summary()
        rs = self.storage.build_reports_summary()
        ac = self.storage.build_actions_summary()
        self.assertEqual(ns["count"], 1)
        self.assertEqual(rs["count"], 1)
        self.assertEqual(ac["count"], 1)
        self.assertTrue((self.root / "latest" / "nodes_summary.json").is_file())

    def test_audit_append(self) -> None:
        self.storage.append_audit_event({"event_type": "test", "at": "2026-01-01T00:00:00+00:00"})
        lines = (self.root / "audit" / "dev_server_events.jsonl").read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["event_type"], "test")


if __name__ == "__main__":
    unittest.main()
