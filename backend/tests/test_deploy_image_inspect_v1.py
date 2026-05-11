"""Deploy image inspect read-only tests."""

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


mod = _load("deploy/image_inspect.py", "setuphelfer_deploy_image_inspect_test")
routes_mod = _load("deploy/routes.py", "setuphelfer_deploy_image_inspect_routes_test")


class TestDeployImageInspectV1(unittest.TestCase):
    def setUp(self):
        self._orig = list(mod._ALLOWED_CACHE_PREFIXES)

    def tearDown(self):
        mod._ALLOWED_CACHE_PREFIXES = self._orig

    def _run(self, **kwargs):
        req = {
            "image_path": kwargs.get("image_path", ""),
            "expected_checksum": kwargs.get("expected_checksum", ""),
            "expected_architecture": kwargs.get("expected_architecture", "unknown"),
            "expected_type": kwargs.get("expected_type", "unknown"),
        }
        return mod.inspect_deploy_image(req)

    def test_file_missing(self):
        with tempfile.TemporaryDirectory() as td:
            mod._ALLOWED_CACHE_PREFIXES = [td]
            out = self._run(image_path=str(Path(td) / "missing.img"))
            self.assertEqual(out["code"], "DEPLOY_IMAGE_INSPECT_FAILED")
            self.assertIn("DEPLOY_IMAGE_NOT_FOUND", out["errors"])

    def test_directory_instead_of_file(self):
        with tempfile.TemporaryDirectory() as td:
            mod._ALLOWED_CACHE_PREFIXES = [td]
            out = self._run(image_path=td)
            self.assertIn("DEPLOY_IMAGE_NOT_REGULAR_FILE", out["errors"])

    def test_invalid_extension(self):
        with tempfile.TemporaryDirectory() as td:
            mod._ALLOWED_CACHE_PREFIXES = [td]
            p = Path(td) / "a.txt"
            p.write_text("x", encoding="utf-8")
            out = self._run(image_path=str(p))
            self.assertIn("DEPLOY_IMAGE_EXTENSION_INVALID", out["errors"])

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as td:
            mod._ALLOWED_CACHE_PREFIXES = [td]
            p = Path(td) / "a.img"
            p.write_bytes(b"")
            out = self._run(image_path=str(p))
            self.assertIn("DEPLOY_IMAGE_EMPTY", out["errors"])

    def test_valid_without_checksum_warns_arch(self):
        with tempfile.TemporaryDirectory() as td:
            mod._ALLOWED_CACHE_PREFIXES = [td]
            p = Path(td) / "a.img"
            p.write_text("abc", encoding="utf-8")
            out = self._run(image_path=str(p), expected_type="img")
            self.assertIn(out["code"], {"DEPLOY_IMAGE_INSPECT_OK", "DEPLOY_IMAGE_INSPECT_WARNING"})
            self.assertIn("DEPLOY_IMAGE_ARCHITECTURE_UNVERIFIED", out["warnings"])

    def test_valid_with_checksum_ok(self):
        with tempfile.TemporaryDirectory() as td:
            mod._ALLOWED_CACHE_PREFIXES = [td]
            p = Path(td) / "a.img"
            p.write_text("abc", encoding="utf-8")
            out = self._run(
                image_path=str(p),
                expected_type="img",
                expected_checksum="sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )
            self.assertTrue(out["verification"]["checksum_ok"])
            self.assertEqual(out["verification"]["code"], "DEPLOY_IMAGE_CHECKSUM_OK")

    def test_wrong_checksum(self):
        with tempfile.TemporaryDirectory() as td:
            mod._ALLOWED_CACHE_PREFIXES = [td]
            p = Path(td) / "a.img"
            p.write_text("abc", encoding="utf-8")
            out = self._run(image_path=str(p), expected_checksum="sha256:deadbeef")
            self.assertEqual(out["code"], "DEPLOY_IMAGE_INSPECT_FAILED")
            self.assertIn("DEPLOY_IMAGE_CHECKSUM_FAILED", out["errors"])

    def test_outside_cache_path_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            with tempfile.TemporaryDirectory() as outside:
                mod._ALLOWED_CACHE_PREFIXES = [td]
                p = Path(outside) / "a.img"
                p.write_text("abc", encoding="utf-8")
                out = self._run(image_path=str(p))
                self.assertIn("DEPLOY_IMAGE_CACHE_PATH_BLOCKED", out["errors"])

    def test_no_mount_or_install_route(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        self.assertEqual(c.post("/api/deploy/image/mount", json={}).status_code, 404)
        self.assertEqual(c.post("/api/deploy/image/install", json={}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
