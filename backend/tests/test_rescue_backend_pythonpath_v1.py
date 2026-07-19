"""Rescue backend PYTHONPATH must include venv site-packages (psutil)."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COMMON = REPO / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"


class RescueBackendPythonpathTests(unittest.TestCase):
    def test_pythonpath_injects_venv_site_packages(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_backend_pythonpath()", text)
        self.assertIn("site-packages", text)
        self.assertIn("venv/lib", text)

    def test_discovery_runner_uses_backend_python_helpers(self) -> None:
        runner = REPO / "scripts/rescue-live/image/setuphelfer-rescue-auto-discovery-runner"
        text = runner.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_backend_python", text)
        self.assertIn("setuphelfer_rescue_backend_pythonpath", text)


if __name__ == "__main__":
    unittest.main()
