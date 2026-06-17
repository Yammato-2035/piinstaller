"""RS-F2B.1: rescue runtime diagnostics redaction tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_runtime_diagnostics import write_rescue_runtime_diagnostics
from core.telemetry_redaction_contract import redact_telemetry_payload


class TestRescueRuntimeDiagnosticsRedactionV1(unittest.TestCase):
    def test_mac_redacted(self):
        out = redact_telemetry_payload({"mac": "aa:bb:cc:dd:ee:ff"})
        self.assertNotIn("aa:bb:cc:dd:ee:ff", json.dumps(out))

    def test_ip_redacted(self):
        out = redact_telemetry_payload({"ip_addr": "192.168.1.10"})
        self.assertNotIn("192.168.1.10", json.dumps(out))

    def test_serial_redacted(self):
        out = redact_telemetry_payload({"serial": "S736NL0X905337T"})
        self.assertNotIn("S736NL0X905337T", json.dumps(out))

    def test_hostname_redacted(self):
        out = redact_telemetry_payload({"host": "msi.example.com"})
        self.assertNotIn("msi.example.com", json.dumps(out))

    def test_no_wifi_passwords(self):
        out = redact_telemetry_payload({"psk": "wlan-secret"})
        self.assertNotIn("wlan-secret", json.dumps(out))

    def test_run_fallback_marked_non_persistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "evidence"
            with patch("core.rescue_runtime_diagnostics.resolve_rescue_evidence_root") as mock_ev:
                mock_ev.return_value = {
                    "persistent": False,
                    "non_persistent": True,
                    "evidence_root": str(out),
                    "warning": "SETUP_LOGS nicht verfügbar",
                }
                with patch("core.rescue_runtime_diagnostics._run_text", return_value=""):
                    result = write_rescue_runtime_diagnostics()
            self.assertTrue(result.get("non_persistent"))

    def test_setup_logs_preferred_when_persistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "evidence"
            with patch("core.rescue_runtime_diagnostics.resolve_rescue_evidence_root") as mock_ev:
                mock_ev.return_value = {
                    "persistent": True,
                    "non_persistent": False,
                    "evidence_root": str(out),
                }
                with patch("core.rescue_runtime_diagnostics._run_text", return_value=""):
                    result = write_rescue_runtime_diagnostics()
            self.assertTrue(result.get("persistent"))
            self.assertTrue(Path(result["paths"]["json"]).is_file())


if __name__ == "__main__":
    unittest.main()
