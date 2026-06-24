"""Shell syntax checks for rescue live image scripts."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IMAGE = REPO / "scripts/rescue-live/image"


class RescueImageScriptSyntaxTests(unittest.TestCase):
    def test_bash_n_all_image_scripts(self) -> None:
        skip_suffixes = {".txt", ".cfg", ".py", ".service", ".timer", ".md", ".json"}
        for path in sorted(IMAGE.glob("setuphelfer-rescue-*")):
            if not path.is_file() or path.suffix in skip_suffixes:
                continue
            if path.suffix == ".sh" or path.name.endswith(("-onboarding", "-check", "-push", "-pull", "-launch", "-start", "-hold", "-fix")):
                proc = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, f"bash -n failed for {path.name}: {proc.stderr}")


if __name__ == "__main__":
    unittest.main()
