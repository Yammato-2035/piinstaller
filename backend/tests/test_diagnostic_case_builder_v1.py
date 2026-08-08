"""Unit tests for diagnostic case builder + telemetry ACK view (007 Phase 11)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from rescue.diagnostic_case_builder import build_diagnostic_case, build_telemetry_ack_view


class DiagnosticCaseBuilderTests(unittest.TestCase):
    def test_campaign_shape_keys(self) -> None:
        case = build_diagnostic_case(
            run_id="run-1",
            boot_id="boot-3",
            payload_version="1.10.6.0",
            kernel="6.8.0",
            boot_profile="ASUS-TUI-BASELINE",
            findings=[
                {
                    "issue_code": "gui.xorg.not_invoked",
                    "area": "gpu",
                    "status": "confirmed",
                    "safe_remediation": "activate_tui_fallback",
                }
            ],
            hypotheses=[{"id": "h1", "text": "Xorg never started"}],
            driver_gaps=[{"required_driver": "amdgpu", "package_candidates": ["firmware-amd-graphics"]}],
            firmware_gaps=["amdgpu/foo.bin"],
            hardware_state={
                "gpu": "failed",
                "device_binding": "asus-rog-1",
                "linux_target_identified": True,
                "windows_target_identified": True,
                "confidence": 0.8,
            },
            previous_boot_comparison={"changed_factors": ["boot_profile"]},
        )
        for key in (
            "primary_failure_area",
            "confirmed_findings",
            "hypotheses",
            "missing_drivers",
            "missing_firmware",
            "hardware_risks",
            "safe_remediations",
            "install_readiness",
            "next_tests",
            "confidence",
        ):
            self.assertIn(key, case)
        self.assertEqual(case["run_id"], "run-1")
        self.assertEqual(case["boot_id"], "boot-3")
        self.assertEqual(case["primary_failure_area"], "gpu")
        self.assertEqual(len(case["confirmed_findings"]), 1)
        self.assertIn("amdgpu/foo.bin", case["missing_firmware"])
        self.assertIn("activate_tui_fallback", case["safe_remediations"])
        self.assertGreaterEqual(case["confidence"], 0.0)
        self.assertLessEqual(case["confidence"], 1.0)
        self.assertIn(case["install_readiness"], {"ready", "review_required", "blocked", "unknown"})

    def test_install_readiness_blocked_on_risks(self) -> None:
        case = build_diagnostic_case(
            run_id="r",
            boot_id="b",
            payload_version="1.10.6.0",
            kernel="6.8",
            boot_profile="ASUS-00",
            findings=[],
            hypotheses=[],
            driver_gaps=[],
            firmware_gaps=[],
            hardware_state={"hardware_risks": ["nvme_critical_warning"]},
        )
        self.assertEqual(case["install_readiness"], "blocked")


class TelemetryAckViewTests(unittest.TestCase):
    def test_http_200_alone_insufficient(self) -> None:
        view = build_telemetry_ack_view(
            {
                "http_status": 200,
                "accepted": False,
                "correlation_id": "c1",
                "case_id": "case-1",
                "diagnostics_forwarding_status": "queued",
            }
        )
        self.assertFalse(view["ok"])
        self.assertIn("accepted_not_true", view["errors"])
        self.assertIn("http_200_without_accepted", view["errors"])
        self.assertTrue(view["http_200_alone_insufficient"])

    def test_requires_all_ack_fields(self) -> None:
        view = build_telemetry_ack_view({"http_status": 200, "accepted": True})
        self.assertFalse(view["ok"])
        self.assertIn("missing_correlation_id", view["errors"])
        self.assertIn("missing_case_id", view["errors"])
        self.assertIn("missing_diagnostics_forwarding_status", view["errors"])

    def test_accepted_true_ok(self) -> None:
        view = build_telemetry_ack_view(
            {
                "http_status": 200,
                "accepted": True,
                "correlation_id": "corr-9",
                "case_id": "case-9",
                "diagnostics_forwarding_status": "forwarded",
            }
        )
        self.assertTrue(view["ok"])
        self.assertEqual(view["errors"], [])
        self.assertEqual(view["correlation_id"], "corr-9")
        self.assertEqual(view["case_id"], "case-9")
        self.assertEqual(view["diagnostics_forwarding_status"], "forwarded")


if __name__ == "__main__":
    unittest.main()
