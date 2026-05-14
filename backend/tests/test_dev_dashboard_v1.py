"""Development Cockpit API — read-only, keine Backup-/Restore-Ausführung."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import dev_dashboard as dd  # noqa: E402


class TestDevDashboardCore(unittest.TestCase):
    def test_build_dashboard_status_empty_repo_no_crash(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            body = dd.build_dashboard_status(repo_root=tmp, running_jobs=[], package_activity=[])
            self.assertIn("generated_at", body)
            self.assertTrue(body.get("backend_running"))
            self.assertIsInstance(body.get("warnings"), list)
            self.assertIsInstance(body.get("errors"), list)
            self.assertEqual(body.get("release_gate_status"), "unknown")
            self.assertIn("runtime", body)
            self.assertIn("workspace", body)
            self.assertIn("frontend", body)
            self.assertIn("consistency", body)
            self.assertIn("backend_api_reachable", body.get("runtime") or {})

    def test_build_modules_list_missing_dir(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            out = dd.build_modules_list(repo_root=tmp)
            self.assertEqual(out.get("status"), "success")
            self.assertEqual(out.get("modules"), [])
            self.assertTrue(any("modules_dir_missing" in w for w in (out.get("warnings") or [])))

    def test_build_module_detail_not_found(self):
        out = dd.build_module_detail("__no_such_module__xyz__")
        self.assertEqual(out.get("status"), "error")
        self.assertIsNone(out.get("module"))

    def test_build_evidence_index_tolerates_missing_docs_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            out = dd.build_evidence_index(repo_root=tmp, max_files=10)
            self.assertEqual(out.get("status"), "success")
            self.assertIn("buckets", out)
            warns = out.get("warnings") or []
            self.assertIn("docs_evidence_missing", warns)

    def test_module_json_invalid_traffic_becomes_gray(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mod_dir = root / "docs" / "dev-dashboard" / "modules"
            mod_dir.mkdir(parents=True)
            raw = {
                "id": "z-invalid-traffic",
                "title": "T",
                "area": "backup",
                "status": "orange",
                "last_updated": "2026-01-01",
            }
            (mod_dir / "z-invalid-traffic.json").write_text(json.dumps(raw), encoding="utf-8")
            out = dd.build_modules_list(repo_root=root)
            self.assertEqual(out.get("status"), "success")
            mods = out.get("modules") or []
            self.assertEqual(len(mods), 1)
            self.assertEqual(mods[0].get("status"), "gray")
            warns = out.get("warnings") or []
            self.assertTrue(any("invalid_traffic" in w for w in warns))

    def test_action_placeholders(self):
        r1 = dd.action_placeholder_response("restart-backend")
        self.assertEqual(r1.get("result"), "not_implemented_safe")
        self.assertTrue(r1.get("confirm_required"))
        self.assertEqual(r1.get("message_key"), "devDashboard.actions.restartBackendNotImplemented")

        r2 = dd.action_placeholder_response("start-backup")
        self.assertEqual(r2.get("result"), "use_existing_backup_api")
        self.assertTrue(r2.get("confirm_required"))
        self.assertEqual(r2.get("message_key"), "devDashboard.actions.startBackupUseExistingApi")

        r3 = dd.action_placeholder_response("destroy-world")
        self.assertEqual(r3.get("status"), "error")
        self.assertEqual(r3.get("result"), "unknown_action")

    @patch("core.versioning.load_project_version")
    def test_consistency_frontend_build_outdated_yellow(self, lp: MagicMock) -> None:
        lp.return_value = SimpleNamespace(project_version="1.7.1", release_stage="internal_testing", version_track="t")
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "docs" / "evidence" / "release-gates").mkdir(parents=True)
            (tmp / "docs" / "evidence" / "release-gates" / "backup_restore_release_gate.json").write_text(
                '{"ampel":"gelb"}', encoding="utf-8"
            )
            (tmp / "config").mkdir(parents=True)
            (tmp / "config" / "version.json").write_text(
                json.dumps(
                    {
                        "project_version": "1.7.1",
                        "release_stage": "internal_testing",
                        "version_source_of_truth": True,
                        "version_track": "t",
                    }
                ),
                encoding="utf-8",
            )
            body = dd.build_dashboard_status(
                repo_root=tmp,
                running_jobs=[],
                package_activity=[],
                frontend_build_version="1.5.0.0",
                frontend_runtime_source="build",
            )
        self.assertEqual(body.get("consistency", {}).get("status"), "yellow")
        self.assertIn("frontend_build_outdated", body.get("consistency", {}).get("warnings") or [])

    @patch("core.versioning.load_project_version", side_effect=FileNotFoundError("no version"))
    def test_consistency_red_when_runtime_version_unreadable(self, _lp: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "docs" / "evidence" / "release-gates").mkdir(parents=True)
            (tmp / "docs" / "evidence" / "release-gates" / "backup_restore_release_gate.json").write_text(
                '{"ampel":"gelb"}', encoding="utf-8"
            )
            body = dd.build_dashboard_status(repo_root=tmp, running_jobs=[], package_activity=[])
        self.assertEqual(body.get("consistency", {}).get("status"), "red")
        self.assertIn("version_unknown", body.get("consistency", {}).get("warnings") or [])


try:
    from fastapi.testclient import TestClient
    from app import app

    _HAS_APP = True
except Exception:
    _HAS_APP = False
    TestClient = None
    app = None


@unittest.skipUnless(_HAS_APP, "FastAPI TestClient oder app nicht verfuegbar")
class TestDevDashboardApiV1(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, base_url="http://localhost")

    def test_status_200(self):
        r = self.client.get("/api/dev-dashboard/status")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("dashboard", data)
        dash = data.get("dashboard") or {}
        for key in ("runtime", "workspace", "frontend", "consistency"):
            self.assertIn(key, dash, msg=key)

    def test_status_accepts_frontend_query_params(self):
        r = self.client.get("/api/dev-dashboard/status?frontend_build_version=0.0.1-test&frontend_runtime_source=build")
        self.assertEqual(r.status_code, 200, r.text)
        fe = (r.json().get("dashboard") or {}).get("frontend") or {}
        self.assertEqual(fe.get("frontend_build_version"), "0.0.1-test")
        self.assertEqual(fe.get("frontend_runtime_source"), "build")

    def test_modules_includes_backup_restore_with_children(self):
        r = self.client.get("/api/dev-dashboard/modules")
        self.assertEqual(r.status_code, 200, r.text)
        mods = r.json().get("modules") or []
        br = next((m for m in mods if m.get("id") == "backup-restore"), None)
        self.assertIsNotNone(br)
        children = br.get("children") or []
        self.assertGreaterEqual(len(children), 1)

    def test_module_detail_backup_restore(self):
        r = self.client.get("/api/dev-dashboard/modules/backup-restore")
        self.assertEqual(r.status_code, 200, r.text)
        payload = r.json()
        self.assertEqual(payload.get("status"), "success")
        mod = payload.get("module") or {}
        self.assertEqual(mod.get("id"), "backup-restore")
        self.assertGreaterEqual(len(mod.get("children") or []), 1)

    def test_evidence_index_200(self):
        r = self.client.get("/api/dev-dashboard/evidence-index")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json().get("status"), "success")

    def test_post_restart_placeholder(self):
        r = self.client.post("/api/dev-dashboard/actions/restart-backend", json={})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json().get("result"), "not_implemented_safe")

    def test_post_start_backup_placeholder(self):
        r = self.client.post("/api/dev-dashboard/actions/start-backup", json={})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json().get("result"), "use_existing_backup_api")


if __name__ == "__main__":
    unittest.main()
