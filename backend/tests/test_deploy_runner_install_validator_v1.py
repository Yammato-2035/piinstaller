"""Tests fuer Runner-Installations-Dry-run-Validator."""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_install_validator import validate_runner_installation_dryrun


def _plan(runner_path: str, interpreter_path: str, job_path: str) -> dict:
    return {
        "runner_binary": {"target_path": runner_path, "interpreter_path": interpreter_path},
        "job_directory": {"target_path": job_path, "allowed_prefixes": [str(Path(job_path).parent)]},
    }


class TestDeployRunnerInstallValidatorV1(unittest.TestCase):
    def test_valid_plan_and_safe_snippet_ok_or_review(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runner = root / "deploy_write_runner.py"
            runner.write_text("def deploy_write_runner():\n    return 'dry'\n", encoding="utf-8")
            jobdir = root / "deploy-jobs"
            jobdir.mkdir()
            plan = _plan(str(runner), "/usr/bin/python3", str(jobdir))
            snippet = f"Defaults env_reset\nsetuphelfer ALL=(root) NOPASSWD: /usr/bin/python3 {runner} --job {jobdir}/runner-job-001.json --dry-run"
            out = validate_runner_installation_dryrun(install_plan=plan, sudoers_snippet_text=snippet, environment={"PATH": "/usr/bin:/bin"})
            self.assertIn(out["validation_status"], ["ok", "review_required"])

    def test_missing_runner_path_review_required(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runner = root / "missing_runner.py"
            jobdir = root / "deploy-jobs"
            jobdir.mkdir()
            plan = _plan(str(runner), "/usr/bin/python3", str(jobdir))
            snippet = f"Defaults env_reset\nsetuphelfer ALL=(root) NOPASSWD: /usr/bin/python3 {runner} --job {jobdir}/runner-job-001.json --dry-run"
            out = validate_runner_installation_dryrun(install_plan=plan, sudoers_snippet_text=snippet, environment={"PATH": "/usr/bin:/bin"})
            self.assertEqual(out["validation_status"], "review_required")

    def test_runner_path_symlink_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            real = root / "deploy_write_runner.py"
            real.write_text("deploy_write_runner\n", encoding="utf-8")
            link = root / "runner_link.py"
            link.symlink_to(real)
            jobdir = root / "deploy-jobs"
            jobdir.mkdir()
            plan = _plan(str(link), "/usr/bin/python3", str(jobdir))
            snippet = f"Defaults env_reset\nsetuphelfer ALL=(root) NOPASSWD: /usr/bin/python3 {link} --job {jobdir}/runner-job-001.json --dry-run"
            out = validate_runner_installation_dryrun(install_plan=plan, sudoers_snippet_text=snippet, environment={"PATH": "/usr/bin:/bin"})
            self.assertEqual(out["validation_status"], "blocked")

    def test_jobdir_missing_review_required(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runner = root / "deploy_write_runner.py"
            runner.write_text("deploy_write_runner\n", encoding="utf-8")
            jobdir = root / "missing-jobs"
            plan = _plan(str(runner), "/usr/bin/python3", str(jobdir))
            snippet = f"Defaults env_reset\nsetuphelfer ALL=(root) NOPASSWD: /usr/bin/python3 {runner} --job {jobdir}/runner-job-001.json --dry-run"
            out = validate_runner_installation_dryrun(install_plan=plan, sudoers_snippet_text=snippet, environment={"PATH": "/usr/bin:/bin"})
            self.assertEqual(out["validation_status"], "review_required")

    def test_jobdir_symlink_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runner = root / "deploy_write_runner.py"
            runner.write_text("deploy_write_runner\n", encoding="utf-8")
            real = root / "real-jobs"
            real.mkdir()
            link = root / "jobs-link"
            link.symlink_to(real)
            plan = _plan(str(runner), "/usr/bin/python3", str(link))
            snippet = f"Defaults env_reset\nsetuphelfer ALL=(root) NOPASSWD: /usr/bin/python3 {runner} --job {link}/runner-job-001.json --dry-run"
            out = validate_runner_installation_dryrun(install_plan=plan, sudoers_snippet_text=snippet, environment={"PATH": "/usr/bin:/bin"})
            self.assertEqual(out["validation_status"], "blocked")

    def test_snippet_without_env_reset_blocked(self):
        out = validate_runner_installation_dryrun(
            install_plan={},
            sudoers_snippet_text="setuphelfer ALL=(root) NOPASSWD: /usr/bin/python3 /opt/setuphelfer/backend/tools/deploy_write_runner.py",
            environment={"PATH": "/usr/bin:/bin"},
        )
        self.assertEqual(out["validation_status"], "blocked")

    def test_snippet_with_env_keep_pythonpath_blocked(self):
        txt = "Defaults env_reset, env_keep += PYTHONPATH\nsetuphelfer ALL=(root) NOPASSWD: /usr/bin/python3 /opt/setuphelfer/backend/tools/deploy_write_runner.py"
        out = validate_runner_installation_dryrun(install_plan={}, sudoers_snippet_text=txt, environment={"PATH": "/usr/bin:/bin"})
        self.assertEqual(out["validation_status"], "blocked")

    def test_snippet_with_ld_preload_blocked(self):
        txt = "Defaults env_reset\nDefaults env_keep += LD_PRELOAD\nsetuphelfer ALL=(root) NOPASSWD: /usr/bin/python3 /opt/setuphelfer/backend/tools/deploy_write_runner.py"
        out = validate_runner_installation_dryrun(install_plan={}, sudoers_snippet_text=txt, environment={"PATH": "/usr/bin:/bin"})
        self.assertEqual(out["validation_status"], "blocked")

    def test_snippet_with_wildcard_blocked(self):
        txt = "Defaults env_reset\nsetuphelfer ALL=(root) NOPASSWD: /usr/bin/python3 /opt/setuphelfer/backend/tools/deploy_write_runner.py --job /var/lib/setuphelfer/deploy-jobs/*.json"
        out = validate_runner_installation_dryrun(install_plan={}, sudoers_snippet_text=txt, environment={"PATH": "/usr/bin:/bin"})
        self.assertEqual(out["validation_status"], "blocked")

    def test_snippet_with_all_all_blocked(self):
        txt = "Defaults env_reset\nsetuphelfer ALL=(ALL) ALL"
        out = validate_runner_installation_dryrun(install_plan={}, sudoers_snippet_text=txt, environment={"PATH": "/usr/bin:/bin"})
        self.assertEqual(out["validation_status"], "blocked")

    def test_rollback_steps_present_and_not_auto(self):
        out = validate_runner_installation_dryrun(install_plan={}, sudoers_snippet_text="", environment={"PATH": "/usr/bin:/bin"})
        steps = list((out.get("rollback_check") or {}).get("steps") or [])
        self.assertTrue(bool(steps))
        for step in steps:
            self.assertFalse(bool((step or {}).get("auto_allowed")))

    def test_no_install_apply_execute_route_present(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        paths = {getattr(r, "path", "") for r in app.routes}
        self.assertIn("/api/deploy/runner/install/validate", paths)
        self.assertNotIn("/api/deploy/runner/install/apply", paths)
        self.assertNotIn("/api/deploy/runner/install/execute", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_install_validator.py").read_text(encoding="utf-8").lower()
        forbidden_patterns = [
            r"\bsudo\b",
            r"\bvisudo\b",
            r"chmod\(",
            r"chown\(",
            r"mkdir\(",
            r"os\.system\(",
            r"subprocess\.",
            r"shell\s*=\s*true",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(re.search(pat, src), msg=pat)

