"""Development Cockpit API — read-only, keine Backup-/Restore-Ausführung."""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import dev_dashboard as dd  # noqa: E402

_MANIFEST_DRIFT_NEUTRAL: dict[str, object] = {
    "workspace_manifest_path": "/tmp/manifest-ws.json",
    "runtime_manifest_path": "/tmp/manifest-rt.json",
    "manifest_available_workspace": True,
    "manifest_available_runtime": True,
    "manifest_match": True,
    "manifest_warnings": [],
}


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
            self.assertIn("deploy_drift", body)
            self.assertIn("backend_api_reachable", body.get("runtime") or {})
            for key in (
                "runtime_gate",
                "safe_test_mode",
                "package_gate",
                "tests_evidence",
                "roadmap",
                "structure_health",
                "updated_at",
            ):
                self.assertIn(key, body, msg=key)

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

    def test_safe_is_file_permission_error_returns_false(self) -> None:
        p = Path("/home/volker/piinstaller/config/version.json")

        with patch("core.deploy_manifest.os.stat", side_effect=PermissionError(13, "Permission denied")):
            self.assertFalse(dd._safe_is_file(p))

    def test_effective_workspace_root_absolute_when_is_dir_blocked(self) -> None:
        repo = Path("/opt/setuphelfer")
        target = Path("/home/user/piinstaller")

        def fake_is_dir(self: Path) -> bool:  # noqa: ANN001
            if str(self) == str(target):
                return False
            return Path.is_dir(self)

        with patch.object(Path, "is_dir", fake_is_dir):
            with patch.dict(os.environ, {"SETUPHELFER_DEV_WORKSPACE_ROOT": str(target)}, clear=False):
                got = dd._effective_workspace_root(repo)
        self.assertEqual(got, target)

    def test_deploy_drift_same_root_gray(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = dd._compute_deploy_drift(workspace_root=root, runtime_root=root)
        self.assertEqual(out["status"], "gray")
        self.assertIn("deploy_drift_same_workspace_and_runtime_root", out["warnings"])

    def test_deploy_drift_runtime_missing_dir_gray(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "ws"
            rt = Path(td) / "rt_missing"
            ws.mkdir()
            out = dd._compute_deploy_drift(workspace_root=ws, runtime_root=rt)
        self.assertEqual(out["status"], "gray")
        self.assertIn("runtime_root_not_a_directory", out.get("warnings") or [])

    @patch.object(dd, "DEPLOY_DRIFT_REL_PATHS", ("probe.txt",))
    def test_deploy_drift_green_identical_files(self) -> None:
        with patch("core.dev_dashboard.manifest_drift_for_roots", return_value=dict(_MANIFEST_DRIFT_NEUTRAL)):
            with tempfile.TemporaryDirectory() as td:
                ws = Path(td) / "w"
                rt = Path(td) / "r"
                ws.mkdir()
                rt.mkdir()
                (ws / "probe.txt").write_text("same", encoding="utf-8")
                (rt / "probe.txt").write_text("same", encoding="utf-8")
                out = dd._compute_deploy_drift(workspace_root=ws, runtime_root=rt)
        self.assertEqual(out["status"], "green")
        self.assertEqual(out["matching_files_count"], 1)
        self.assertEqual(out["differing_files_count"], 0)
        self.assertEqual(out["suggested_actions"], ["none"])

    @patch.object(dd, "DEPLOY_DRIFT_REL_PATHS", ("probe.txt",))
    def test_deploy_drift_yellow_missing_runtime_file(self) -> None:
        with patch("core.dev_dashboard.manifest_drift_for_roots", return_value=dict(_MANIFEST_DRIFT_NEUTRAL)):
            with tempfile.TemporaryDirectory() as td:
                ws = Path(td) / "w"
                rt = Path(td) / "r"
                ws.mkdir()
                rt.mkdir()
                (ws / "probe.txt").write_text("only-ws", encoding="utf-8")
                out = dd._compute_deploy_drift(workspace_root=ws, runtime_root=rt)
        self.assertEqual(out["status"], "yellow")
        self.assertEqual(out["missing_runtime_files"], ["probe.txt"])
        self.assertIn("deploy_backend_files", out["suggested_actions"])

    @patch.object(dd, "DEPLOY_DRIFT_REL_PATHS", ("packaging/helpers/probe-starter.py",))
    def test_deploy_drift_green_when_workspace_dirty_but_runtime_matches_head(self) -> None:
        with patch("core.dev_dashboard.manifest_drift_for_roots", return_value=dict(_MANIFEST_DRIFT_NEUTRAL)):
            with tempfile.TemporaryDirectory() as td:
                ws = Path(td) / "w"
                rt = Path(td) / "r"
                ws.mkdir()
                rt.mkdir()
                (ws / "packaging" / "helpers").mkdir(parents=True)
                (rt / "packaging" / "helpers").mkdir(parents=True)
                deployed = "runtime-and-head\n"
                dirty = "runtime-and-head\nlocal-only\n"
                starter = ws / "packaging" / "helpers" / "probe-starter.py"
                runtime_starter = rt / "packaging" / "helpers" / "probe-starter.py"
                starter.write_text(deployed, encoding="utf-8")
                runtime_starter.write_text(deployed, encoding="utf-8")
                subprocess.run(["git", "-C", str(ws), "init", "-q"], check=True)
                subprocess.run(["git", "-C", str(ws), "config", "user.email", "test@example.com"], check=True)
                subprocess.run(["git", "-C", str(ws), "config", "user.name", "Test"], check=True)
                subprocess.run(["git", "-C", str(ws), "add", "."], check=True)
                subprocess.run(["git", "-C", str(ws), "commit", "-qm", "head"], check=True)
                starter.write_text(dirty, encoding="utf-8")
                out = dd._compute_deploy_drift(workspace_root=ws, runtime_root=rt)
        self.assertEqual(out["status"], "green")
        self.assertEqual(out["differing_files_count"], 0)
        self.assertEqual(out["suggested_actions"], ["none"])
        rows = out.get("checked_files") or []
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].get("matches"))
        self.assertEqual(rows[0].get("reason"), "workspace_dirty_runtime_matches_head")

    @patch.object(dd, "DEPLOY_DRIFT_REL_PATHS", ("backend/probe.py",))
    def test_deploy_drift_yellow_content_mismatch(self) -> None:
        with patch("core.dev_dashboard.manifest_drift_for_roots", return_value=dict(_MANIFEST_DRIFT_NEUTRAL)):
            with tempfile.TemporaryDirectory() as td:
                ws = Path(td) / "w"
                rt = Path(td) / "r"
                ws.mkdir()
                rt.mkdir()
                (ws / "backend").mkdir()
                (rt / "backend").mkdir()
                (ws / "backend" / "probe.py").write_text("a", encoding="utf-8")
                (rt / "backend" / "probe.py").write_text("b", encoding="utf-8")
                out = dd._compute_deploy_drift(workspace_root=ws, runtime_root=rt)
        self.assertEqual(out["status"], "yellow")
        self.assertEqual(out["differing_files_count"], 1)
        self.assertIn("deploy_backend_files", out["suggested_actions"])

    @patch.object(dd, "DEPLOY_DRIFT_MAX_HASH_BYTES", 8)
    @patch.object(dd, "DEPLOY_DRIFT_REL_PATHS", ("big.bin",))
    def test_deploy_drift_large_file_uses_metadata_not_full_hash(self) -> None:
        with patch("core.dev_dashboard.manifest_drift_for_roots", return_value=dict(_MANIFEST_DRIFT_NEUTRAL)):
            with tempfile.TemporaryDirectory() as td:
                ws = Path(td) / "w"
                rt = Path(td) / "r"
                ws.mkdir()
                rt.mkdir()
                payload = b"0123456789abcdef"
                (ws / "big.bin").write_bytes(payload)
                (rt / "big.bin").write_bytes(payload)
                out = dd._compute_deploy_drift(workspace_root=ws, runtime_root=rt)
        self.assertEqual(out["status"], "green")
        self.assertEqual(out["matching_files_count"], 1)
        rows = out.get("checked_files") or []
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].get("reason"), "compared_by_size_mtime")

    @patch.object(dd, "DEPLOY_DRIFT_MAX_HASH_BYTES", 8)
    @patch.object(dd, "DEPLOY_DRIFT_REL_PATHS", ("big.bin",))
    def test_deploy_drift_large_file_same_content_different_mtime_green(self) -> None:
        with patch("core.dev_dashboard.manifest_drift_for_roots", return_value=dict(_MANIFEST_DRIFT_NEUTRAL)):
            with tempfile.TemporaryDirectory() as td:
                ws = Path(td) / "w"
                rt = Path(td) / "r"
                ws.mkdir()
                rt.mkdir()
                payload = b"0123456789abcdef"
                (ws / "big.bin").write_bytes(payload)
                (rt / "big.bin").write_bytes(payload)
                time.sleep(1.1)
                (ws / "big.bin").touch()
                out = dd._compute_deploy_drift(workspace_root=ws, runtime_root=rt)
        self.assertEqual(out["status"], "green")
        self.assertEqual(out["suggested_actions"], ["none"])
        rows = out.get("checked_files") or []
        self.assertEqual(rows[0].get("reason"), "sha256_same_content")

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
        for key in ("runtime", "workspace", "frontend", "consistency", "deploy_drift"):
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

    def test_status_includes_cockpit_sections(self):
        r = self.client.get("/api/dev-dashboard/status")
        self.assertEqual(r.status_code, 200, r.text)
        dash = r.json().get("dashboard") or {}
        self.assertIn("runtime_gate", dash)
        self.assertIn("safe_test_mode", dash)
        stm = dash.get("safe_test_mode") or {}
        self.assertIn(stm.get("mode"), ("LOCKED", "UNLOCKED"))

    def test_prompt_findings_200(self):
        r = self.client.get("/api/dev-dashboard/prompt-findings")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("findings", data)

    def test_cursor_meta_prompt_200(self):
        r = self.client.get("/api/dev-dashboard/cursor-meta-prompt")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("prompt", data)

    def test_ai_prompt_generate_requires_confirmation(self):
        r = self.client.post("/api/ai/prompt/generate", json={"provider": "manual"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json().get("error"), "confirmation_required")


class TestDevDashboardCockpit(unittest.TestCase):
    def test_runtime_gate_allows_yellow_drift_without_actionable_suggestions(self) -> None:
        from core.dev_dashboard_cockpit import build_runtime_gate

        rg = build_runtime_gate(
            consistency={"status": "green", "backend_workspace_match": True, "warnings": []},
            deploy_drift={"status": "yellow", "suggested_actions": ["none"], "manifest_match": True},
            runtime={"backend_runtime_path": "/opt/setuphelfer/backend"},
            workspace={"workspace_version": "1.7.2"},
            install_profile="opt",
            app_edition="release",
        )
        self.assertTrue(rg.get("passed"))
        self.assertEqual(rg.get("status"), "green")
        self.assertEqual(rg.get("blockers"), [])

    def test_safe_mode_locked_when_runtime_gate_fails(self) -> None:
        from core.dev_dashboard_cockpit import build_runtime_gate, build_safe_test_mode

        rg = build_runtime_gate(
            consistency={"status": "red", "backend_workspace_match": False, "warnings": []},
            deploy_drift={"status": "yellow", "suggested_actions": ["deploy_backend_files"]},
            runtime={"backend_runtime_path": "/wrong"},
            workspace={"workspace_version": "1.0.0"},
            install_profile="opt",
            app_edition="release",
        )
        stm = build_safe_test_mode(rg)
        self.assertEqual(stm["mode"], "LOCKED")
        self.assertTrue(stm["locked"])
        self.assertIn("backup", stm["blocked_operations"])

    def test_build_roadmap_missing_matrix_no_crash(self):
        from core.dev_dashboard_cockpit import build_roadmap

        with tempfile.TemporaryDirectory() as td:
            out = build_roadmap(Path(td))
        self.assertIn("tabs", out)
        self.assertFalse(out["changed_to_green"]["available"])

    def test_tests_evidence_yellow_when_only_release_gates_red(self):
        from core.dev_dashboard_cockpit import build_tests_evidence

        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            gates = repo / "docs" / "evidence" / "release-gates"
            gates.mkdir(parents=True)
            (gates / "test_inventory.json").write_text(
                json.dumps({"ampel": "gelb", "evidence_complete": True}),
                encoding="utf-8",
            )
            (gates / "current_failures.json").write_text(
                json.dumps({"ampel": "gruen", "evidence_complete": True}),
                encoding="utf-8",
            )
            (gates / "release_readiness_gate.json").write_text(
                json.dumps({"ampel": "rot", "evidence_complete": True}),
                encoding="utf-8",
            )
            (gates / "backup_restore_release_gate.json").write_text(
                json.dumps({"ampel": "rot", "evidence_complete": True}),
                encoding="utf-8",
            )
            out = build_tests_evidence(repo)
        self.assertEqual(out["status"], "yellow")

    def test_build_br001_gates_offline_primary(self):
        from core.dev_dashboard_cockpit import build_br001_gates, enrich_dashboard_cockpit

        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            gates = repo / "docs" / "evidence" / "release-gates"
            gates.mkdir(parents=True)
            (gates / "backup_restore_release_gate.json").write_text(
                json.dumps(
                    {
                        "br001_gates": {
                            "live": {"id": "BR-001-LIVE", "release_gate": False, "ampel": "rot", "role": "experimental"},
                            "offline": {"id": "BR-001-OFFLINE", "release_gate": True, "ampel": "rot", "role": "release_gate"},
                        },
                        "release_gate_primary": "BR-001-OFFLINE",
                    }
                ),
                encoding="utf-8",
            )
            g = build_br001_gates(repo)
            self.assertFalse(g["live"]["release_gate"])
            self.assertTrue(g["offline"]["release_gate"])
            self.assertEqual(g["primary_release_gate"], "BR-001-OFFLINE")
            body: dict = {"consistency": {}, "deploy_drift": {}, "runtime": {}, "workspace": {}}
            enrich_dashboard_cockpit(body, repo_root=repo)
            self.assertIn("br001_gates", body)
            self.assertIn("rescue_stick_board", body)
            self.assertEqual(body.get("release_gate_primary"), "BR-001-OFFLINE")


if __name__ == "__main__":
    unittest.main()
