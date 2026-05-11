from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_laptop_failure_test_execution_readiness_final_gate import (
    build_laptop_failure_test_execution_readiness_final_gate,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_OUT = _HANDOFF / "laptop_failure_test_execution_readiness_gate.json"
_BRAND = _HANDOFF / "setuphelfer_branding_guard_check.json"
_REPORT_DE = _REPO_ROOT / "docs/evidence/LAPTOP_FAILURE_TEST_READINESS_REPORT_DE.md"
_REPORT_EN = _REPO_ROOT / "docs/evidence/LAPTOP_FAILURE_TEST_READINESS_REPORT_EN.md"
_RUNNER = _REPO_ROOT / "backend/deploy/runner_laptop_failure_test_execution_readiness_final_gate.py"


class DeployRunnerLaptopFailureTestExecutionReadinessFinalGateV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._out_bak = _OUT.read_bytes() if _OUT.exists() else None
        self._brand_bak = _BRAND.read_bytes() if _BRAND.exists() else None
        self._rde_bak = _REPORT_DE.read_bytes() if _REPORT_DE.exists() else None
        self._ren_bak = _REPORT_EN.read_bytes() if _REPORT_EN.exists() else None
        _OUT.unlink(missing_ok=True)
        _BRAND.write_text(json.dumps({"branding_guard_status": "ok"}), encoding="utf-8")

    def tearDown(self) -> None:
        if self._out_bak is None:
            _OUT.unlink(missing_ok=True)
        else:
            _OUT.write_bytes(self._out_bak)
        if self._brand_bak is None:
            _BRAND.unlink(missing_ok=True)
        else:
            _BRAND.write_bytes(self._brand_bak)
        if self._rde_bak is not None:
            _REPORT_DE.write_bytes(self._rde_bak)
        if self._ren_bak is not None:
            _REPORT_EN.write_bytes(self._ren_bak)

    def test_gate_writes_handoff_and_schema(self) -> None:
        res = build_laptop_failure_test_execution_readiness_final_gate(explicit_overwrite=True, probe_live_system=False)
        self.assertIn(
            res.get("laptop_failure_test_execution_readiness_gate_status"),
            ("ok", "review_required", "blocked"),
        )
        body = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertEqual(body.get("strict_mode"), "laptop_failure_test_execution_readiness_final_gate")
        self.assertIn("phase2_failure_runorder", body)
        self.assertEqual(len(body.get("phase2_failure_runorder") or []), 8)
        self.assertIn("phase6_rescue_readiness_snapshot", body)
        self.assertIn("phase7_blockers", body)
        self.assertTrue(_REPORT_DE.is_file())
        self.assertIn("Gate-Status", _REPORT_DE.read_text(encoding="utf-8"))

    def test_runner_has_no_destructive_ops(self) -> None:
        src = _RUNNER.read_text(encoding="utf-8")
        for bad in ("subprocess.call", "os.system", "restore_execute", "shutil.rmtree"):
            self.assertNotIn(bad, src, msg=bad)

    def test_no_overwrite_without_flag(self) -> None:
        build_laptop_failure_test_execution_readiness_final_gate(explicit_overwrite=True, probe_live_system=False)
        res = build_laptop_failure_test_execution_readiness_final_gate(explicit_overwrite=False, probe_live_system=False)
        self.assertEqual(res.get("laptop_failure_test_execution_readiness_gate_status"), "blocked")

