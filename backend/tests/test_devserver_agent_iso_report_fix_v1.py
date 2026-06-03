"""Tests for developer-qemu devserver_agent import path and lab proxy host fixes."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_REPO = Path(__file__).resolve().parents[2]
AUTOPILOT = (
    _REPO
    / "build/rescue/profiles/developer-qemu/includes.chroot/usr/local/sbin/setuphelfer-qemu-smoke-autopilot.sh"
)
BACKEND_ROOT = _REPO / "backend"


class DevserverAgentIsoReportFixTests(unittest.TestCase):
    def test_autopilot_pythonpath_includes_backend(self) -> None:
        text = AUTOPILOT.read_text(encoding="utf-8")
        self.assertIn("PYTHONPATH=/opt/setuphelfer-rescue/backend:/opt/setuphelfer-rescue", text)
        self.assertIn("devserver_agent.cli", text)
        self.assertIn("Host: 127.0.0.1:8000", text)

    def test_import_devserver_agent_with_rescue_pythonpath(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{BACKEND_ROOT}{os.pathsep}{_REPO}"
        proc = subprocess.run(
            [sys.executable, "-c", "import devserver_agent.cli; print('ok')"],
            env=env,
            capture_output=True,
            text=True,
            cwd=str(_REPO),
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)

    def test_local_lab_qemu_guest_host_contract(self) -> None:
        """app._get_allowed_hosts() appends 10.0.2.2 when install_profile is local_lab."""
        self.assertIn("10.0.2.2", open(_REPO / "backend/app.py", encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()
