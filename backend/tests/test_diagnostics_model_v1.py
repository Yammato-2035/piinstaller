import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.diagnostics.models import DiagnosticCase


class TestDiagnosticsModelV1(unittest.TestCase):
    def test_case_requires_valid_severity(self):
        with self.assertRaises(ValidationError):
            DiagnosticCase(
                id="X",
                domain="backup_restore",
                title_de="x",
                title_en="x",
                summary_de="x",
                summary_en="x",
                severity="fatal",  # type: ignore[arg-type]
                confidence="high",
            )

    def test_case_minimal_valid(self):
        d = DiagnosticCase(
            id="X",
            domain="backup_restore",
            title_de="t",
            title_en="t",
            summary_de="s",
            summary_en="s",
            severity="low",
            confidence="medium",
        )
        self.assertEqual(d.domain, "backup_restore")


if __name__ == "__main__":
    unittest.main()
