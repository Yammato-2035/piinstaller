"""Deploy image inspect API contract tests."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
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


routes_mod = _load("deploy/routes.py", "setuphelfer_deploy_image_inspect_contract_routes_test")
image_mod = _load("deploy/image_inspect.py", "setuphelfer_deploy_image_inspect_contract_image_test")


class TestDeployImageInspectContractV1(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        self.client = TestClient(app)
        self._orig = list(image_mod._ALLOWED_CACHE_PREFIXES)

    def tearDown(self):
        image_mod._ALLOWED_CACHE_PREFIXES = self._orig

    def _assert_stable_top_level(self, payload: dict):
        self.assertIn("code", payload)
        self.assertIn("image", payload)
        self.assertIn("verification", payload)
        self.assertIn("compatibility", payload)
        self.assertIn("warnings", payload)
        self.assertIn("errors", payload)
        self.assertIsInstance(payload["image"], dict)
        self.assertIsInstance(payload["verification"], dict)
        self.assertIsInstance(payload["compatibility"], dict)
        self.assertIsInstance(payload["warnings"], list)
        self.assertIsInstance(payload["errors"], list)

    def test_empty_body_validation(self):
        resp = self.client.post("/api/deploy/image/inspect", json={})
        self.assertEqual(resp.status_code, 422)

    def test_missing_image_path_validation(self):
        resp = self.client.post(
            "/api/deploy/image/inspect",
            json={
                "expected_checksum": "",
                "expected_architecture": "unknown",
                "expected_type": "unknown",
            },
        )
        self.assertEqual(resp.status_code, 422)

    def test_outside_cache_blocked_stable_code(self):
        with tempfile.TemporaryDirectory() as cache_td:
            with tempfile.TemporaryDirectory() as outside_td:
                image_mod._ALLOWED_CACHE_PREFIXES = [cache_td]
                p = Path(outside_td) / "outside.img"
                p.write_bytes(b"abc")
                resp = self.client.post(
                    "/api/deploy/image/inspect",
                    json={
                        "image_path": str(p),
                        "expected_checksum": "",
                        "expected_architecture": "unknown",
                        "expected_type": "img",
                    },
                )
                self.assertEqual(resp.status_code, 200)
                payload = resp.json()
                self._assert_stable_top_level(payload)
                self.assertEqual(payload["code"], "DEPLOY_IMAGE_CACHE_PATH_BLOCKED")
                self.assertIn("DEPLOY_IMAGE_CACHE_PATH_BLOCKED", payload["errors"])

    def test_valid_cache_file_has_stable_top_level_fields(self):
        with tempfile.TemporaryDirectory() as cache_td:
            image_mod._ALLOWED_CACHE_PREFIXES = [cache_td]
            p = Path(cache_td) / "valid.img"
            p.write_bytes(b"abc")
            resp = self.client.post(
                "/api/deploy/image/inspect",
                json={
                    "image_path": str(p),
                    "expected_checksum": "",
                    "expected_architecture": "unknown",
                    "expected_type": "img",
                },
            )
            self.assertEqual(resp.status_code, 200)
            payload = resp.json()
            self._assert_stable_top_level(payload)


if __name__ == "__main__":
    unittest.main()
