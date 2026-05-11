"""
Unit-Tests: Modul-Registry (get_all, get_descriptors, get, perform_action).
Lauf: cd backend && python -m pytest tests/test_remote_registry.py -v
      oder: python -m unittest tests.test_remote_registry -v
"""

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.registry import get_registry


class TestModuleRegistry(unittest.TestCase):
    def test_get_descriptors(self):
        reg = get_registry()
        descs = reg.get_descriptors()
        self.assertIsInstance(descs, list)
        ids = [d.id for d in descs]
        self.assertIn("sabrina-tuner", ids)
        self.assertIn("pi-installer", ids)

    def test_get_module(self):
        reg = get_registry()
        m = reg.get("sabrina-tuner")
        self.assertIsNotNone(m)
        self.assertTrue(hasattr(m, "descriptor"))
        self.assertTrue(hasattr(m, "get_state"))
        self.assertTrue(hasattr(m, "perform_action"))
        d = m.descriptor()
        self.assertEqual(d.id, "sabrina-tuner")
        self.assertGreater(len(d.actions), 0)

    def test_get_unknown_module(self):
        reg = get_registry()
        self.assertIsNone(reg.get("unknown-module"))

    def test_get_state(self):
        reg = get_registry()
        m = reg.get("sabrina-tuner")
        state = m.get_state()
        self.assertIn("volume", state)
        self.assertIn("muted", state)
        self.assertIn("station", state)

    def test_perform_action_known(self):
        reg = get_registry()
        m = reg.get("sabrina-tuner")
        result = m.perform_action("set_volume", {"value": 50})
        self.assertTrue(result.get("success"))
        state = m.get_state()
        self.assertEqual(state.get("volume"), 50)

    def test_perform_action_unknown(self):
        reg = get_registry()
        m = reg.get("sabrina-tuner")
        result = m.perform_action("unknown_action", {})
        self.assertFalse(result.get("success"))
        self.assertIn("Unbekannte", result.get("message", ""))

    def test_pi_installer_state_and_action(self):
        reg = get_registry()
        m = reg.get("pi-installer")
        self.assertIsNotNone(m)
        state = m.get_state()
        self.assertIn("job_status", state)
        self.assertIn("last_logs", state)
        result = m.perform_action("start_job", {})
        self.assertTrue(result.get("success"))
        state2 = m.get_state()
        self.assertEqual(state2.get("job_status"), "running")
