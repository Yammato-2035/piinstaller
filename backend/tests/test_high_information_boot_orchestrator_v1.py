"""PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007: high_information_boot_orchestrator tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from rescue.high_information_boot_orchestrator import (
    DEFAULT_BOOT_PROFILE,
    STAGE_SPECS,
    run_high_information_boot,
)


def _ok(**evidence):
    return lambda: {"status": "ok", "exit_code": 0, "evidence": dict(evidence), "error": None}


def _failed(error: str = "probe_failed"):
    return lambda: {"status": "failed", "exit_code": 1, "evidence": {}, "error": error}


def _by_id(result: dict, stage_id: str) -> dict:
    for stage in result["stages"]:
        if stage["stage_id"] == stage_id:
            return stage
    raise AssertionError(f"missing stage {stage_id!r}")


class TestStageSpecs(unittest.TestCase):
    def test_stage_order_and_metadata(self) -> None:
        ids = [s["id"] for s in STAGE_SPECS]
        self.assertEqual(
            ids,
            [
                "tui_stabilize",
                "hardware_inventory",
                "baseline_cpu_ram_storage",
                "kernel_acpi_pcie_analysis",
                "driver_firmware_gap_detection",
                "network_pipeline",
                "telemetry_connectivity",
                "controlled_drm_xorg_probe",
                "optional_gui_probe",
                "diagnostics_case",
                "safe_local_remediation",
                "install_readiness",
                "final_evidence_flush",
            ],
        )
        for spec in STAGE_SPECS:
            self.assertIn("timeout_s", spec)
            self.assertIn("blocks_dependent", spec)
            self.assertGreater(spec["timeout_s"], 0)


class TestDefaultsAndSafety(unittest.TestCase):
    def test_no_runners_skips_side_effect_stages_and_defaults_others(self) -> None:
        result = run_high_information_boot(run_id="r1", boot_id="b1")
        self.assertEqual(result["boot_profile"], DEFAULT_BOOT_PROFILE)
        self.assertFalse(result["chromium_started"])
        self.assertFalse(result["secrets_exposed"])
        self.assertTrue(result["tui_survived"])

        skip_without_runner = {
            "network_pipeline",
            "telemetry_connectivity",
            "controlled_drm_xorg_probe",
        }
        for stage in result["stages"]:
            if stage["stage_id"] in skip_without_runner:
                self.assertEqual(stage["status"], "skipped")
                self.assertEqual(stage["evidence"].get("reason"), "injectable_not_provided")
            elif stage["stage_id"] == "optional_gui_probe":
                self.assertEqual(stage["status"], "skipped")
                self.assertEqual(stage["evidence"].get("reason"), "xorg_not_ready")
            else:
                # Tiny in-memory default: ok with empty evidence
                self.assertEqual(stage["status"], "ok")
                self.assertEqual(stage["evidence"], {})

    def test_chromium_never_auto_started(self) -> None:
        result = run_high_information_boot(
            run_id="r1",
            boot_id="b1",
            stage_runners={
                "controlled_drm_xorg_probe": _ok(xorg_ready=True),
                "optional_gui_probe": _ok(),  # ok but no chromium_started flag
            },
            context={"xorg_ready": True},
        )
        self.assertEqual(_by_id(result, "optional_gui_probe")["status"], "ok")
        self.assertFalse(result["chromium_started"])

    def test_chromium_started_only_when_optional_gui_sets_flag(self) -> None:
        result = run_high_information_boot(
            run_id="r1",
            boot_id="b1",
            stage_runners={
                "controlled_drm_xorg_probe": _ok(xorg_ready=True),
                "optional_gui_probe": _ok(chromium_started=True),
            },
        )
        self.assertTrue(result["chromium_started"])
        self.assertFalse(result["secrets_exposed"])


class TestXorgFailureIndependence(unittest.TestCase):
    def test_xorg_failure_continues_independent_stages_and_tui_survives(self) -> None:
        ran: list[str] = []

        def _track(stage_id: str, status: str = "ok"):
            def _runner():
                ran.append(stage_id)
                return {"status": status, "exit_code": 0 if status == "ok" else 1, "evidence": {}, "error": None if status == "ok" else "fail"}

            return _runner

        runners = {
            "tui_stabilize": _track("tui_stabilize"),
            "hardware_inventory": _track("hardware_inventory"),
            "baseline_cpu_ram_storage": _track("baseline_cpu_ram_storage"),
            "kernel_acpi_pcie_analysis": _track("kernel_acpi_pcie_analysis"),
            "driver_firmware_gap_detection": _track("driver_firmware_gap_detection"),
            "network_pipeline": _track("network_pipeline"),
            "telemetry_connectivity": _track("telemetry_connectivity"),
            "controlled_drm_xorg_probe": _track("controlled_drm_xorg_probe", status="failed"),
            "optional_gui_probe": _track("optional_gui_probe"),
            "diagnostics_case": _track("diagnostics_case"),
            "safe_local_remediation": _track("safe_local_remediation"),
            "install_readiness": _track("install_readiness"),
            "final_evidence_flush": _track("final_evidence_flush"),
        }

        result = run_high_information_boot(run_id="r-xorg", boot_id="b-xorg", stage_runners=runners)

        self.assertEqual(_by_id(result, "controlled_drm_xorg_probe")["status"], "failed")
        self.assertEqual(result["xorg_probe"], "failed")
        self.assertTrue(result["tui_survived"])
        self.assertFalse(result["chromium_started"])
        self.assertFalse(result["secrets_exposed"])

        # optional_gui must not run when Xorg is not ready
        self.assertEqual(_by_id(result, "optional_gui_probe")["status"], "skipped")
        self.assertEqual(_by_id(result, "optional_gui_probe")["evidence"].get("reason"), "xorg_not_ready")
        self.assertNotIn("optional_gui_probe", ran)

        # Independent later stages still execute
        for stage_id in (
            "diagnostics_case",
            "safe_local_remediation",
            "install_readiness",
            "final_evidence_flush",
        ):
            self.assertIn(stage_id, ran)
            self.assertEqual(_by_id(result, stage_id)["status"], "ok")

        # Network already ran before Xorg (still "runs" in the pipeline sense)
        self.assertIn("network_pipeline", ran)
        self.assertEqual(_by_id(result, "network_pipeline")["status"], "ok")

    def test_optional_gui_skipped_when_xorg_not_ready_in_context(self) -> None:
        called = {"gui": False}

        def gui_runner():
            called["gui"] = True
            return {"status": "ok", "evidence": {"chromium_started": True}}

        result = run_high_information_boot(
            run_id="r2",
            boot_id="b2",
            stage_runners={"optional_gui_probe": gui_runner},
            context={"xorg_ready": False},
        )
        self.assertFalse(called["gui"])
        self.assertEqual(_by_id(result, "optional_gui_probe")["status"], "skipped")
        self.assertFalse(result["chromium_started"])

    def test_runner_exception_becomes_failed_without_stopping_pipeline(self) -> None:
        def boom():
            raise RuntimeError("injected")

        result = run_high_information_boot(
            run_id="r3",
            boot_id="b3",
            stage_runners={
                "hardware_inventory": boom,
                "install_readiness": _ok(),
                "final_evidence_flush": _ok(),
            },
        )
        failed = _by_id(result, "hardware_inventory")
        self.assertEqual(failed["status"], "failed")
        self.assertIn("RuntimeError", failed["error"] or "")
        self.assertEqual(_by_id(result, "install_readiness")["status"], "ok")
        self.assertEqual(_by_id(result, "final_evidence_flush")["status"], "ok")


if __name__ == "__main__":
    unittest.main()
