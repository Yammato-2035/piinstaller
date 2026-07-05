"""Master assessment evidence writer script tests."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/rescue/write-master-assessment-evidence.sh"


class MasterAssessmentEvidenceScriptV1Tests(unittest.TestCase):
    def test_script_writes_bundle(self) -> None:
        self.assertTrue(SCRIPT.is_file())
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "SETUP_LOGS": tmp}
            subprocess.run(["bash", str(SCRIPT)], check=True, env=env, cwd=str(REPO))
            bundle = Path(tmp) / "setuphelfer/evidence/master-assessment-bundle-v1.json"
            self.assertTrue(bundle.is_file())
            data = json.loads(bundle.read_text(encoding="utf-8"))
            self.assertIn("system_assessment", data)


if __name__ == "__main__":
    unittest.main()
