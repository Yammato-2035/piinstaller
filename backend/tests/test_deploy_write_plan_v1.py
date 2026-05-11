"""Deploy write plan tests (simulation only, no writes)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load(rel: str, name: str):
    p = _BACKEND / rel
    spec = importlib.util.spec_from_file_location(name, p)
    if not spec or not spec.loader:
        raise ImportError(rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


wp_mod = _load("deploy/write_plan.py", "setuphelfer_deploy_write_plan_test")
routes_mod = _load("deploy/routes.py", "setuphelfer_deploy_routes_write_plan_test")


def _session(dev: str = "/dev/sdz") -> dict:
    return {"target_device": dev}


def _preview(dev: str = "/dev/sdz", src_type: str = "local_image") -> dict:
    return {"target": {"target_device": dev}, "os_source": {"type": src_type}}


def _image(ok: bool = True) -> dict:
    if not ok:
        return {"code": "DEPLOY_IMAGE_INSPECT_FAILED", "image": {}, "verification": {"checksum_expected": True, "checksum_checked": True, "checksum_ok": False}, "errors": ["DEPLOY_IMAGE_CHECKSUM_FAILED"]}
    return {
        "code": "DEPLOY_IMAGE_INSPECT_WARNING",
        "image": {"path": "/cache/a.img", "extension": ".img", "size_bytes": 1},
        "verification": {"checksum_expected": False, "checksum_checked": False, "checksum_ok": None},
        "errors": [],
    }


def _inspect(system_type: str = "EMPTY") -> dict:
    return {"classification": {"system_type": system_type}}


def _safety(device: str = "/dev/sdz", reason_code: str = "SAFETY_EMPTY_DISK", write_allowed: bool = True) -> dict:
    return {
        "policy_code": "safety.summary.v1",
        "targets": [
            {
                "device": device,
                "reason_code": reason_code,
                "write_allowed": write_allowed,
            }
        ],
    }


class TestDeployWritePlanV1(unittest.TestCase):
    def _run(self, **kwargs):
        return wp_mod.generate_deploy_write_plan(
            kwargs.get("deploy_session", _session()),
            kwargs.get("deploy_preview", _preview()),
            kwargs.get("image_inspect", _image()),
            kwargs.get("inspect_result", _inspect()),
            kwargs.get("safety_summary", _safety()),
        )

    def test_target_mismatch_blocked(self):
        out = self._run(deploy_preview=_preview("/dev/sdy"))
        self.assertEqual(out["plan_status"], "blocked")
        self.assertIn("DEPLOY_WRITE_BLOCKED_TARGET_MISMATCH", out["blocked_reasons"])

    def test_systemdisk_blocked(self):
        out = self._run(safety_summary=_safety(reason_code="SAFETY_SYSTEM_DISK", write_allowed=False))
        self.assertEqual(out["plan_status"], "blocked")
        self.assertIn("DEPLOY_WRITE_BLOCKED_SYSTEM_DISK", out["blocked_reasons"])

    def test_windows_dualboot_blocked(self):
        out_win = self._run(safety_summary=_safety(reason_code="SAFETY_WINDOWS_DETECTED", write_allowed=False))
        self.assertIn("DEPLOY_WRITE_BLOCKED_WINDOWS", out_win["blocked_reasons"])
        out_dual = self._run(safety_summary=_safety(reason_code="SAFETY_DUALBOOT", write_allowed=False))
        self.assertIn("DEPLOY_WRITE_BLOCKED_DUALBOOT", out_dual["blocked_reasons"])

    def test_unknown_target_blocked(self):
        out = self._run(safety_summary={"policy_code": "safety.summary.v1", "targets": []})
        self.assertEqual(out["plan_status"], "blocked")
        self.assertIn("DEPLOY_WRITE_BLOCKED_UNKNOWN", out["blocked_reasons"])

    def test_image_invalid_blocked(self):
        out = self._run(image_inspect=_image(ok=False))
        self.assertEqual(out["plan_status"], "blocked")
        self.assertIn("DEPLOY_WRITE_BLOCKED_IMAGE_INVALID", out["blocked_reasons"])

    def test_valid_empty_target_and_valid_image(self):
        out = self._run()
        self.assertIn(out["plan_status"], {"ok", "review_required"})

    def test_all_simulated_ops_auto_allowed_false(self):
        out = self._run()
        for op in out["simulated_operations"]:
            self.assertFalse(bool(op.get("auto_allowed")))

    def test_destructive_operations_marked(self):
        out = self._run()
        destructive = [op for op in out["simulated_operations"] if bool(op.get("destructive"))]
        self.assertTrue(len(destructive) >= 2)

    def test_required_confirmations_present(self):
        out = self._run()
        conf = out.get("required_confirmations") or []
        self.assertIn("CONFIRM_TARGET_DEVICE", conf)
        self.assertIn("CONFIRM_DATA_LOSS", conf)
        self.assertIn("CONFIRM_IMAGE_SOURCE", conf)
        self.assertIn("CONFIRM_NO_WINDOWS_DUALBOOT", conf)
        self.assertIn("CONFIRM_FINAL_DEPLOY_WRITE", conf)

    def test_no_write_execute_route(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        resp = c.post("/api/deploy/write/execute", json={})
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
