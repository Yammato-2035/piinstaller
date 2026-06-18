"""RS-P2C boot evidence redaction tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.rescue_boot_evidence import build_boot_state, redact_boot_state


class TestRescueBootEvidenceRedactionV1(unittest.TestCase):
    def test_mac_redacted(self):
        raw = {"cmdline": "boot=live mac=aa:bb:cc:dd:ee:ff"}
        out = redact_boot_state(raw)
        self.assertNotIn("aa:bb", out["cmdline"])

    def test_ip_redacted(self):
        raw = {"cmdline": "ip=192.168.1.10"}
        out = redact_boot_state(raw)
        self.assertNotIn("192.168.1.10", out["cmdline"])

    def test_boot_mode_stored(self):
        with patch("core.rescue_boot_evidence._read_cmdline", return_value="setuphelfer_mode=text"):
            out = build_boot_state(phase="text_mode_started")
        self.assertEqual(out["selected_mode"], "text")

    def test_gui_failure_phase(self):
        out = build_boot_state(phase="gui_failed_fallback_tui", extra={"gui_failed": True})
        self.assertTrue(out.get("gui_failed"))

    def test_secrets_blocked_in_redaction(self):
        raw = {"cmdline": "wifi_psk=secret123 token=abc"}
        out = redact_boot_state(raw)
        self.assertNotIn("secret123", str(out))

    def test_backup_execute_false(self):
        out = build_boot_state()
        self.assertFalse(out["backup_execute_allowed"])


if __name__ == "__main__":
    unittest.main()
