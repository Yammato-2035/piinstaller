"""Tests für devserver_agent.collector."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from devserver_agent.collector import (
    CollectorError,
    FORBIDDEN_TOKENS,
    _run_command,
    _validate_command,
    build_dev_report_from_collection,
    collect_hardware_inventory,
)


class DevAgentCollectorTests(unittest.TestCase):
    def test_forbidden_commands_blocked(self) -> None:
        for cmd in ("sudo id", "dd if=/dev/zero", "mkfs.ext4 /dev/sda", "mount /dev/sda1 /mnt"):
            with self.subTest(cmd=cmd):
                with self.assertRaises(CollectorError):
                    _validate_command(cmd)

    def test_systemctl_write_blocked_readonly_ok(self) -> None:
        with self.assertRaises(CollectorError):
            _validate_command("systemctl restart ssh")
        _validate_command("systemctl is-system-running 2>/dev/null || true")

    def test_run_command_timeout(self) -> None:
        import subprocess
        with patch("devserver_agent.collector.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 1)
            result = _run_command("uname -a")
        self.assertEqual(result["stderr"], "timeout")

    def test_stdout_truncated(self) -> None:
        with patch("devserver_agent.collector.subprocess.run") as mock_run:
            mock_run.return_value = type("P", (), {"returncode": 0, "stdout": "x" * 100000, "stderr": ""})()
            result = _run_command("uname -a")
        self.assertIn("truncated", result["stdout"])

    def test_collect_only_builds_node_and_report(self) -> None:
        with patch("devserver_agent.collector._run_commands", return_value=([], [], [])):
            report, _ = build_dev_report_from_collection(node_id="n1", mode="local_lab")
        self.assertEqual(report["node_id"], "n1")
        self.assertIn("payload", report)

    def test_errors_become_warnings(self) -> None:
        with patch("devserver_agent.collector._run_commands", return_value=([], ["w1"], ["e1"])):
            data = collect_hardware_inventory()
        self.assertIn("w1", data.get("warnings", []))


if __name__ == "__main__":
    unittest.main()
