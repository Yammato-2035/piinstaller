"""PI-RS-ASUS-EMERGENCY-LINUX-TELEMETRY-003: boot/hardware sentinels + profiles."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from rescue.asus_boot_profiles import (
    get_asus_profile,
    list_asus_profiles,
    profile_gate_allows,
    resolve_asus_profile_from_cmdline,
    validate_cmdline_against_profile,
)
from rescue.boot_comparison_engine import assert_single_variable_hypothesis, compare_boot_runs
from rescue.boot_stage_sentinel import (
    diagnose_missing_next_stage,
    mark_stage_failed,
    mark_stage_reached,
    new_boot_stage_state,
)
from rescue.diagnostics_forwarding_contract import build_diagnostics_result, validate_ingest_response
from rescue.driver_failure_resolver import resolve_driver_failure
from rescue.hardware_state_sentinel import HardwareDeviceState, transition_device
from rescue.telemetry_spooler import (
    enqueue_telemetry_event,
    init_spool_layout,
    reconcile_event_counts,
    record_ingest_response,
)


class BootStageSentinelTests(unittest.TestCase):
    def test_graphics_scope_not_unknown(self) -> None:
        st = new_boot_stage_state(run_id="r1", boot_profile="ASUS-00")
        mark_stage_reached(st, "critical_modules_loaded")
        diag = diagnose_missing_next_stage(st, "drm_ready")
        self.assertEqual(diag["boot_failure_scope"], "graphics_initialization")
        self.assertNotEqual(diag["boot_failure_scope"], "boot_failed_unknown")

    def test_failed_marker_preserved(self) -> None:
        st = new_boot_stage_state(run_id="r1")
        mark_stage_reached(st, "systemd_started")
        mark_stage_failed(st, "drm_ready", issue_code="drm_timeout")
        self.assertEqual(st.last_successful_marker, "systemd_started")
        self.assertEqual(st.first_failed_marker, "drm_ready")


class HardwareStateSentinelTests(unittest.TestCase):
    def test_transition_event_has_no_serial(self) -> None:
        dev = HardwareDeviceState(device_id="pci:01:00.0", device_class="gpu", vendor_id="1002")
        ev = transition_device(
            dev,
            "driver_missing",
            run_id="r1",
            boot_id="b1",
            driver_expected="amdgpu",
        )
        self.assertIsNone(ev["serial_number"])
        self.assertEqual(ev["driver_expected"], "amdgpu")
        self.assertEqual(ev["issue_code"], "hw_driver_missing")


class DriverFailureResolverTests(unittest.TestCase):
    def test_names_concrete_driver(self) -> None:
        report = resolve_driver_failure(
            device="pci:01:00.0",
            candidate_modules=["amdgpu"],
            module_files_present={"amdgpu": False},
            loaded_modules=[],
        )
        self.assertEqual(report["required_driver"], "amdgpu")
        self.assertIn("amdgpu", report["technical_summary"])
        self.assertNotEqual(report["recommended_next_action"], "driver missing")


class AsusBootProfileTests(unittest.TestCase):
    def test_profiles_exist(self) -> None:
        ids = list_asus_profiles()
        for needed in ("ASUS-00", "ASUS-01", "ASUS-02", "ASUS-03", "ASUS-04", "ASUS-05", "ASUS-RECOVERY"):
            self.assertIn(needed, ids)

    def test_asus01_forbids_nomodeset(self) -> None:
        v = validate_cmdline_against_profile("nomodeset setuphelfer_asus_profile=ASUS-01", "ASUS-01")
        self.assertTrue(any(x.startswith("forbidden_present:nomodeset") for x in v))

    def test_asus05_requires_priors(self) -> None:
        gate = profile_gate_allows("ASUS-05", completed_profiles={"ASUS-01": "passed"})
        self.assertFalse(gate["allowed"])

    def test_resolve_from_cmdline(self) -> None:
        p = resolve_asus_profile_from_cmdline("setuphelfer_asus_profile=ASUS-00 nomodeset")
        self.assertEqual(p["profile_id"], "ASUS-00")
        self.assertFalse(p["allows_gui"])


class BootComparisonTests(unittest.TestCase):
    def test_single_profile_change(self) -> None:
        prev = {"boot_profile": "ASUS-00", "kernel_version": "6.1", "device_ids": []}
        cur = {"boot_profile": "ASUS-01", "kernel_version": "6.1", "device_ids": []}
        out = compare_boot_runs(prev, cur)
        self.assertEqual(out["causality_assessment"], "boot_profile_change_primary")
        self.assertFalse(out["simultaneous_change_violation"])

    def test_hypothesis_required(self) -> None:
        errs = assert_single_variable_hypothesis({"intended_changed_variables": []})
        self.assertIn("missing_hypothesis_changed_variable", errs)


class TelemetrySpoolerTests(unittest.TestCase):
    def test_offline_not_sent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            spool = Path(td)
            init_spool_layout(spool)
            res = enqueue_telemetry_event(
                spool,
                {"event_type": "rescue_boot_started", "technical_summary": "boot"},
                consent_granted=True,
            )
            self.assertEqual(res["telemetry_status"], "queued_offline")
            self.assertNotEqual(res["telemetry_status"], "sent")

    def test_ingest_requires_status_not_http_alone(self) -> None:
        errors = validate_ingest_response({"http_status": 200, "ingest_status": "rejected"})
        self.assertIn("http_200_without_accepted_ingest_status", errors)
        with tempfile.TemporaryDirectory() as td:
            spool = Path(td)
            init_spool_layout(spool)
            state = record_ingest_response(
                spool,
                {
                    "ingest_status": "accepted",
                    "correlation_id": "c1",
                    "received_events": 1,
                    "rejected_events": 0,
                    "redaction_status": "ok",
                    "diagnostics_forwarding_status": "queued",
                    "retry_required": False,
                },
            )
            self.assertEqual(state["status"], "delivered_confirmed")

    def test_reconcile_counts(self) -> None:
        r = reconcile_event_counts(local_total=10, accepted=7, rejected=1, pending_local=2)
        self.assertTrue(r["balanced"])


class DiagnosticsContractTests(unittest.TestCase):
    def test_insufficient_without_concrete_driver(self) -> None:
        result = build_diagnostics_result(
            correlation_id="c1",
            run_id="r1",
            diagnostic_status="confirmed",
            missing_drivers=[{"device_id": "x"}],
            root_cause_confidence=0.9,
        )
        self.assertEqual(result["diagnostic_status"], "insufficient_evidence")
        self.assertLessEqual(result["root_cause_confidence"], 0.49)


if __name__ == "__main__":
    unittest.main()
