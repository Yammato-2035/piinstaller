from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from deploy.runner_laptop_live_probe_execution_handoff import (
    build_laptop_live_probe_final_gate,
    build_laptop_live_probe_plan,
    execute_laptop_live_probe_readonly,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_READINESS = _HANDOFF / "laptop_failure_test_execution_readiness_gate.json"
_PLAN = _HANDOFF / "laptop_live_probe_plan.json"
_RESULT = _HANDOFF / "laptop_live_probe_result.json"
_FINAL = _HANDOFF / "laptop_live_probe_final_gate.json"
_ROUTES = _REPO_ROOT / "backend/deploy/routes.py"
_RUNNER = _REPO_ROOT / "backend/deploy/runner_laptop_live_probe_execution_handoff.py"


class _FakeResp:
    def __init__(self, status: int, body: object) -> None:
        self.status = status
        self._raw = json.dumps(body).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *a: object) -> None:
        return None


class DeployRunnerLaptopLiveProbeExecutionHandoffV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._r_bak = _READINESS.read_bytes() if _READINESS.exists() else None
        self._p_bak = _PLAN.read_bytes() if _PLAN.exists() else None
        self._res_bak = _RESULT.read_bytes() if _RESULT.exists() else None
        self._f_bak = _FINAL.read_bytes() if _FINAL.exists() else None
        for p in (_PLAN, _RESULT, _FINAL):
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in (
            (_READINESS, self._r_bak),
            (_PLAN, self._p_bak),
            (_RESULT, self._res_bak),
            (_FINAL, self._f_bak),
        ):
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def _write_readiness(self, *, abnahme: str = "conditional_review", gate: str = "review_required") -> None:
        _READINESS.write_text(
            json.dumps({"abnahme_decision": abnahme, "gate_status": gate}),
            encoding="utf-8",
        )

    def test_plan_blocked_without_readiness(self) -> None:
        _READINESS.unlink(missing_ok=True)
        res = build_laptop_live_probe_plan(explicit_overwrite=True, live_base_url="http://127.0.0.1:8000")
        self.assertEqual(res.get("laptop_live_probe_plan_status"), "blocked")

    def test_plan_blocked_invalid_base_url(self) -> None:
        self._write_readiness()
        res = build_laptop_live_probe_plan(explicit_overwrite=True, live_base_url="ftp://127.0.0.1:8000")
        self.assertEqual(res.get("laptop_live_probe_plan_status"), "blocked")

    def test_execute_blocked_without_explicit_flag(self) -> None:
        self._write_readiness()
        build_laptop_live_probe_plan(explicit_overwrite=True, live_base_url="http://127.0.0.1:8000")
        res = execute_laptop_live_probe_readonly(explicit_overwrite=True, explicit_execute_live_probe=False)
        self.assertEqual(res.get("laptop_live_probe_execute_readonly_status"), "blocked")

    def test_api_down_blocked(self) -> None:
        self._write_readiness()
        build_laptop_live_probe_plan(explicit_overwrite=True, live_base_url="http://127.0.0.1:8000")

        def boom(*a: object, **k: object) -> None:
            raise OSError("connection refused")

        with mock.patch("deploy.runner_laptop_live_probe_execution_handoff.urllib.request.urlopen", side_effect=boom):
            res = execute_laptop_live_probe_readonly(explicit_overwrite=True, explicit_execute_live_probe=True)
        self.assertEqual(res.get("laptop_live_probe_result_status"), "blocked")

    def test_health_degraded_review_required(self) -> None:
        self._write_readiness()
        build_laptop_live_probe_plan(explicit_overwrite=True, live_base_url="http://127.0.0.1:8000")

        def fake_open(req: object, timeout: float | None = None) -> _FakeResp:
            u = req.get_full_url() if hasattr(req, "get_full_url") else ""
            if u.endswith("/api/version"):
                return _FakeResp(200, {"project_version": "1.7.0", "product": "setuphelfer"})
            if "health" in u:
                return _FakeResp(200, {"status": "degraded"})
            if "network" in u:
                return _FakeResp(200, {"ok": True})
            if "preflight" in u:
                return _FakeResp(200, {"code": "PREFLIGHT_SOURCE_FOUND", "sources": []})
            if u.endswith("/api/backup/verify"):
                return _FakeResp(200, {"code": "backup.verify_missing_file"})
            if "precheck" in u:
                return _FakeResp(200, {"precheck_status": "review_required"})
            if "result-template" in u:
                return _FakeResp(200, {"template_status": "blocked"})
            return _FakeResp(404, {})

        with mock.patch("deploy.runner_laptop_live_probe_execution_handoff.urllib.request.urlopen", fake_open):
            res = execute_laptop_live_probe_readonly(explicit_overwrite=True, explicit_execute_live_probe=True)
        self.assertEqual(res.get("laptop_live_probe_result_status"), "review_required")

    def test_setuphelfer_version_ok(self) -> None:
        self._write_readiness()
        build_laptop_live_probe_plan(explicit_overwrite=True, live_base_url="http://127.0.0.1:8000")

        def fake_open(req: object, timeout: float | None = None) -> _FakeResp:
            u = req.get_full_url() if hasattr(req, "get_full_url") else ""
            if u.endswith("/api/version"):
                return _FakeResp(200, {"project_version": "1.7.0"})
            if "health" in u and "/api/health" in u:
                return _FakeResp(404, {})
            if u.endswith("/health"):
                return _FakeResp(200, {"status": "healthy"})
            if "network" in u:
                return _FakeResp(200, {"ok": True})
            if "preflight" in u:
                return _FakeResp(200, {"code": "PREFLIGHT_SOURCE_FOUND", "sources": []})
            if u.endswith("/api/backup/verify"):
                return _FakeResp(200, {"code": "backup.verify_missing_file"})
            if "precheck" in u:
                return _FakeResp(200, {"precheck_status": "ready_for_manual_runtime"})
            if "result-template" in u:
                return _FakeResp(200, {"template_status": "ok"})
            return _FakeResp(404, {})

        with mock.patch("deploy.runner_laptop_live_probe_execution_handoff.urllib.request.urlopen", fake_open):
            res = execute_laptop_live_probe_readonly(explicit_overwrite=True, explicit_execute_live_probe=True)
        self.assertEqual(res.get("laptop_live_probe_result_status"), "ok")

    def test_legacy_pi_installer_blocked(self) -> None:
        self._write_readiness()
        build_laptop_live_probe_plan(explicit_overwrite=True, live_base_url="http://127.0.0.1:8000")

        def fake_open(req: object, timeout: float | None = None) -> _FakeResp:
            u = req.get_full_url() if hasattr(req, "get_full_url") else ""
            if u.endswith("/api/version"):
                return _FakeResp(200, {"project_version": "1.0.0", "note": "pi-installer legacy ref"})
            if "health" in u and "/api/health" in u:
                return _FakeResp(404, {})
            if u.endswith("/health"):
                return _FakeResp(200, {"status": "healthy"})
            if "network" in u:
                return _FakeResp(200, {"ok": True})
            if "preflight" in u:
                return _FakeResp(200, {"code": "PREFLIGHT_SOURCE_FOUND", "sources": []})
            if u.endswith("/api/backup/verify"):
                return _FakeResp(200, {"code": "backup.verify_missing_file"})
            if "precheck" in u:
                return _FakeResp(200, {"precheck_status": "blocked"})
            if "result-template" in u:
                return _FakeResp(200, {"template_status": "blocked"})
            return _FakeResp(404, {})

        with mock.patch("deploy.runner_laptop_live_probe_execution_handoff.urllib.request.urlopen", fake_open):
            res = execute_laptop_live_probe_readonly(explicit_overwrite=True, explicit_execute_live_probe=True)
        self.assertEqual(res.get("laptop_live_probe_result_status"), "blocked")

    def test_final_gate_chain(self) -> None:
        self._write_readiness(abnahme="pass", gate="ok")
        build_laptop_live_probe_plan(explicit_overwrite=True, live_base_url="http://127.0.0.1:8000")

        def fake_open(req: object, timeout: float | None = None) -> _FakeResp:
            u = req.get_full_url() if hasattr(req, "get_full_url") else ""
            if u.endswith("/api/version"):
                return _FakeResp(200, {"project_version": "1.7.0"})
            if "health" in u and "/api/health" in u:
                return _FakeResp(404, {})
            if u.endswith("/health"):
                return _FakeResp(200, {"status": "healthy"})
            if "network" in u:
                return _FakeResp(200, {"ok": True})
            if "preflight" in u:
                return _FakeResp(200, {"code": "PREFLIGHT_SOURCE_FOUND", "sources": []})
            if u.endswith("/api/backup/verify"):
                return _FakeResp(200, {"code": "backup.verify_missing_file"})
            if "precheck" in u:
                return _FakeResp(200, {"precheck_status": "ready_for_manual_runtime"})
            if "result-template" in u:
                return _FakeResp(200, {"template_status": "ok"})
            return _FakeResp(404, {})

        with mock.patch("deploy.runner_laptop_live_probe_execution_handoff.urllib.request.urlopen", fake_open):
            execute_laptop_live_probe_readonly(explicit_overwrite=True, explicit_execute_live_probe=True)
        fg = build_laptop_live_probe_final_gate(explicit_overwrite=True)
        self.assertEqual(fg.get("laptop_live_probe_final_gate_status"), "ok")
        inner = fg.get("laptop_live_probe_final_gate") or {}
        self.assertTrue(inner.get("api_reachable"))
        self.assertTrue(inner.get("safe_to_start_manual_laptop_failure_run"))

    def test_runner_no_forbidden_calls(self) -> None:
        src = _RUNNER.read_text(encoding="utf-8")
        for bad in ("os.system", "subprocess.call", "subprocess.Popen"):
            self.assertNotIn(bad, src, msg=bad)

    def test_routes_live_probe_no_forbidden_verbs(self) -> None:
        routes = _ROUTES.read_text(encoding="utf-8")
        start = routes.find("@router.post(\"/runner/manual-runtime/laptop-live-probe-plan\")")
        self.assertGreaterEqual(start, 0)
        block = routes[start : start + 2500].lower()
        for b in ("/execute", "/apply", "/install", "/delete", "/release", "/publish"):
            self.assertNotIn(b, block)

