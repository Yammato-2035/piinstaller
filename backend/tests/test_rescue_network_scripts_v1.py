"""Shell syntax checks for rescue live image scripts."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IMAGE = REPO / "scripts/rescue-live/image"


class RescueImageScriptSyntaxTests(unittest.TestCase):
    def test_bash_n_all_image_scripts(self) -> None:
        for path in sorted(IMAGE.glob("setuphelfer-rescue-*")):
            if path.suffix == ".sh" or path.name.endswith((".sh", "-onboarding", "-check", "-push", "-pull")) or "setuphelfer-rescue" in path.name:
                proc = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, f"bash -n failed for {path.name}: {proc.stderr}")


if __name__ == "__main__":
    unittest.main()
