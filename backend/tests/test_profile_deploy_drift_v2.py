"""Profile-aware deploy drift v2."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.profile_deploy_manifest import enrich_deploy_drift_profile_aware


class ProfileDeployDriftV2Tests(unittest.TestCase):
    def test_release_forbidden_fleet_dir_red(self) -> None:
        with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as rt:
            ws_p, rt_p = Path(ws), Path(rt)
            (rt_p / "backend" / "fleet").mkdir(parents=True)
            base = {"status": "green", "suggested_actions": ["none"], "manifest_match": True}
            with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=True):
                out = enrich_deploy_drift_profile_aware(
                    base,
                    workspace_root=ws_p,
                    runtime_root=rt_p,
                    route_paths=["/api/version"],
                )
            self.assertTrue(out.get("profile_aware"))
            self.assertEqual(out["status"], "red")
            self.assertIn("backend/fleet", out.get("forbidden_paths_present") or [])

    def test_release_no_dev_routes_green(self) -> None:
        with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as rt:
            ws_p, rt_p = Path(ws), Path(rt)
            (rt_p / "backend").mkdir(parents=True, exist_ok=True)
            (rt_p / "backend" / "app.py").write_text("#", encoding="utf-8")
            (rt_p / "config").mkdir(parents=True, exist_ok=True)
            (rt_p / "config" / "version.json").write_text("{}", encoding="utf-8")
            base = {"status": "green", "suggested_actions": ["none"], "manifest_match": True}
            with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=True):
                out = enrich_deploy_drift_profile_aware(
                    base,
                    workspace_root=ws_p,
                    runtime_root=rt_p,
                    route_paths=["/api/version"],
                )
            self.assertEqual(out["status"], "green")
            self.assertEqual(out.get("forbidden_api_paths_visible") or [], [])

    def test_release_dev_dashboard_registered_allowed_with_developer_capability(self) -> None:
        with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as rt:
            ws_p, rt_p = Path(ws), Path(rt)
            (rt_p / "backend").mkdir(parents=True, exist_ok=True)
            (rt_p / "backend" / "app.py").write_text("#", encoding="utf-8")
            (rt_p / "config").mkdir(parents=True, exist_ok=True)
            (rt_p / "config" / "version.json").write_text("{}", encoding="utf-8")
            base = {"status": "green", "suggested_actions": ["none"], "manifest_match": True}
            with patch.dict(
                os.environ,
                {
                    "SETUPHELFER_INSTALL_PROFILE": "release",
                    "DCC_DEVELOPER_ENABLED": "1",
                    "DCC_DEVELOPER_TOKEN": "dev-host-token",
                },
                clear=True,
            ):
                out = enrich_deploy_drift_profile_aware(
                    base,
                    workspace_root=ws_p,
                    runtime_root=rt_p,
                    route_paths=["/api/version", "/api/dev-dashboard/status"],
                )
            self.assertEqual(out["status"], "green")
            self.assertEqual(out.get("forbidden_api_paths_visible") or [], [])
            cap_exp = out.get("developer_capability_exposure") or {}
            self.assertEqual(cap_exp.get("status"), "allowed")
            self.assertIn("/api/dev-dashboard", cap_exp.get("exempt_api_prefixes") or [])

    def test_release_dev_server_registered_allowed_with_developer_capability(self) -> None:
        with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as rt:
            ws_p, rt_p = Path(ws), Path(rt)
            (rt_p / "backend").mkdir(parents=True, exist_ok=True)
            (rt_p / "backend" / "app.py").write_text("#", encoding="utf-8")
            (rt_p / "config").mkdir(parents=True, exist_ok=True)
            (rt_p / "config" / "version.json").write_text("{}", encoding="utf-8")
            base = {"status": "green", "suggested_actions": ["none"], "manifest_match": True}
            with patch.dict(
                os.environ,
                {
                    "SETUPHELFER_INSTALL_PROFILE": "release",
                    "DCC_DEVELOPER_ENABLED": "1",
                    "DCC_DEVELOPER_TOKEN": "dev-host-token",
                },
                clear=True,
            ):
                out = enrich_deploy_drift_profile_aware(
                    base,
                    workspace_root=ws_p,
                    runtime_root=rt_p,
                    route_paths=["/api/dev-server/health"],
                )
            self.assertEqual(out["status"], "green")
            self.assertEqual(out.get("forbidden_api_paths_visible") or [], [])
            cap_exp = out.get("developer_capability_exposure") or {}
            self.assertIn("/api/dev-server", cap_exp.get("exempt_api_prefixes") or [])

    def test_release_dev_dashboard_registered_red_without_developer_capability(self) -> None:
        with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as rt:
            ws_p, rt_p = Path(ws), Path(rt)
            base = {"status": "green", "suggested_actions": ["none"], "manifest_match": True}
            with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=True):
                out = enrich_deploy_drift_profile_aware(
                    base,
                    workspace_root=ws_p,
                    runtime_root=rt_p,
                    route_paths=["/api/dev-dashboard/status"],
                )
            self.assertEqual(out["status"], "red")
            self.assertIn("/api/dev-dashboard", out.get("forbidden_api_paths_visible") or [])

    def test_local_lab_required_api_missing_yellow(self) -> None:
        with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as rt:
            ws_p, rt_p = Path(ws), Path(rt)
            base = {"status": "green", "suggested_actions": ["none"], "manifest_match": True}
            with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "local_lab"}, clear=True):
                out = enrich_deploy_drift_profile_aware(
                    base,
                    workspace_root=ws_p,
                    runtime_root=rt_p,
                    route_paths=["/api/version"],
                )
            self.assertIn(out["status"], ("yellow", "red"))
            self.assertTrue(out.get("required_api_paths_missing"))

    def test_public_exposure_bind_red(self) -> None:
        with tempfile.TemporaryDirectory() as ws:
            ws_p = Path(ws)
            base = {"status": "green", "suggested_actions": ["none"]}
            with patch.dict(
                os.environ,
                {"SETUPHELFER_INSTALL_PROFILE": "local_lab"},
                clear=True,
            ):
                out = enrich_deploy_drift_profile_aware(
                    base,
                    workspace_root=ws_p,
                    runtime_root=None,
                    route_paths=[],
                    bind_address="0.0.0.0",
                )
            self.assertEqual(out.get("public_exposure_status"), "red")
            self.assertEqual(out["status"], "red")


if __name__ == "__main__":
    unittest.main()
