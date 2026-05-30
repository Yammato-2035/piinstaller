"""Tests für /api/dev-server/* Routen."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from devserver.routers import router as dev_server_router

    _HAS_FASTAPI = True
except Exception:
    FastAPI = None
    TestClient = None
    dev_server_router = None
    _HAS_FASTAPI = False


def _make_client(storage_root: Path) -> TestClient:
    assert FastAPI is not None and TestClient is not None and dev_server_router is not None
    mini = FastAPI()
    mini.include_router(dev_server_router)
    env = {
        "SETUPHELFER_DEV_SERVER_ENABLED": "true",
        "SETUPHELFER_DEV_SERVER_MODE": "local_lab",
        "SETUPHELFER_DEV_SERVER_STORAGE_ROOT": str(storage_root),
        "SETUPHELFER_DEV_SERVER_TOKEN": "route-test-token",
        "SETUPHELFER_DEV_SERVER_ALLOW_REMOTE_SSH": "false",
    }
    patcher = patch.dict(os.environ, env, clear=False)
    patcher.start()
    return TestClient(mini)


@unittest.skipUnless(_HAS_FASTAPI, "FastAPI nicht verfuegbar")
class DevServerRoutesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.storage_root = Path(self._td.name) / "dev-server"
        self._patcher = patch.dict(
            os.environ,
            {
                "SETUPHELFER_DEV_SERVER_ENABLED": "true",
                "SETUPHELFER_DEV_SERVER_MODE": "local_lab",
                "SETUPHELFER_DEV_SERVER_STORAGE_ROOT": str(self.storage_root),
                "SETUPHELFER_DEV_SERVER_TOKEN": "route-test-token",
                "SETUPHELFER_DEV_SERVER_ALLOW_REMOTE_SSH": "false",
            },
            clear=False,
        )
        self._patcher.start()

    def tearDown(self) -> None:
        self._patcher.stop()
        self._td.cleanup()

    def test_health_endpoint(self) -> None:
        with TestClient(self._app()) as client:
            res = client.get("/api/dev-server/health")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("enabled", body)
        self.assertIn("mode", body)

    def test_nodes_endpoint_when_enabled(self) -> None:
        with TestClient(self._app()) as client:
            res = client.get("/api/dev-server/nodes")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], "DEV_SERVER_NODES_OK")

    def test_ingest_report_endpoint(self) -> None:
        with TestClient(self._app()) as client:
            res = client.post(
                "/api/dev-server/ingest/report",
                json={
                    "node": {"node_id": "route-node-1", "node_kind": "vm"},
                    "report": {"lab_mode": "local_lab", "report_type": "manual", "payload": {}},
                },
                headers={"X-Dev-Server-Token": "route-test-token"},
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], "DEV_SERVER_REPORT_ACCEPTED")

    def test_ssh_routes_blocked_when_ssh_disabled(self) -> None:
        with TestClient(self._app()) as client:
            client.post(
                "/api/dev-server/ingest/report",
                json={
                    "node": {"node_id": "ssh-node", "ssh": {"enabled": True, "host": "h", "username": "u"}},
                    "report": {"lab_mode": "local_lab", "payload": {}},
                },
                headers={"X-Dev-Server-Token": "route-test-token"},
            )
            res = client.post("/api/dev-server/nodes/ssh-node/ssh/check")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], "DEV_SERVER_SSH_ACTION_BLOCKED")

    def test_no_write_backup_restore_routes(self) -> None:
        paths = [getattr(r, "path", "") for r in dev_server_router.routes]
        self.assertTrue(any(p.endswith("/health") for p in paths))
        for p in paths:
            low = p.lower()
            for bad in ("backup", "restore", "repair", "partition", "mkfs", "deploy"):
                self.assertNotIn(bad, low)

    def test_disabled_blocks_nodes(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_DEV_SERVER_ENABLED": "false"}, clear=False):
            with TestClient(self._app()) as client:
                res = client.get("/api/dev-server/nodes")
        self.assertEqual(res.status_code, 403)

    def _app(self) -> FastAPI:
        assert FastAPI is not None and dev_server_router is not None
        mini = FastAPI()
        mini.include_router(dev_server_router)
        return mini


class DevServerRouterStaticTests(unittest.TestCase):
    @unittest.skipUnless(dev_server_router is not None, "devserver router nicht importierbar")
    def test_router_paths_registered(self) -> None:
        paths = {getattr(r, "path", "") for r in dev_server_router.routes}
        expected = {
            "/api/dev-server/health",
            "/api/dev-server/nodes",
            "/api/dev-server/ingest/report",
            "/api/dev-server/summary",
        }
        for p in expected:
            self.assertIn(p, paths)

    def test_health_logic_without_fastapi(self) -> None:
        from devserver.config import load_dev_server_config
        from devserver.storage import DevServerStorage

        with patch.dict(os.environ, {}, clear=True):
            cfg = load_dev_server_config()
            storage = DevServerStorage(cfg.storage_root)
            self.assertFalse(cfg.enabled)
            self.assertTrue(storage.storage_ok() or not cfg.enabled)


if __name__ == "__main__":
    unittest.main()
