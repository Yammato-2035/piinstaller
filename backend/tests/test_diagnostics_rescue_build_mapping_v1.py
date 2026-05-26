from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.diagnostics.matcher import match_diagnoses  # noqa: E402
from core.diagnostics.models import DiagnosticsAnalyzeRequest  # noqa: E402


class DiagnosticsRescueBuildMappingTests(unittest.TestCase):
    def _ids(self, signals: dict[str, object]) -> list[str]:
        hits = match_diagnoses(DiagnosticsAnalyzeRequest(question="", signals=signals))
        return [item.id for item in hits]

    def test_root_policy_signal_maps_to_rescue_build_root(self) -> None:
        ids = self._ids(
            {
                "code": "blocked_requires_operator_sudo_policy",
                "stderr": "sudo: a terminal is required; sudo: a password is required",
            }
        )
        self.assertIn("RESCUE-BUILD-ROOT-001", ids)

    def test_controlled_gate_signal_maps_to_gate_case(self) -> None:
        ids = self._ids(
            {
                "code": "blocked_controlled_build_gate_required",
                "stderr": "Use controlled gate before running lb build.",
            }
        )
        self.assertIn("RESCUE-BUILD-GATE-001", ids)

    def test_missing_rsvg_tooling_maps_to_tool_case(self) -> None:
        ids = self._ids(
            {
                "code": "blocked_build_tools_missing",
                "summary": "rsvg-convert fehlt; librsvg2-bin fehlt",
            }
        )
        self.assertIn("RESCUE-BUILD-TOOL-001", ids)

    def test_legacy_rsvg_expectation_maps_to_compat_case(self) -> None:
        ids = self._ids(
            {
                "code": "blocked_legacy_rsvg_command_missing",
                "summary": "live-build erwartet /usr/bin/rsvg; rsvg-convert vorhanden, aber rsvg fehlt",
            }
        )
        self.assertIn("RESCUE-BUILD-RSVG-001", ids)

    def test_deferred_architecture_track_maps_to_arch_case(self) -> None:
        ids = self._ids(
            {
                "requested_architecture": "arm64",
                "architecture_track_status": "deferred",
            }
        )
        self.assertIn("RESCUE-BUILD-ARCH-001", ids)

    def test_notification_provider_limit_maps_to_notification_case(self) -> None:
        ids = self._ids(
            {
                "classification": "notification.email.provider_limit_exceeded",
                "email_status": "provider_limit",
                "stderr": "554 5.7.0 outgoing message limit exceeded",
            }
        )
        self.assertIn("NOTIFICATION-EMAIL-PROVIDER-001", ids)


if __name__ == "__main__":
    unittest.main()
