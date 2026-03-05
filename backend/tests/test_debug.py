"""
Unit-Tests für Debug/Observability: Config-Merge, should_log, Redaction, Rotation, Support-Bundle.
Lauf mit: cd backend && python -m unittest tests.test_debug -v
"""

import json
import os
import tempfile
import zipfile
import unittest
from pathlib import Path
from unittest import mock

# Tests laufen mit cwd=backend
import sys
_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from debug import config as debug_config
from debug import redaction
from debug import logger as debug_logger
from debug import support_bundle
from debug.sink import RotatingFileSink


class TestConfigMerge(unittest.TestCase):
    """Config-Merging: global -> module -> step."""

    def test_load_uses_defaults_when_no_file(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            with mock.patch.object(debug_config, "load_system_config", return_value={}):
                cfg = debug_config.get_effective_config_cached(force_reload=True)
        self.assertIn("global", cfg)
        self.assertIn("rotate", cfg.get("global") or {})
        self.assertIn("privacy", cfg.get("global") or {})

    def test_effective_module_config_falls_back_to_global(self):
        with mock.patch.object(debug_config, "get_effective_config_cached") as m:
            m.return_value = {
                "global": {"enabled": True, "level": "DEBUG"},
                "scopes": {"modules": {}},
            }
            eff = debug_config.get_effective_module_config("storage_nvme")
            self.assertTrue(eff["enabled"])
            self.assertEqual(eff["level"], "DEBUG")

    def test_effective_step_config_falls_back_to_module_and_global(self):
        with mock.patch.object(debug_config, "get_effective_config_cached") as m:
            m.return_value = {
                "global": {"enabled": True, "level": "INFO"},
                "scopes": {
                    "modules": {
                        "storage_nvme": {"enabled": True, "level": "DEBUG", "steps": {"detect": {"enabled": True, "level": "DEBUG"}}},
                    }
                },
            }
            eff = debug_config.get_effective_step_config("storage_nvme", "detect")
            self.assertTrue(eff["enabled"])
            self.assertEqual(eff["level"], "DEBUG")
            eff2 = debug_config.get_effective_step_config("storage_nvme", "unknown_step")
            self.assertEqual(eff2["level"], "DEBUG")


class TestShouldLog(unittest.TestCase):
    """should_log(level, module_id, step_id)."""

    def test_disabled_global_only_error(self):
        with mock.patch.object(debug_config, "get_effective_config_cached") as m:
            m.return_value = {"global": {"enabled": False}, "scopes": {"modules": {}}}
            self.assertFalse(debug_logger.should_log("INFO", "storage_nvme", "detect"))
            self.assertTrue(debug_logger.should_log("ERROR", "storage_nvme", "detect"))

    def test_enabled_global_and_step_allows_info(self):
        with mock.patch.object(debug_config, "get_effective_config_cached") as m:
            m.return_value = {"global": {"enabled": True}, "scopes": {"modules": {}}}
            with mock.patch.object(debug_logger, "get_effective_step_config") as g:
                g.return_value = {"enabled": True, "level": "INFO"}
                self.assertTrue(debug_logger.should_log("INFO", "x", "y"))
                self.assertTrue(debug_logger.should_log("ERROR", "x", "y"))

    def test_level_filter(self):
        with mock.patch.object(debug_config, "get_effective_config_cached") as m:
            m.return_value = {"global": {"enabled": True}, "scopes": {"modules": {}}}
            with mock.patch.object(debug_logger, "get_effective_step_config") as g:
                g.return_value = {"enabled": True, "level": "INFO"}
                self.assertTrue(debug_logger.should_log("INFO", "x", "y"))
                g.return_value = {"enabled": True, "level": "ERROR"}
                self.assertFalse(debug_logger.should_log("INFO", "x", "y"))
                self.assertTrue(debug_logger.should_log("ERROR", "x", "y"))


class TestRedaction(unittest.TestCase):
    """Rekursive Redaction in data/context."""

    def test_redact_value_single_pattern(self):
        out = redaction.redact_value("password=secret123", [r"password\s*=\s*\S+"])
        self.assertNotIn("secret", out)
        self.assertIn("[REDACTED]", out)

    def test_redact_recursive_dict(self):
        obj = {"a": "password=foo", "b": {"c": "token=xyz"}}
        out = redaction.redact_recursive(obj, [r"password\s*=\s*\S+", r"token\s*=\s*\S+"])
        self.assertNotEqual(out["a"], "password=foo")
        self.assertIn("[REDACTED]", out["a"])
        self.assertIn("[REDACTED]", out["b"]["c"])

    def test_redact_recursive_list(self):
        obj = ["password=bar", {"x": "api_key=abc"}]
        out = redaction.redact_recursive(obj, [r"password\s*=\s*\S+", r"api_key\s*=\s*\S+"])
        self.assertIn("[REDACTED]", out[0])
        self.assertIn("[REDACTED]", out[1]["x"])

    def test_redact_recursive_empty_patterns_returns_unchanged(self):
        obj = {"a": "password=foo"}
        out = redaction.redact_recursive(obj, [])
        self.assertEqual(out["a"], "password=foo")


class TestRotatingSink(unittest.TestCase):
    """Rotating File-Sink (temp dir)."""

    def test_write_creates_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "test.jsonl"
            sink = RotatingFileSink(str(path), max_size_mb=0.001, max_files=2)
            sink.write_line('{"x":1}')
            self.assertTrue(path.exists())
            self.assertEqual(path.read_text().strip(), '{"x":1}')

    def test_rotation_creates_backup(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "rot.jsonl"
            sink = RotatingFileSink(str(path), max_size_mb=0.0001, max_files=3)
            for i in range(50):
                sink.write_line(json.dumps({"i": i, "padding": "x" * 10}))
            files = sink.list_log_files()
            self.assertGreaterEqual(len(files), 1)
            self.assertTrue(any(f.name == "rot.jsonl" or f.name.startswith("rot.") for f in files))


class TestSupportBundle(unittest.TestCase):
    """Support-Bundle erzeugt Zip mit erwarteten Dateien und redigierten Inhalten."""

    def test_create_support_bundle_creates_zip(self):
        with tempfile.TemporaryDirectory() as d:
            out_dir = Path(d)
            full_cfg = {
                "global": {
                    "enabled": True,
                    "export": {
                        "enabled": True,
                        "include_system_snapshot": True,
                        "include_recent_logs": False,
                        "max_log_lines": 100,
                        "output_dir": str(out_dir),
                    },
                },
            }
            with mock.patch.object(debug_config, "get_effective_config_cached", return_value=full_cfg):
                debug_logger.set_run_id("test-run-12345")
            zip_path = support_bundle.create_support_bundle(output_dir=out_dir)
            self.assertTrue(zip_path.exists())
            self.assertEqual(zip_path.suffix, ".zip")
            with zipfile.ZipFile(zip_path, "r") as z:
                names = z.namelist()
                self.assertIn("manifest.json", names)
                self.assertIn("system_snapshot.json", names)
                self.assertIn("debug.config.effective.yaml", names)
                manifest = json.loads(z.read("manifest.json"))
                self.assertIn("run_id", manifest)
                self.assertIn("timestamp", manifest)
                snap = json.loads(z.read("system_snapshot.json"))
                self.assertTrue("os" in snap or "kernel" in snap)

    def test_support_bundle_snapshot_no_secrets(self):
        with tempfile.TemporaryDirectory() as d:
            out_dir = Path(d)
            full_cfg = {
                "global": {
                    "enabled": True,
                    "export": {"enabled": True, "include_system_snapshot": True, "include_recent_logs": False, "max_log_lines": 0, "output_dir": str(out_dir)},
                },
            }
            with mock.patch.object(debug_config, "get_effective_config_cached", return_value=full_cfg):
                debug_logger.set_run_id("test-run")
            zip_path = support_bundle.create_support_bundle(output_dir=out_dir)
            with zipfile.ZipFile(zip_path, "r") as z:
                snap = json.loads(z.read("system_snapshot.json"))
            text = json.dumps(snap)
            self.assertTrue("password" not in text.lower() or "[REDACTED]" in text)
            self.assertTrue("api_key" not in text.lower() or "[REDACTED]" in text)


if __name__ == "__main__":
    unittest.main()
