from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.diagnostics.matcher import match_diagnoses  # noqa: E402
from core.diagnostics.models import DiagnosticsAnalyzeRequest  # noqa: E402
from core.diagnostics.registry import get_case_by_id  # noqa: E402


class RescueBuildDiagnosticsMappingTests(unittest.TestCase):
    def test_sudo_terminal_failure_maps_to_root_policy_diagnostic(self) -> None:
        hits = match_diagnoses(
            DiagnosticsAnalyzeRequest(
                question="",
                signals={
                    "code": "blocked_requires_operator_sudo_policy",
                    "stderr": "sudo: ein Terminal ist erforderlich; sudo: Ein Passwort ist notwendig",
                },
            )
        )
        ids = [item.id for item in hits]
        self.assertIn("RESCUE-BUILD-ROOT-001", ids)

    def test_direct_lb_build_gate_maps_to_controlled_gate_diagnostic(self) -> None:
        hits = match_diagnoses(
            DiagnosticsAnalyzeRequest(
                question="",
                signals={
                    "code": "blocked_controlled_build_gate_required",
                    "stderr": "Use controlled gate before running lb build.",
                },
            )
        )
        ids = [item.id for item in hits]
        self.assertIn("RESCUE-BUILD-GATE-001", ids)

    def test_architecture_matrix_gap_maps_to_arch_diagnostic(self) -> None:
        hits = match_diagnoses(
            DiagnosticsAnalyzeRequest(
                question="",
                signals={
                    "target_architecture": "amd64",
                    "i386_covered": False,
                    "arm64_covered": False,
                    "armhf_covered": False,
                },
            )
        )
        ids = [item.id for item in hits]
        self.assertIn("RESCUE-BUILD-ARCH-001", ids)

    def test_root_policy_diagnostic_links_docs(self) -> None:
        case = get_case_by_id("RESCUE-BUILD-ROOT-001")
        self.assertIsNotNone(case)
        assert case is not None
        self.assertIn("docs/knowledge-base/diagnostics/RESCUE_BUILD_DIAGNOSTICS.md", case.related_docs)
        self.assertIn("operator_policy", case.tags)


if __name__ == "__main__":
    unittest.main()
