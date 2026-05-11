"""Inspect API Contract (Phase 0/1): nur Top-Level-Schema."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

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


@unittest.skipUnless(_HAS_APP, "FastAPI TestClient oder app nicht verfügbar")
class TestInspectApiContract(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, base_url="http://localhost")

    def test_get_inspect_run_contract(self):
        response = self.client.get("/api/inspect/run")
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        dict_keys = (
            "system",
            "storage",
            "filesystems",
            "boot",
            "network",
            "capabilities",
        )
        list_keys = ("warnings", "errors", "source_modules")
        phase2_dict_keys = ("classification", "advice", "write_safety_summary")
        for key in dict_keys + list_keys + phase2_dict_keys:
            self.assertIn(key, data)
        for key in dict_keys + phase2_dict_keys:
            self.assertIsInstance(data[key], dict, key)
        for key in list_keys:
            self.assertIsInstance(data[key], list, key)
        cls = data["classification"]
        self.assertIn("system_type", cls)
        self.assertIn("confidence", cls)
        self.assertIn("indicators", cls)
        self.assertIn("risk_level", cls)
        self.assertIsInstance(cls["indicators"], list)
        self.assertIsInstance(cls["confidence"], (int, float))
        adv = data["advice"]
        self.assertIn("recommended_paths", adv)
        self.assertIsInstance(adv["recommended_paths"], list)
        for item in adv["recommended_paths"]:
            self.assertIsInstance(item, dict)
            self.assertIn("code", item)
            self.assertIn("priority", item)
            self.assertIn("requires_confirmation", item)
        wss = data["write_safety_summary"]
        self.assertIn("targets", wss)
        self.assertIsInstance(wss["targets"], list)
