"""Version gate for PI-RS-ASUS-PHYSICAL-DIAG-003."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class VersionTests(unittest.TestCase):
    def test_versions(self) -> None:
        app = json.loads((ROOT / "config/version.json").read_text(encoding="utf-8"))
        payload = json.loads((ROOT / "config/rescue_payload_version.json").read_text(encoding="utf-8"))
        self.assertEqual(app["project_version"], "1.9.21.2")
        self.assertEqual(payload["rescue_payload_version"], "1.10.2.3")
        self.assertTrue(payload.get("pi_rs_asus_physical_diag_003"))
        self.assertTrue(payload.get("pi_rs_asus_capture_finalize_004"))


if __name__ == "__main__":
    unittest.main()
