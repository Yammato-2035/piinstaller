"""Tests für devserver_agent.spool."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from devserver_agent.models import build_dev_node, build_dev_report, new_report_id
from devserver_agent.spool import AgentSpool, AgentSpoolError


class DevAgentSpoolTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.spool = AgentSpool(Path(self._td.name))

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_save_and_list(self) -> None:
        node = build_dev_node(node_id="n1", display_name="N1", mode="local_lab")
        report = build_dev_report(report_id=new_report_id(), node_id="n1", report_type="inventory", mode="local_lab", payload={})
        saved = self.spool.save_spooled_report(node, report, "test")
        self.assertTrue(saved["ok"])
        listed = self.spool.list_spooled_reports()
        self.assertEqual(listed["count"], 1)

    def test_traversal_blocked(self) -> None:
        with self.assertRaises(AgentSpoolError):
            self.spool.save_spooled_report({}, {"report_id": "../evil"}, "x")

    def test_symlink_blocked_on_read(self) -> None:
        self.spool.root.mkdir(parents=True, exist_ok=True)
        outside = Path(self._td.name).parent / "outside_spool.json"
        outside.write_text("{}", encoding="utf-8")
        link = self.spool.root / "evil.json"
        os.symlink(outside, link)
        listed = self.spool.list_spooled_reports()
        self.assertEqual(listed["count"], 0)

    def test_atomic_write_no_tmp_left(self) -> None:
        node = build_dev_node(node_id="n2", display_name="N2", mode="local_lab")
        report = build_dev_report(report_id=new_report_id(), node_id="n2", report_type="inventory", mode="local_lab", payload={})
        self.spool.save_spooled_report(node, report, "atomic")
        tmps = list(self.spool.root.glob("*.tmp"))
        self.assertEqual(len(tmps), 0)

    def test_retry_calls_client(self) -> None:
        node = build_dev_node(node_id="n3", display_name="N3", mode="local_lab")
        report = build_dev_report(report_id=new_report_id(), node_id="n3", report_type="inventory", mode="local_lab", payload={})
        self.spool.save_spooled_report(node, report, "retry")
        calls = []

        def fake_upload(n, r):
            calls.append(1)
            return {"ok": True, "code": "ok"}

        out = self.spool.retry_spooled_reports(upload_fn=fake_upload)
        self.assertEqual(out["retried"], 1)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
