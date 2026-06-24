from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import project_overview_dashboard_state as pov  # noqa: E402


class ProjectOverviewDashboardStateTests(unittest.TestCase):
    def _write(self, repo: Path, rel: str, content: str) -> None:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _complete_docs(self, repo: Path) -> None:
        self._write(repo, "docs/roadmap/MASTER_ROADMAP_2026_2030.md", "# Master Roadmap\n")
        self._write(
            repo,
            "docs/roadmap/master_roadmap_status.json",
            '{\n  "overall_status": "green",\n  "summary": "Roadmap vorhanden."\n}\n',
        )
        self._write(repo, "docs/architecture/MONOLITH_BOUNDARY_MAP.md", "# Monolith Boundary Map\n")
        self._write(
            repo,
            "docs/architecture/monolith_boundary_status.json",
            '{\n  "overall_status": "yellow",\n  "summary": "Monolith bleibt teilweise gekoppelt."\n}\n',
        )
        self._write(repo, "docs/evidence/TEST_FAILURE_REGISTER.md", "# Test Failure Register\n")
        self._write(
            repo,
            "docs/evidence/test_failure_register.json",
            '{\n  "summary": "Register vorhanden.",\n  "open_failures_status": "red"\n}\n',
        )
        self._write(repo, "docs/evidence/EVIDENCE_INDEX.md", "# Evidence Index\n")
        self._write(
            repo,
            "docs/evidence/evidence_index.json",
            '{\n  "summary": "Index vorhanden."\n}\n',
        )

    def _deploy(self, *, exit_code: int, last_job_status: str = "success", summary: str = "ok") -> dict:
        return {
            "status": "success" if exit_code == 0 and last_job_status == "success" else "blocked",
            "runtime_gate": {"exit_code": exit_code, "status": "green" if exit_code == 0 else "red", "summary": summary},
            "last_job": {"status": last_job_status, "summary": summary, "deploy_exit_code": 0 if last_job_status == "success" else 1},
        }

    def _update(self, *, status: str = "ok", deploy_required: bool = False) -> dict:
        return {
            "status": status,
            "deploy_required": deploy_required,
            "automatic_update_allowed": False,
            "package_manager_update_allowed": False,
        }

    def _rescue(self, *, dpkg: str = "pre_chroot_ok", stale_sudo: bool = False, status: str = "yellow") -> dict:
        return {
            "status": status,
            "summary": "Rescue summary",
            "path_status": "ok",
            "temp_runtime_bundle": {"status": "ok"},
            "build_tree": {"validator_status": "ok"},
            "stale_state": {"needs_sudo_clean": stale_sudo, "present": stale_sudo},
            "dpkg_preflight": {"status": dpkg, "summary": "DPKG summary"},
            "iso_build": {"status": "not_started", "iso_found": False},
            "usb_write": {"allowed": False, "status": "blocked"},
            "forbidden_actions": {"usb_write_allowed": False},
            "next_operator_action": {"type": "operator_sudo_required"},
        }

    def _packaging(self, *, status: str = "yellow") -> dict:
        return {
            "status": status,
            "summary": "Packaging summary",
            "install_test_passed": False,
        }

    def test_runtime_can_be_green_while_rescue_is_only_yellow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._complete_docs(repo)
            with (
                patch.object(pov, "build_deploy_job_state", return_value=self._deploy(exit_code=0)),
                patch.object(pov, "build_update_status", return_value=self._update(status="ok", deploy_required=False)),
                patch.object(pov, "build_rescue_iso_dashboard_state", return_value=self._rescue(status="yellow")),
                patch.object(pov, "build_packaging_readiness_state", return_value=self._packaging()),
            ):
                state = pov.build_project_overview_dashboard_state(repo_root=repo)
        self.assertEqual(state["runtime"]["overall_status"], "green")
        self.assertEqual(state["rescue_iso"]["overall_status"], "yellow")

    def test_deploy_helper_success_sets_section_green(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._complete_docs(repo)
            with (
                patch.object(pov, "build_deploy_job_state", return_value=self._deploy(exit_code=0, last_job_status="success")),
                patch.object(pov, "build_update_status", return_value=self._update()),
                patch.object(pov, "build_rescue_iso_dashboard_state", return_value=self._rescue()),
                patch.object(pov, "build_packaging_readiness_state", return_value=self._packaging()),
            ):
                state = pov.build_project_overview_dashboard_state(repo_root=repo)
        self.assertEqual(state["deploy_helper"]["overall_status"], "green")

    def test_update_ok_without_deploy_required_is_green(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._complete_docs(repo)
            with (
                patch.object(pov, "build_deploy_job_state", return_value=self._deploy(exit_code=0)),
                patch.object(pov, "build_update_status", return_value=self._update(status="ok", deploy_required=False)),
                patch.object(pov, "build_rescue_iso_dashboard_state", return_value=self._rescue()),
                patch.object(pov, "build_packaging_readiness_state", return_value=self._packaging()),
            ):
                state = pov.build_project_overview_dashboard_state(repo_root=repo)
        self.assertEqual(state["update_check"]["overall_status"], "green")

    def test_rescue_prebuild_ready_but_iso_missing_stays_yellow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._complete_docs(repo)
            with (
                patch.object(pov, "build_deploy_job_state", return_value=self._deploy(exit_code=0)),
                patch.object(pov, "build_update_status", return_value=self._update()),
                patch.object(pov, "build_rescue_iso_dashboard_state", return_value=self._rescue(dpkg="ok", stale_sudo=False, status="green")),
                patch.object(pov, "build_packaging_readiness_state", return_value=self._packaging()),
            ):
                state = pov.build_project_overview_dashboard_state(repo_root=repo)
        self.assertEqual(state["rescue_iso"]["overall_status"], "yellow")

    def test_usb_write_blocked_counts_as_green_safety_gate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._complete_docs(repo)
            with (
                patch.object(pov, "build_deploy_job_state", return_value=self._deploy(exit_code=0)),
                patch.object(pov, "build_update_status", return_value=self._update()),
                patch.object(pov, "build_rescue_iso_dashboard_state", return_value=self._rescue()),
                patch.object(pov, "build_packaging_readiness_state", return_value=self._packaging()),
            ):
                state = pov.build_project_overview_dashboard_state(repo_root=repo)
        self.assertEqual(state["usb_write_gate"]["overall_status"], "green")
        self.assertFalse(state["usb_write_gate"]["allowed"])

    def test_dpkg_preflight_ok_and_pre_chroot_ok_are_green(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._complete_docs(repo)
            for dpkg_status in ("ok", "pre_chroot_ok"):
                with (
                    patch.object(pov, "build_deploy_job_state", return_value=self._deploy(exit_code=0)),
                    patch.object(pov, "build_update_status", return_value=self._update()),
                    patch.object(pov, "build_rescue_iso_dashboard_state", return_value=self._rescue(dpkg=dpkg_status)),
                    patch.object(pov, "build_packaging_readiness_state", return_value=self._packaging()),
                ):
                    state = pov.build_project_overview_dashboard_state(repo_root=repo)
                self.assertEqual(state["dpkg_preflight"]["overall_status"], "green")

    def test_test_failure_register_presence_sets_overview_green(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._complete_docs(repo)
            with (
                patch.object(pov, "build_deploy_job_state", return_value=self._deploy(exit_code=0)),
                patch.object(pov, "build_update_status", return_value=self._update()),
                patch.object(pov, "build_rescue_iso_dashboard_state", return_value=self._rescue()),
                patch.object(pov, "build_packaging_readiness_state", return_value=self._packaging()),
            ):
                state = pov.build_project_overview_dashboard_state(repo_root=repo)
        self.assertEqual(state["tests"]["summary_status"], "green")
        self.assertEqual(state["tests"]["open_failures_status"], "red")

    def test_monolith_docs_keep_monolith_area_yellow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._complete_docs(repo)
            with (
                patch.object(pov, "build_deploy_job_state", return_value=self._deploy(exit_code=0)),
                patch.object(pov, "build_update_status", return_value=self._update()),
                patch.object(pov, "build_rescue_iso_dashboard_state", return_value=self._rescue()),
                patch.object(pov, "build_packaging_readiness_state", return_value=self._packaging(status="green")),
            ):
                state = pov.build_project_overview_dashboard_state(repo_root=repo)
        self.assertEqual(state["monolith"]["overall_status"], "yellow")
        self.assertNotEqual(state["status"], "green")

    def test_packaging_presence_never_sets_install_test_passed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._complete_docs(repo)
            with (
                patch.object(pov, "build_deploy_job_state", return_value=self._deploy(exit_code=0)),
                patch.object(pov, "build_update_status", return_value=self._update()),
                patch.object(pov, "build_rescue_iso_dashboard_state", return_value=self._rescue()),
                patch.object(pov, "build_packaging_readiness_state", return_value=self._packaging(status="green")),
            ):
                state = pov.build_project_overview_dashboard_state(repo_root=repo)
        self.assertEqual(state["packaging"]["overall_status"], "green")
        self.assertFalse(state["packaging"]["install_test_passed"])

    def test_missing_evidence_prevents_green(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._complete_docs(repo)
            (repo / "docs/evidence/EVIDENCE_INDEX.md").unlink()
            with (
                patch.object(pov, "build_deploy_job_state", return_value=self._deploy(exit_code=0)),
                patch.object(pov, "build_update_status", return_value=self._update()),
                patch.object(pov, "build_rescue_iso_dashboard_state", return_value=self._rescue()),
                patch.object(pov, "build_packaging_readiness_state", return_value=self._packaging(status="green")),
            ):
                state = pov.build_project_overview_dashboard_state(repo_root=repo)
        self.assertEqual(state["evidence"]["overall_status"], "yellow")
        self.assertNotEqual(state["status"], "green")

    def test_runtime_offline_keeps_runtime_red(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._complete_docs(repo)
            with (
                patch.object(pov, "build_deploy_job_state", return_value=self._deploy(exit_code=11, last_job_status="failed", summary="offline")),
                patch.object(pov, "build_update_status", return_value=self._update(status="blocked", deploy_required=True)),
                patch.object(pov, "build_rescue_iso_dashboard_state", return_value=self._rescue(status="red")),
                patch.object(pov, "build_packaging_readiness_state", return_value=self._packaging()),
            ):
                state = pov.build_project_overview_dashboard_state(repo_root=repo)
        self.assertEqual(state["runtime"]["overall_status"], "red")

    def test_module_is_read_only_and_runs_no_actions(self) -> None:
        src = (_backend / "core/project_overview_dashboard_state.py").read_text(encoding="utf-8")
        self.assertNotIn("apt install", src)
        self.assertNotIn("apt upgrade", src)
        self.assertNotIn("lb build", src)
        self.assertNotIn("dd if=", src)

    def test_new_routes_are_registered_in_app(self) -> None:
        cc = (_backend / "api" / "routes" / "control_center_readonly.py").read_text(encoding="utf-8")
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertIn('@router.get("/api/dev-dashboard/packaging/readiness")', cc)
        self.assertIn('@router.get("/api/dev-dashboard/project-overview")', cc)
        self.assertIn("include_router(control_center_readonly_router)", app_text)


if __name__ == "__main__":
    unittest.main()
