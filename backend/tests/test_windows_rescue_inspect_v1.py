"""Tests for Windows rescue inspect read-only stub."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import windows_rescue_inspect as wri  # noqa: E402


class WindowsRescueInspectTests(unittest.TestCase):
    def test_bitlocker_unknown_blocks_access(self) -> None:
        bl = wri.evaluate_bitlocker_access({"status": "unknown", "confidence": "low"})
        self.assertFalse(bl["access_allowed"])
        self.assertEqual(bl["blocking_reason"], "WIN-BITLOCKER-UNKNOWN")

    def test_bitlocker_locked_blocks_access(self) -> None:
        bl = wri.evaluate_bitlocker_access({"status": "locked", "confidence": "medium"})
        self.assertFalse(bl["access_allowed"])
        self.assertEqual(bl["blocking_reason"], "WIN-BITLOCKER-LOCKED")

    def test_report_from_plan_blocks_registry_when_bitlocker_unknown(self) -> None:
        plan = {
            "bitlocker": {"status": "unknown", "confidence": "low"},
            "nvme_devices": [{"name": "nvme0n1"}, {"name": "nvme1n1"}],
            "partitions": [{"name": "nvme0n1p3", "fstype": "ntfs"}],
            "windows_candidates": [{"name": "nvme0n1p3", "fstype": "ntfs"}],
            "hardware_hints": {"dual_nvme_detected": True, "target_profile": "2x2TB_NVMe_AMD_Ryzen_NVIDIA"},
            "blocked_reasons": ["bitlocker_unknown_blocks_file_access"],
            "required_operator_actions": ["VERIFY_BITLOCKER_BEFORE_READONLY_MOUNT"],
        }
        report = wri.build_inspect_report_from_plan(plan)
        self.assertFalse(report["safety"]["bitlocker_access_allowed"])
        self.assertFalse(report["windows_health"]["registry_available"])
        self.assertIn("WIN-BITLOCKER-UNKNOWN", report["diagnostics"]["codes"])
        self.assertTrue(report["backup_selection"]["dry_run_only"])
        self.assertEqual(report["backup_selection"]["selected_paths"], [])

    def test_telemetry_without_ack_stays_yellow(self) -> None:
        report = wri.build_inspect_report_from_sample(_backend.parent)
        envelope = wri.build_telemetry_envelope(
            report,
            run_id="run-1",
            device_session_id="sess-1",
            ack_status="queued_local",
        )
        completion = wri.evaluate_completion(report, envelope)
        self.assertEqual(completion["ampel"], "yellow")
        self.assertEqual(envelope["telemetry_transport"]["status"], "queued_local")

    def test_telemetry_green_only_with_ack_and_hash_match(self) -> None:
        report = wri.build_inspect_report_from_sample(_backend.parent)
        report_hash = wri.sha256_canonical_json(report)
        envelope = wri.build_telemetry_envelope(
            report,
            run_id="run-2",
            device_session_id="sess-2",
            ack_status="acknowledged",
            server_ack_id="ack-123",
            server_confirmed_hash_sha256=report_hash,
        )
        completion = wri.evaluate_completion(report, envelope)
        self.assertEqual(completion["ampel"], "green")
        self.assertTrue(envelope["telemetry_transport"]["hash_match"])

    def test_hash_mismatch_is_red(self) -> None:
        report = wri.build_inspect_report_from_sample(_backend.parent)
        envelope = wri.build_telemetry_envelope(
            report,
            run_id="run-3",
            device_session_id="sess-3",
            ack_status="acknowledged",
            server_ack_id="ack-999",
            server_confirmed_hash_sha256="deadbeef",
        )
        completion = wri.evaluate_completion(report, envelope)
        self.assertEqual(completion["ampel"], "red")
        self.assertIn("WIN-TELEMETRY-002", wri.classify_diagnostic_codes({**report, "telemetry": {"server_ack_required": True, "hash_match": False}}))

    def test_repartition_blocked_in_sample(self) -> None:
        report = wri.build_inspect_report_from_sample(_backend.parent)
        self.assertTrue(report["repartition_readiness"]["blocked"])
        self.assertTrue(report["dualboot_readiness"]["planning_only"])

    def test_privacy_guard_blocks_forbidden_keys(self) -> None:
        blocked, code = wri.privacy_guard_blocks({"file_content": "secret"})
        self.assertTrue(blocked)
        self.assertEqual(code, "TELEMETRY-PRIVACY-001")

    def test_sample_has_no_file_content_fields(self) -> None:
        report = wri.build_inspect_report_from_sample(_backend.parent)
        blob = str(report).lower()
        self.assertNotIn("file_content", blob)
        self.assertNotIn("password", blob)
        self.assertEqual(report.get("data_classification"), "sample_only_not_operator_evidence")

    def test_ingest_without_plan_returns_awaiting(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = wri.ingest_operator_hardware_run(root, write_outputs=True)
            self.assertEqual(result["ingest_status"], "awaiting_operator_hardware_run")
            self.assertEqual(result["operator_status"]["status"], "awaiting_operator_hardware_run")
            self.assertFalse(result["operator_status"]["real_laptop_data_present"])

    def test_ingest_with_plan_marks_operator_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = {
                "source": "plan_windows_readonly_inspect",
                "bitlocker": {"status": "unknown", "confidence": "low"},
                "nvme_devices": [{"name": "nvme0n1"}, {"name": "nvme1n1"}],
                "windows_candidates": [{"name": "nvme0n1p3", "fstype": "ntfs"}],
                "hardware": {"cpu_vendor": "AMD", "gpu_vendor": "NVIDIA"},
                "blocked_reasons": ["bitlocker_unknown_blocks_file_access"],
                "required_operator_actions": ["VERIFY_BITLOCKER_BEFORE_READONLY_MOUNT"],
            }
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            result = wri.ingest_operator_hardware_run(root, plan_path=plan_path, write_outputs=False)
            self.assertEqual(result["ingest_status"], "ok")
            self.assertEqual(result["report"]["source"], "operator_hardware_readonly_run")
            self.assertFalse(result["report"]["safety"]["bitlocker_access_allowed"])
            self.assertEqual(result["completion"]["ampel"], "yellow")


if __name__ == "__main__":
    unittest.main()
