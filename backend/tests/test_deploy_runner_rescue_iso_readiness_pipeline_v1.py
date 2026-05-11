from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest import mock

from deploy.runner_rescue_iso_readiness_pipeline import (
    build_rescue_bootflow_simulation,
    build_rescue_iso_baseline,
    build_rescue_iso_build_plan,
    build_rescue_iso_filesystem_layout,
    build_rescue_iso_final_readiness_gate,
    validate_offline_recovery_runtime,
    validate_rescue_iso_safety,
)

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_PIPELINE = _REPO / "backend/deploy/runner_rescue_iso_readiness_pipeline.py"
_ROUTES = _REPO / "backend/deploy/routes.py"


class DeployRunnerRescueIsoReadinessPipelineV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._env_bak = os.environ.get("RESCUE_ISO_PIPELINE_TEST")
        self._files = [
            _H / "rescue_iso_baseline.json",
            _H / "rescue_iso_filesystem_layout.json",
            _H / "offline_recovery_runtime_validation.json",
            _H / "rescue_bootflow_simulation.json",
            _H / "rescue_iso_safety_validation.json",
            _H / "rescue_iso_final_readiness_gate.json",
            _H / "rescue_iso_build_plan.json",
            _H / "rescue_debian_live_build_plan.json",
            _H / "rescue_live_build_config.json",
            _H / "setuphelfer_branding_guard_check.json",
            _H / "runtime_identifier_zero_state_verification.json",
            _H / "rescue_final_recovery_readiness_gate.json",
        ]
        self._backs = {p: p.read_bytes() if p.exists() else None for p in self._files}
        for p in self._files:
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._env_bak is None:
            os.environ.pop("RESCUE_ISO_PIPELINE_TEST", None)
        else:
            os.environ["RESCUE_ISO_PIPELINE_TEST"] = self._env_bak
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def _seed_debian_handoffs(self) -> None:
        (_H / "rescue_debian_live_build_plan.json").write_text('{"x":1}', encoding="utf-8")
        (_H / "rescue_live_build_config.json").write_text('{"y":1}', encoding="utf-8")

    def test_missing_debian_live_basis_blocked_simulated(self) -> None:
        os.environ["RESCUE_ISO_PIPELINE_TEST"] = "missing_debian"
        r = build_rescue_iso_baseline(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_iso_baseline_status"), "blocked")

    def test_baseline_ok_with_handoffs(self) -> None:
        self._seed_debian_handoffs()
        r = build_rescue_iso_baseline(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_iso_baseline_status"), "ok")

    def test_filesystem_layout_complete(self) -> None:
        r = build_rescue_iso_filesystem_layout(explicit_overwrite=True)
        body = r.get("rescue_iso_filesystem_layout") or {}
        paths = (body.get("layout") or {}).get("paths") or []
        self.assertGreaterEqual(len(paths), 6)

    def test_bootflow_nine_steps(self) -> None:
        r = build_rescue_bootflow_simulation(explicit_overwrite=True)
        steps = (r.get("rescue_bootflow_simulation") or {}).get("steps") or []
        self.assertEqual(len(steps), 9)

    def test_safety_no_destructive_defaults(self) -> None:
        r = validate_rescue_iso_safety(explicit_overwrite=True)
        body = r.get("rescue_iso_safety_validation") or {}
        self.assertTrue(body.get("no_destructive_defaults"))
        self.assertEqual(r.get("rescue_iso_safety_validation_status"), "ok")

    def test_branding_blocked_final_blocked(self) -> None:
        self._seed_debian_handoffs()
        build_rescue_iso_baseline(explicit_overwrite=True)
        build_rescue_iso_filesystem_layout(explicit_overwrite=True)
        (_H / "setuphelfer_branding_guard_check.json").write_text(
            json.dumps({"branding_guard_status": "blocked"}),
            encoding="utf-8",
        )
        (_H / "runtime_identifier_zero_state_verification.json").write_text(
            json.dumps({"zero_state_status": "ok"}),
            encoding="utf-8",
        )
        validate_offline_recovery_runtime(explicit_overwrite=True)
        build_rescue_bootflow_simulation(explicit_overwrite=True)
        validate_rescue_iso_safety(explicit_overwrite=True)
        (_H / "rescue_final_recovery_readiness_gate.json").write_text(
            json.dumps({"gate_status": "ready"}),
            encoding="utf-8",
        )
        r = build_rescue_iso_final_readiness_gate(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_iso_final_readiness_gate_status"), "blocked")

    def test_final_ready_when_inputs_clean(self) -> None:
        self._seed_debian_handoffs()
        build_rescue_iso_baseline(explicit_overwrite=True)
        build_rescue_iso_filesystem_layout(explicit_overwrite=True)
        (_H / "setuphelfer_branding_guard_check.json").write_text(
            json.dumps({"branding_guard_status": "ok"}),
            encoding="utf-8",
        )
        (_H / "runtime_identifier_zero_state_verification.json").write_text(
            json.dumps({"zero_state_status": "ok"}),
            encoding="utf-8",
        )
        validate_offline_recovery_runtime(explicit_overwrite=True)
        build_rescue_bootflow_simulation(explicit_overwrite=True)
        validate_rescue_iso_safety(explicit_overwrite=True)
        (_H / "rescue_final_recovery_readiness_gate.json").write_text(
            json.dumps({"gate_status": "ready"}),
            encoding="utf-8",
        )
        r = build_rescue_iso_final_readiness_gate(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_iso_final_readiness_gate_status"), "ready")

    def test_offline_blocked_low_rescue_api_count(self) -> None:
        with mock.patch("deploy.runner_rescue_iso_readiness_pipeline._count_rescue_posts", return_value=5):
            r = validate_offline_recovery_runtime(explicit_overwrite=True)
        self.assertEqual(r.get("offline_recovery_runtime_validation_status"), "blocked")

    def test_build_plan_advisory_only(self) -> None:
        r = build_rescue_iso_build_plan(explicit_overwrite=True)
        self.assertIn(r.get("rescue_iso_build_plan_status"), ("ok", "review_required"))

    def test_no_iso_generation_flag(self) -> None:
        self._seed_debian_handoffs()
        r = build_rescue_iso_baseline(explicit_overwrite=True)
        self.assertFalse((r.get("rescue_iso_baseline") or {}).get("iso_build_executed"))

    def test_pipeline_runner_no_subprocess(self) -> None:
        raw = _PIPELINE.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", raw)
        self.assertNotIn("os.system", raw)

    def test_routes_have_iso_readiness_endpoints(self) -> None:
        txt = _ROUTES.read_text(encoding="utf-8")
        for needle in (
            "/rescue/iso-baseline",
            "/rescue/iso-filesystem-layout",
            "/rescue/offline-runtime-validation",
            "/rescue/bootflow-simulation",
            "/rescue/iso-safety-validation",
            "/rescue/iso-final-readiness-gate",
            "/rescue/iso-build-plan",
        ):
            self.assertIn(needle, txt)

    def test_routes_no_forbidden_iso_segments(self) -> None:
        low = _ROUTES.read_text(encoding="utf-8").lower()
        for bad in ("publish-release", "deploy-release", "auto-build", "auto-write", "installer execute"):
            self.assertNotIn(bad, low)
