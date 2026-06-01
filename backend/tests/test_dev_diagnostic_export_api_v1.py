"""API tests for /api/dev-diagnostics/* (no QEMU)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from dev_diagnostics.routers import router as dev_diag_router

    HAS_TEST_CLIENT = True
except ImportError:
    HAS_TEST_CLIENT = False
    FastAPI = None
    TestClient = None
    dev_diag_router = None

from core.fleet_session_state import FORBIDDEN_ROUTE_FRAGMENTS, create_fleet_session


def _mini_client() -> TestClient:
    assert FastAPI is not None and TestClient is not None and dev_diag_router is not None
    mini = FastAPI()
    mini.include_router(dev_diag_router)
    return TestClient(mini)


@unittest.skipUnless(HAS_TEST_CLIENT, "fastapi TestClient not installed")
class DevDiagnosticExportApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.repo = Path(self._td.name)
        self._env = patch.dict(
            os.environ,
            {
                "SETUPHELFER_FLEET_SESSIONS_ENABLED": "true",
                "SETUPHELFER_DEV_DIAGNOSTICS_ENABLED": "true",
                "PI_INSTALLER_DEV": "1",
            },
            clear=False,
        )
        self._env.start()
        self._patches = [
            patch("core.dev_diagnostic_export._repo_root", return_value=self.repo),
            patch("core.fleet_session_state._repo_root", return_value=self.repo),
        ]
        for p in self._patches:
            p.start()
        self.client = _mini_client()
        run_id = "api_qemu_run_1"
        run_dir = self.repo / "docs/evidence/runtime-results/rescue/qemu" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "qemu_autopilot_result.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "status": "failed",
                    "qemu_exit_code": 124,
                    "dev_server_report_new": False,
                    "guest_smoke_from_serial": None,
                }
            ),
            encoding="utf-8",
        )
        (run_dir / "qemu-serial.log").write_text("", encoding="utf-8")
        create_fleet_session({"run_id": run_id}, repo_root=self.repo)
        self.run_id = run_id
        self.session_id = f"fleet-{run_id}"

    def tearDown(self) -> None:
        for p in self._patches:
            p.stop()
        self._env.stop()
        self._td.cleanup()

    def test_qemu_export_ok(self) -> None:
        r = self.client.get(f"/api/dev-diagnostics/qemu-smokes/{self.run_id}/export")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn(body["code"], ("DEV_DIAGNOSTIC_EXPORT_OK", "DEV_DIAGNOSTIC_REDACTED"))
        exp = body["export"]
        self.assertEqual(exp["classification"]["primary"], "serial_empty_boot_unknown")
        self.assertFalse(exp["devserver_ingest"]["report_new"])
        self.assertFalse(exp["devserver_ingest"]["guest_found"])
        self.assertEqual(exp["qemu_smoke"]["serial_size_bytes"], 0)

    def test_fleet_session_export_ok(self) -> None:
        r = self.client.get(f"/api/dev-diagnostics/fleet-sessions/{self.session_id}/export")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["export"]["run_id"], self.run_id)

    def test_markdown_endpoint(self) -> None:
        r = self.client.get(f"/api/dev-diagnostics/qemu-smokes/{self.run_id}/markdown")
        self.assertEqual(r.status_code, 200)
        self.assertIn(self.run_id, r.text)
        self.assertIn("serial_empty_boot_unknown", r.text)

    def test_evidence_index(self) -> None:
        r = self.client.get(f"/api/dev-diagnostics/qemu-smokes/{self.run_id}/evidence-index")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["code"], "DEV_DIAGNOSTIC_EVIDENCE_INDEX_OK")

    def test_unredacted_without_confirm_blocked(self) -> None:
        r = self.client.get(
            f"/api/dev-diagnostics/qemu-smokes/{self.run_id}/export?redacted=false"
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["code"], "DEV_DIAGNOSTIC_BLOCKED_UNREDACTED_NOT_CONFIRMED")

    def test_invalid_run_id_rejected(self) -> None:
        r = self.client.get("/api/dev-diagnostics/qemu-smokes/bad%2F..%2Fid/export")
        self.assertEqual(r.status_code, 404)

    def test_missing_run_export_review(self) -> None:
        r = self.client.get("/api/dev-diagnostics/qemu-smokes/qemu_missing_run_xyz/export")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["export"]["classification"]["primary"], "serial_empty_boot_unknown")

    def test_no_control_routes(self) -> None:
        assert dev_diag_router is not None
        paths = [getattr(r, "path", "") for r in dev_diag_router.routes]
        for p in paths:
            low = p.lower()
            for frag in FORBIDDEN_ROUTE_FRAGMENTS:
                self.assertNotIn(frag, low, msg=f"forbidden {frag} in {p}")
        methods = set()
        for r in dev_diag_router.routes:
            for m in getattr(r, "methods", []) or []:
                methods.add(m.upper())
        self.assertFalse(methods & {"POST", "PUT", "PATCH", "DELETE"})


if __name__ == "__main__":
    unittest.main()
