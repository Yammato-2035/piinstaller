from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from deploy.runner_rescue_iso_live_runtime_probe import (
    build_rescue_iso_live_runtime_probe_plan,
    execute_rescue_iso_live_runtime_probe,
)

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_PLAN = _H / "rescue_iso_live_runtime_probe_plan.json"
_RES = _H / "rescue_iso_live_runtime_probe_result.json"


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


class DeployRunnerRescueIsoLiveRuntimeProbeV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._p_bak = _PLAN.read_bytes() if _PLAN.exists() else None
        self._r_bak = _RES.read_bytes() if _RES.exists() else None
        _PLAN.unlink(missing_ok=True)
        _RES.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in ((_PLAN, self._p_bak), (_RES, self._r_bak)):
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def test_execute_blocked_without_flag(self) -> None:
        build_rescue_iso_live_runtime_probe_plan(explicit_overwrite=True)
        r = execute_rescue_iso_live_runtime_probe(
            explicit_overwrite=True,
            explicit_execute_iso_live_runtime_probe=False,
        )
        self.assertEqual(r.get("rescue_iso_live_runtime_probe_execute_status"), "blocked")

    def test_full_chain_mocked_http(self) -> None:
        build_rescue_iso_live_runtime_probe_plan(explicit_overwrite=True)

        def fake_open(req: object, timeout: float | None = None) -> _FakeResp:
            u = req.get_full_url() if hasattr(req, "get_full_url") else ""
            if u.endswith("/api/version"):
                return _FakeResp(200, {"project_version": "1.7.0", "product": "setuphelfer"})
            if "/api/health" in u:
                return _FakeResp(200, {"status": "healthy"})
            if u.endswith("/health"):
                return _FakeResp(404, {})
            if "network" in u:
                return _FakeResp(200, {"ok": True})
            if "inspect" in u:
                return _FakeResp(200, {"inspect": "readonly"})
            if "branding-guard" in u:
                return _FakeResp(200, {"code": "DEPLOY_SETUPHELFER_BRANDING_GUARD_CHECK_OK", "setuphelfer_branding_guard_check": {"setuphelfer_branding_guard_check_status": "ok"}})
            return _FakeResp(404, {})

        with mock.patch("deploy.runner_laptop_live_probe_execution_handoff.urllib.request.urlopen", fake_open):
            ex = execute_rescue_iso_live_runtime_probe(
                explicit_overwrite=True,
                explicit_execute_iso_live_runtime_probe=True,
            )
        self.assertEqual(ex.get("rescue_iso_live_runtime_probe_result_status"), "ok")
