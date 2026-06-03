from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.runtime_ports import load_runtime_ports_registry, version_api_port_fields


class RuntimePortsTests(unittest.TestCase):
    def test_embedded_fallback_has_backend_8000(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("core.runtime_ports._repo_candidates", return_value=[repo]):
                reg = load_runtime_ports_registry(repo_root=repo)
        self.assertEqual(reg["ports"]["backend_api"]["port"], 8000)
        self.assertEqual(reg["ports"]["frontend_ui"]["port"], 3001)
        self.assertEqual(reg["ports"]["nginx_default"]["port"], 8080)
        self.assertEqual(reg["ports"]["qemu_lab_proxy_host"]["port"], 8001)
        self.assertTrue(reg.get("port_registry_fallback"))

    def test_loads_json_from_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cfg = repo / "config"
            cfg.mkdir(parents=True)
            payload = {
                "version": 1,
                "ports": {"backend_api": {"port": 8000, "base_url": "http://127.0.0.1:8000"}},
                "profiles": {},
                "canonical_urls": {},
            }
            (cfg / "runtime_ports.json").write_text(json.dumps(payload), encoding="utf-8")
            reg = load_runtime_ports_registry(repo_root=repo)
        self.assertFalse(reg.get("port_registry_fallback"))
        self.assertEqual(reg["ports"]["backend_api"]["port"], 8000)

    def test_version_fields_release_profile(self) -> None:
        fields = version_api_port_fields(install_profile="release", dev_control_enabled=False)
        self.assertEqual(fields["runtime_ports"]["backend_api"]["port"], 8000)
        self.assertEqual(fields["canonical_urls"]["dcc"], "http://127.0.0.1:3001/?window=cockpit")
        self.assertFalse(fields["profile_capabilities"]["dev_control_enabled"])

    def test_version_fields_local_lab(self) -> None:
        fields = version_api_port_fields(install_profile="local_lab", dev_control_enabled=True)
        self.assertTrue(fields["profile_capabilities"]["dev_control_enabled"])

    def test_api_version_endpoint_includes_runtime_ports(self) -> None:
        from fastapi.testclient import TestClient

        import app as app_module

        client = TestClient(app_module.app)
        r = client.get("/api/version")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["runtime_ports"]["backend_api"]["port"], 8000)
        self.assertEqual(data["runtime_ports"]["frontend_ui"]["port"], 3001)
        self.assertIn("port_registry_source", data)


if __name__ == "__main__":
    unittest.main()
