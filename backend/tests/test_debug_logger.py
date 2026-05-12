"""
Tests: should_log level merging, redaction recursion, rotate shift, request_id.
Lauf: cd backend && python -m unittest tests.test_debug_logger -v
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys
_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from debug import logger as debug_logger
from debug import levels
from debug import redaction
from debug import context
from debug import rotate as rotate_module


class TestShouldLogLevelMerging(unittest.TestCase):
    def test_disabled_global_only_error(self):
        with mock.patch.object(debug_logger, "get_effective_config_cached") as m:
            m.return_value = {"global": {"enabled": False}}
            self.assertFalse(debug_logger.should_log("INFO", "m", "s"))
            self.assertTrue(debug_logger.should_log("ERROR", "m", "s"))

    def test_enabled_level_filter(self):
        with mock.patch.object(debug_logger, "get_effective_config_cached") as m:
            m.return_value = {"global": {"enabled": True}, "scopes": {"modules": {}}}
            with mock.patch.object(debug_logger, "get_effective_step_config") as g:
                g.return_value = {"enabled": True, "level": "INFO"}
                self.assertTrue(debug_logger.should_log("INFO", "x", "y"))
                self.assertTrue(debug_logger.should_log("ERROR", "x", "y"))
                g.return_value = {"enabled": True, "level": "ERROR"}
                self.assertFalse(debug_logger.should_log("INFO", "x", "y"))
                self.assertTrue(debug_logger.should_log("ERROR", "x", "y"))

    def test_level_compare(self):
        self.assertTrue(levels.should_log_level("ERROR", "INFO"))
        self.assertTrue(levels.should_log_level("INFO", "INFO"))
        self.assertFalse(levels.should_log_level("DEBUG", "INFO"))
        self.assertTrue(levels.should_log_level("WARN", "INFO"))


class TestRedactionRecursion(unittest.TestCase):
    def test_redact_string(self):
        out = redaction.redact_string("password=secret", redaction.compile_patterns([r"password\s*=\s*\S+"]))
        self.assertIn("[REDACTED]", out)
        self.assertNotIn("secret", out)

    def test_redact_value_dict_list_tuple_set(self):
        patterns = redaction.compile_patterns([r"token\s*=\s*\S+"])
        obj = {"a": "token=xyz", "b": [1, "token=foo"], "c": ("t", "token=bar"), "d": {"nested": "token=qux"}}
        out = redaction.redact_value(obj, patterns)
        self.assertIn("[REDACTED]", str(out))
        self.assertEqual(out["b"][0], 1)
        self.assertEqual(out["c"][0], "t")


class TestRotateShift(unittest.TestCase):
    def test_rotate_if_needed_creates_dot1(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "test.jsonl"
            path.write_text("x" * 200)
            self.assertTrue(path.exists())
            rotate_module.rotate_if_needed(str(path), max_size_bytes=100, max_files=3)
            dot1 = path.parent / "test.1.jsonl"
            self.assertTrue(dot1.exists(), "Rotate sollte test.1.jsonl anlegen")
            self.assertFalse(path.exists(), "Base-Datei wurde nach Rotation zu .1 umbenannt")


class TestRequestIdPropagation(unittest.TestCase):
    def test_context_var_set_get_reset(self):
        token = context.bind_request_id()
        rid = context.get_request_id()
        self.assertIsNotNone(rid)
        self.assertTrue(len(rid) > 10)
        context.reset_request_id(token)
        self.assertIsNone(context.get_request_id())
