"""Pydantic-Validierung DiagnosisRecord / Request."""

import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from models.diagnosis import DiagnosisInterpretRequest, DiagnosisRecord


class TestDiagnosisModel(unittest.TestCase):
    def test_request_minimal(self):
        r = DiagnosisInterpretRequest(area="firewall", event_type="api_error")
        self.assertEqual(r.area, "firewall")
        self.assertEqual(r.extra, {})

    def test_record_confidence_bounds(self):
        with self.assertRaises(ValidationError):
            DiagnosisRecord(
                interpreter_version="v1",
                diagnosis_id="x",
                diagnose_type="unknown",
                severity="low",
                confidence=1.5,
                title="t",
                user_message="m",
                area="a",
            )

    def test_record_serializable(self):
        rec = DiagnosisRecord(
            interpreter_version="v1",
            diagnosis_id="test.id",
            diagnose_type="connectivity",
            severity="medium",
            confidence=0.5,
            title="T",
            user_message="U",
            technical_summary="tech",
            suggested_actions=["a1"],
            quick_fix_available=False,
            source_event={"k": 1},
            area="system",
            beginner_safe=True,
            companion_mode="caution",
        )
        d = rec.model_dump()
        self.assertEqual(d["diagnosis_id"], "test.id")
        self.assertEqual(d["suggested_actions"], ["a1"])


if __name__ == "__main__":
    unittest.main()
