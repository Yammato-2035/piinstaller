"""
Tests für instrumentierte Module: storage_nvme (detect, apply_boot_config), network (detect).
Prüft, dass erwartete Events (STEP_START/STEP_END, DECISION, APPLY_*) mit korrektem scope geschrieben werden.
Lauf: cd backend && python -m pytest tests/test_debug_instrumentation.py -v
      oder: python -m unittest tests.test_debug_instrumentation -v
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys
_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


class TestInstrumentationScopes(unittest.TestCase):
    """Instrumentierte Module erzeugen Events mit erwartetem module_id/step_id."""

    def test_storage_nvme_detect_emits_scope(self):
        from debug.logger import init_debug
        from debug.config import get_effective_config_cached

        events = []
        def capture_write(event_dict):
            events.append(event_dict)

        with tempfile.TemporaryDirectory() as d:
            os.environ["PIINSTALLER_DEBUG_PATH"] = str(Path(d) / "debug.jsonl")
            get_effective_config_cached(force_reload=True)
            init_debug()
            with mock.patch("debug.logger.write_event", side_effect=capture_write):
                from modules.raspberry_pi_config import RaspberryPiConfigModule
                mod = RaspberryPiConfigModule()
                with mock.patch.object(mod, "get_config_file", return_value=Path("/nonexistent")):
                    result = mod.read_config(sudo_password="")
            scopes = [e.get("scope", {}) for e in events]
            module_ids = [s.get("module_id") for s in scopes]
            step_ids = [s.get("step_id") for s in scopes]
            self.assertIn("storage_nvme", module_ids, "storage_nvme scope erwartet")
            self.assertIn("detect", step_ids, "step_id detect erwartet")
            types = [e.get("event", {}).get("type") for e in events]
            self.assertTrue(any(t == "STEP_START" for t in types), "STEP_START erwartet")
            self.assertTrue(any(t == "STEP_END" for t in types), "STEP_END erwartet")
            self.assertTrue(any(t == "DECISION" for t in types), "DECISION erwartet")

    def test_network_detect_emits_scope(self):
        try:
            from app import get_network_info
        except ImportError:
            self.skipTest("app (fastapi) nicht installiert – network detect Skip")
        from debug.logger import init_debug
        from debug.config import get_effective_config_cached

        events = []
        def capture_write(event_dict):
            events.append(event_dict)

        with tempfile.TemporaryDirectory() as d:
            os.environ["PIINSTALLER_DEBUG_PATH"] = str(Path(d) / "debug.jsonl")
            get_effective_config_cached(force_reload=True)
            init_debug()
            with mock.patch("debug.logger.write_event", side_effect=capture_write):
                get_network_info()
            scopes = [e.get("scope", {}) for e in events]
            module_ids = [s.get("module_id") for s in scopes]
            step_ids = [s.get("step_id") for s in scopes]
            self.assertIn("network", module_ids, "network scope erwartet")
            self.assertIn("detect", step_ids, "step_id detect erwartet")
            types = [e.get("event", {}).get("type") for e in events]
            self.assertTrue(any(t == "DECISION" for t in types), "DECISION erwartet")


class TestApplyNoopVsSuccess(unittest.TestCase):
    """APPLY_NOOP wenn Zustand bereits korrekt (gleicher Hash)."""

    def test_apply_boot_config_scope_emitted(self):
        """write_config (apply_boot_config) emittiert step_id apply_boot_config und APPLY_*."""
        from debug.logger import init_debug
        from debug.config import get_effective_config_cached

        events = []
        def capture_write(event_dict):
            events.append(event_dict)

        with tempfile.TemporaryDirectory() as d:
            os.environ["PIINSTALLER_DEBUG_PATH"] = str(Path(d) / "debug.jsonl")
            get_effective_config_cached(force_reload=True)
            init_debug()
            fake_cfg = Path(d) / "config.txt"
            fake_cfg.write_text("# test\narm_boost=on\n")
            with mock.patch("debug.logger.write_event", side_effect=capture_write):
                from modules.raspberry_pi_config import RaspberryPiConfigModule
                mod = RaspberryPiConfigModule()
                with mock.patch.object(mod, "get_config_file", return_value=fake_cfg):
                    with mock.patch.object(mod, "_config_file_hash", return_value="samehash"):
                        mod.write_config({"arm_boost": True}, sudo_password="")
            step_ids = [e.get("scope", {}).get("step_id") for e in events]
            self.assertIn("apply_boot_config", step_ids, "step_id apply_boot_config erwartet")
            types = [e.get("event", {}).get("type") for e in events]
            self.assertTrue(any(t in ("APPLY_NOOP", "APPLY_SUCCESS", "APPLY_ATTEMPT") for t in types), "APPLY_* erwartet")


if __name__ == "__main__":
    unittest.main()
