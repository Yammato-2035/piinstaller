"""Deploy source registry metadata and compatibility tests."""

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


reg_mod = _load("deploy/source_registry.py", "setuphelfer_deploy_source_registry_test")
routes_mod = _load("deploy/routes.py", "setuphelfer_deploy_source_routes_test")


def _inspect(machine: str = "x86_64") -> dict:
    return {"system": {"machine": machine}}


def _plan(rec: str = "DEPLOY_PROFILE_MINIMAL_LINUX") -> dict:
    return {"recommended_profile": {"code": rec}, "hardware_summary": {"network_available": True}}


class TestDeploySourceRegistryV1(unittest.TestCase):
    def test_registry_has_sources(self):
        r = reg_mod.get_deploy_source_registry()
        self.assertEqual(r.get("registry_version"), 1)
        self.assertTrue(isinstance(r.get("sources"), list) and len(r.get("sources")) >= 6)

    def test_rpi_os_not_compatible_with_x86(self):
        source = next(s for s in reg_mod.get_deploy_source_registry()["sources"] if s["source_id"] == "SRC_RPI_OS_LITE")
        compat = reg_mod.evaluate_source_compatibility(source, _inspect("x86_64"), _plan())
        self.assertFalse(compat["compatible"])

    def test_ubuntu_arm64_compatible_with_pi_arm64(self):
        source = next(s for s in reg_mod.get_deploy_source_registry()["sources"] if s["source_id"] == "SRC_UBUNTU_SERVER_LTS")
        compat = reg_mod.evaluate_source_compatibility(source, _inspect("arm64"), _plan())
        self.assertTrue(compat["compatible"])

    def test_experimental_high_risk(self):
        source = next(s for s in reg_mod.get_deploy_source_registry()["sources"] if s["source_id"] == "SRC_EXPERIMENTAL_GENERIC_LINUX")
        compat = reg_mod.evaluate_source_compatibility(source, _inspect("x86_64"), _plan("DEPLOY_PROFILE_EXPERIMENTAL"))
        self.assertEqual(compat["risk_level"], "high")

    def test_blocked_source_incompatible(self):
        source = {"status": "blocked", "platforms": ["linux-x86_64"], "supported_profiles": ["DEPLOY_PROFILE_MINIMAL_LINUX"], "risk_level": "medium"}
        compat = reg_mod.evaluate_source_compatibility(source, _inspect("x86_64"), _plan())
        self.assertFalse(compat["compatible"])

    def test_local_image_valid(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.img"
            p.write_text("x", encoding="utf-8")
            out = reg_mod.validate_local_image_entry({"local_path": str(p)})
            self.assertEqual(out["code"], "DEPLOY_SOURCE_LOCAL_IMAGE_VALID")

    def test_local_image_missing(self):
        out = reg_mod.validate_local_image_entry({"local_path": "/tmp/definitely-missing.img"})
        self.assertEqual(out["code"], "DEPLOY_SOURCE_LOCAL_IMAGE_MISSING")

    def test_remote_metadata_valid(self):
        out = reg_mod.validate_remote_image_metadata({"remote_url": "https://example.org/os.img", "checksum": "sha256:abc"})
        self.assertEqual(out["code"], "DEPLOY_SOURCE_REMOTE_METADATA_VALID")

    def test_remote_metadata_invalid(self):
        out = reg_mod.validate_remote_image_metadata({"remote_url": "http://example.org/os.img", "checksum": ""})
        self.assertEqual(out["code"], "DEPLOY_SOURCE_REMOTE_METADATA_INVALID")

    def test_localhost_internal_url_blocked(self):
        out = reg_mod.validate_remote_image_metadata({"remote_url": "https://localhost/os.img", "checksum": "sha256:abc"})
        self.assertEqual(out["code"], "DEPLOY_SOURCE_REMOTE_METADATA_INVALID")

    def test_no_download_route(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        resp = c.post("/api/deploy/source/download", json={})
        self.assertEqual(resp.status_code, 404)

    def test_no_install_route(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        resp = c.post("/api/deploy/install", json={})
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
