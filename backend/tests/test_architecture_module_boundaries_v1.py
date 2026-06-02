from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


class ArchitectureModuleBoundariesTests(unittest.TestCase):
    def test_boundary_script_runs_and_returns_status(self) -> None:
        repo = Path(__file__).resolve().parent.parent.parent
        cp = subprocess.run(
            ["bash", "scripts/check-module-boundaries.sh"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(cp.returncode, 0)
        payload = json.loads(cp.stdout.strip())
        self.assertIn(payload.get("status"), {"ok", "review_required", "blocked"})
        self.assertIn("line_count", payload)
        self.assertIn("include_router_count", payload)


if __name__ == "__main__":
    unittest.main()

