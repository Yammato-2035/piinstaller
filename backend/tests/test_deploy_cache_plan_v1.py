"""Deploy cache plan tests (planning only, no download/write)."""

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


cache_mod = _load("deploy/cache_plan.py", "setuphelfer_deploy_cache_plan_test")
routes_mod = _load("deploy/routes.py", "setuphelfer_deploy_cache_routes_test")


def _deploy_plan(status: str = "ok") -> dict:
    return {
        "plan_status": status,
        "blocked_steps": [],
        "recommended_profile": {"code": "DEPLOY_PROFILE_MINIMAL_LINUX"},
        "hardware_summary": {"network_available": True},
    }


class TestDeployCachePlanV1(unittest.TestCase):
    def test_local_image_ok_or_review(self):
        src = {"type": "local_image", "name": "local", "checksum_required": False, "architecture": "x86_64", "status": "available"}
        plan = cache_mod.generate_deploy_cache_plan(src, _deploy_plan(), {})
        self.assertIn(plan["plan_status"], {"ok", "review_required"})
        dl = [s for s in plan["required_steps"] if s["code"] == "DEPLOY_CACHE_STEP_DOWNLOAD_IMAGE"][0]
        self.assertFalse(dl["applicable"])

    def test_remote_without_checksum_blocked(self):
        src = {"type": "remote_image", "name": "remote", "remote_url": "https://example.org/os.img", "checksum": ""}
        plan = cache_mod.generate_deploy_cache_plan(src, _deploy_plan(), {})
        self.assertEqual(plan["plan_status"], "blocked")
        self.assertIn("DEPLOY_CACHE_BLOCKED_MISSING_CHECKSUM", plan["blocked_steps"])

    def test_remote_http_blocked(self):
        src = {"type": "remote_image", "name": "remote", "remote_url": "http://example.org/os.img", "checksum": "sha256:abc"}
        plan = cache_mod.generate_deploy_cache_plan(src, _deploy_plan(), {})
        self.assertIn("DEPLOY_CACHE_BLOCKED_INSECURE_URL", plan["blocked_steps"])

    def test_remote_internal_blocked(self):
        src = {"type": "remote_image", "name": "remote", "remote_url": "https://localhost/os.img", "checksum": "sha256:abc"}
        plan = cache_mod.generate_deploy_cache_plan(src, _deploy_plan(), {})
        self.assertIn("DEPLOY_CACHE_BLOCKED_INTERNAL_URL", plan["blocked_steps"])

    def test_remote_https_checksum_review_required(self):
        src = {"type": "remote_image", "name": "remote", "remote_url": "https://example.org/os.img", "checksum": "sha256:abc"}
        plan = cache_mod.generate_deploy_cache_plan(src, _deploy_plan(), {})
        self.assertEqual(plan["plan_status"], "review_required")

    def test_required_steps_auto_allowed_false(self):
        src = {"type": "official_installer", "name": "official"}
        plan = cache_mod.generate_deploy_cache_plan(src, _deploy_plan(), {})
        self.assertTrue(all(s["auto_allowed"] is False for s in plan["required_steps"]))

    def test_no_hash_calculation(self):
        src = Path(cache_mod.__file__).read_text(encoding="utf-8")
        self.assertNotIn("hashlib", src)

    def test_no_directory_creation(self):
        src = Path(cache_mod.__file__).read_text(encoding="utf-8")
        self.assertNotIn("mkdir(", src)

    def test_no_download_route(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        resp = c.post("/api/deploy/cache/download", json={})
        self.assertEqual(resp.status_code, 404)

    def test_api_contract_stable(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        body = {
            "source": {"type": "remote_image", "name": "ubuntu", "remote_url": "https://example.org/os.img", "checksum": "sha256:abc"},
            "deploy_plan": _deploy_plan(),
            "inspect_result": {},
        }
        resp = c.post("/api/deploy/cache/plan", json=body)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("code", data)
        self.assertIn("plan", data)
        self.assertIn(data["code"], {"DEPLOY_CACHE_PLAN_OK", "DEPLOY_CACHE_PLAN_REVIEW_REQUIRED", "DEPLOY_CACHE_PLAN_BLOCKED", "DEPLOY_CACHE_PLAN_NOT_APPLICABLE"})


if __name__ == "__main__":
    unittest.main()
