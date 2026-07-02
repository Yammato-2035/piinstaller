"""Diagnostics import must reject PII."""

from __future__ import annotations

import unittest

from dev.diagnostics_mock_server_v1 import DiagnosticsMockHandler


class DiagnosticsNoPiiImportV1Tests(unittest.TestCase):
    def test_pii_detection(self) -> None:
        handler = DiagnosticsMockHandler.__new__(DiagnosticsMockHandler)
        self.assertTrue(handler._has_pii({"email": "x@y.z"}))
        self.assertFalse(handler._has_pii({"hardware_key": "pci:8086:1234"}))


if __name__ == "__main__":
    unittest.main()
