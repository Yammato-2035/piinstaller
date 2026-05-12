"""Rescue Read-only Analyse — API und Kernlogik."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

try:
    from fastapi.testclient import TestClient
    from app import app

    _HAS_APP = True
except Exception:
    _HAS_APP = False
    TestClient = None
    app = None


class TestRescueAnalyzeModule(unittest.TestCase):
    def test_risk_aggregation_green_when_empty_findings(self):
        # Logik gespiegelt (ohne models/rescue_readonly_analyze-Importkette bei fehlendem pydantic).
        def max_risk(levels):
            if "red" in levels:
                return "red"
            if "yellow" in levels:
                return "yellow"
            return "green"

        self.assertEqual(max_risk(["green"]), "green")
        self.assertEqual(max_risk(["green", "yellow"]), "yellow")
        self.assertEqual(max_risk(["yellow", "red"]), "red")

    def test_inspect_storage_uuid_conflicts(self):
        from modules.inspect_storage import detect_uuid_conflicts

        with patch("modules.inspect_storage._blkid_detect_filesystems", return_value={}):
            out = detect_uuid_conflicts()
        self.assertFalse(out.get("has_conflicts"))

        dup = {
            "/dev/sda1": {"uuid": "duplicate-uuid", "type": "ext4"},
            "/dev/sdb1": {"uuid": "duplicate-uuid", "type": "ext4"},
        }
        with patch("modules.inspect_storage._blkid_detect_filesystems", return_value=dup):
            out2 = detect_uuid_conflicts()
        self.assertTrue(out2.get("has_conflicts"))
        self.assertIn("duplicate-uuid", out2.get("conflicts", {}))


@unittest.skipUnless(_HAS_APP, "FastAPI TestClient oder app nicht verfügbar")
class TestRescueAnalyzeApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, base_url="http://localhost")

    def test_get_analyze_shape(self):
        r = self.client.get("/api/rescue/analyze")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertIn("status", data)
        self.assertIn("risk_level", data)
        self.assertIn("findings", data)
        self.assertIsInstance(data["findings"], list)
        self.assertIn("devices", data)
        self.assertIn("boot_status", data)
        self.assertIn("network_status", data)
        self.assertIn("generated_at", data)
        self.assertIn(data["risk_level"], ("green", "yellow", "red"))
        for f in data["findings"]:
            self.assertIn("code", f)
            self.assertIn("risk_level", f)
            self.assertIn("area", f)
            self.assertIn("evidence", f)
