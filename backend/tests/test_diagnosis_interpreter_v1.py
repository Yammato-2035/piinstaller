"""Interpreter v1: Regelpriorität und konkrete Treffer."""

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from diagnosis.interpret_v1 import INTERPRETER_VERSION, interpret_v1
from models.diagnosis import DiagnosisInterpretRequest


class TestDiagnosisInterpreterV1(unittest.TestCase):
    def test_firewall_sudo_before_generic(self):
        req = DiagnosisInterpretRequest(
            area="firewall",
            event_type="api_error",
            api_status="error",
            message="Sudo-Passwort erforderlich",
        )
        out = interpret_v1(req)
        self.assertEqual(out.diagnosis_id, "firewall.sudo_required")
        self.assertEqual(out.companion_mode, "blocked")
        self.assertEqual(out.interpreter_version, INTERPRETER_VERSION)

    def test_firewall_port_hint(self):
        req = DiagnosisInterpretRequest(
            area="firewall",
            event_type="api_error",
            api_status="error",
            message="Regel konnte nicht hinzugefügt werden: Could not add rule (already exists)",
        )
        out = interpret_v1(req)
        self.assertEqual(out.diagnosis_id, "firewall.rule_apply_failed_port")

    def test_firewall_generic_when_no_port_signal(self):
        req = DiagnosisInterpretRequest(
            area="firewall",
            event_type="api_error",
            api_status="error",
            message="Regel konnte nicht hinzugefügt werden: ERROR: problem running",
        )
        out = interpret_v1(req)
        self.assertEqual(out.diagnosis_id, "firewall.rule_apply_failed_generic")

    def test_webserver_port_conflict(self):
        req = DiagnosisInterpretRequest(
            area="webserver",
            event_type="configure_failed",
            api_status="error",
            message="Job for nginx.service failed: Address already in use (EADDRINUSE) :80",
        )
        out = interpret_v1(req)
        self.assertEqual(out.diagnosis_id, "webserver.port_conflict")
        self.assertEqual(out.companion_mode, "warning")

    def test_webserver_configure_falls_back_without_port_hint(self):
        req = DiagnosisInterpretRequest(
            area="webserver",
            event_type="configure_failed",
            message="Paketquelle temporär nicht erreichbar",
        )
        out = interpret_v1(req)
        self.assertEqual(out.diagnosis_id, "unknown.generic")

    def test_system_timeout(self):
        req = DiagnosisInterpretRequest(
            area="system",
            event_type="backend_unreachable",
            extra={"reason": "timeout"},
        )
        out = interpret_v1(req)
        self.assertEqual(out.diagnosis_id, "system.backend_timeout")
        self.assertEqual(out.severity, "high")

    def test_backup_verify_failed(self):
        req = DiagnosisInterpretRequest(
            area="backup_restore",
            event_type="verify_failed",
            message="checksum mismatch",
            extra={"verify_mode": "basic", "backup_file": "/tmp/x.tar.gz"},
        )
        out = interpret_v1(req)
        self.assertEqual(out.diagnosis_id, "backup_restore.verify_failed_generic")
        self.assertIn("extra", out.source_event)
        self.assertEqual(out.source_event["extra"].get("verify_mode"), "basic")

    def test_fallback_unknown_area(self):
        req = DiagnosisInterpretRequest(area="unknown_module", event_type="foo")
        out = interpret_v1(req)
        self.assertEqual(out.diagnosis_id, "unknown.generic")
        self.assertLessEqual(out.confidence, 0.3)


if __name__ == "__main__":
    unittest.main()
