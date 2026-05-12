"""Read-only Permission-Boundary Audits für Deploy Runner."""

from __future__ import annotations

import errno
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_permission_boundary import (
    audit_runner_binary_path,
    audit_runner_environment,
    audit_runner_job_directory,
    build_runner_sudoers_policy_example,
)


class TestDeployRunnerPermissionBoundaryV1(unittest.TestCase):
    def _assert_no_production_python_names_sudoers_dropin(self, canonical: str) -> None:
        """Wenn /etc nicht statbar ist: sicherstellen, dass kein Produkt-Python diesen Drop-in-Pfad literal referenziert.

        Ziel ist der Nachweis, dass der Codepfad keinen Schreib-/Installationszielstring für diesen falschen
        Dateinamen enthält (Boundary-Audit). Der kanonische produktive Pfad nutzt `setuphelfer-deploy-runner`.
        """
        paths: list[Path] = []
        deploy_root = _BACKEND / "deploy"
        if deploy_root.is_dir():
            paths.extend(sorted(deploy_root.rglob("*.py")))
        runner_tool = _BACKEND / "tools" / "deploy_write_runner.py"
        if runner_tool.is_file():
            paths.append(runner_tool)
        for path in paths:
            rel = path.relative_to(_BACKEND)
            if "test" in rel.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if canonical in text:
                self.fail(f"production source must not reference {canonical!r}: {path}")

    def test_sudoers_example_has_required_restrictions(self):
        out = build_runner_sudoers_policy_example()
        req = set(out["required_restrictions"])
        expected = {
            "RUNNER_REQUIRE_ABSOLUTE_PATH",
            "RUNNER_REQUIRE_FIXED_JOB_DIRECTORY",
            "RUNNER_REQUIRE_ENV_RESET",
            "RUNNER_BLOCK_PYTHONPATH",
            "RUNNER_BLOCK_LD_PRELOAD",
            "RUNNER_BLOCK_DYNAMIC_PATH",
            "RUNNER_BLOCK_WILDCARDS",
            "RUNNER_REQUIRE_NOINTERACTIVE",
            "RUNNER_REQUIRE_NO_SHELL",
        }
        self.assertTrue(expected.issubset(req))

    def test_ld_preload_blocked(self):
        out = audit_runner_environment(env={"PATH": "/usr/bin", "LD_PRELOAD": "/tmp/x.so"})
        self.assertEqual(out["environment_status"], "blocked")
        self.assertIn("LD_PRELOAD", out["blocked_variables"])

    def test_pythonpath_warning_or_block(self):
        out = audit_runner_environment(env={"PATH": "/usr/bin", "PYTHONPATH": "/tmp/x"})
        self.assertIn("PYTHONPATH", out["blocked_variables"])
        self.assertIn(out["environment_status"], {"warning", "blocked"})

    def test_path_relative_segment_warning(self):
        out = audit_runner_environment(env={"PATH": "/usr/bin:bin:/bin"})
        self.assertIn("PATH_CONTAINS_RELATIVE_SEGMENT", out["warnings"])

    def test_path_empty_segment_warning(self):
        out = audit_runner_environment(env={"PATH": "/usr/bin::/bin"})
        self.assertIn("PATH_CONTAINS_EMPTY_SEGMENT", out["warnings"])

    def test_runner_path_relative_blocked(self):
        out = audit_runner_binary_path("backend/tools/deploy_write_runner.py")
        self.assertEqual(out["path_status"], "blocked")

    def test_runner_path_symlink_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "runner.py"
            target.write_text("print('x')\n", encoding="utf-8")
            link = root / "runner-link.py"
            link.symlink_to(target)
            out = audit_runner_binary_path(str(link))
            self.assertEqual(out["path_status"], "blocked")
            self.assertIn("runner_path_symlink", out["errors"])

    def test_world_writable_directory_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            os.chmod(root, 0o777)
            p = root / "runner.py"
            p.write_text("print('x')\n", encoding="utf-8")
            out = audit_runner_binary_path(str(p.resolve()))
            self.assertEqual(out["path_status"], "blocked")

    def test_job_directory_traversal_blocked(self):
        out = audit_runner_job_directory("/var/lib/setuphelfer/deploy-jobs/../evil")
        self.assertEqual(out["path_status"], "blocked")

    def test_job_directory_symlink_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            real = root / "jobs"
            real.mkdir()
            link = root / "jobs-link"
            link.symlink_to(real)
            out = audit_runner_job_directory(str(link), allowed_prefixes=[str(root.resolve())])
            self.assertEqual(out["path_status"], "blocked")

    def test_absolute_safe_paths_ok(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            jobs = root / "deploy-jobs"
            jobs.mkdir()
            runner_dir = root / "opt" / "setuphelfer" / "backend" / "tools"
            runner_dir.mkdir(parents=True)
            runner = runner_dir / "deploy_write_runner.py"
            runner.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            os.chmod(root, 0o755)
            os.chmod(runner_dir, 0o755)
            out_path = audit_runner_binary_path(str(runner))
            out_job = audit_runner_job_directory(str(jobs), allowed_prefixes=[str(root)])
            self.assertIn(out_path["path_status"], {"ok", "warning"})
            self.assertEqual(out_job["path_status"], "ok")

    def test_no_sudoers_file_written(self):
        """Kein Drop-in `/etc/sudoers.d/setuphelfer-runner` auf dem Host (sofern stat möglich).

        Unter Python 3.12+ wirft `Path.exists()` hier oft `PermissionError` (pathlib ignoriert EACCES/EPERM
        nicht wie ENOENT). `os.lstat` ist gleichwertig; bei fehlenden Rechten bleibt der Nachweis, dass
        kein Produktcode diesen Pfad literal ansteuert (kein write/open/chmod zu sudoers aus dem getesteten
        Quellbaum für diesen String).
        """
        sudoers_dropin = "/etc/sudoers.d/setuphelfer-runner"
        try:
            os.lstat(sudoers_dropin)
        except FileNotFoundError:
            return
        except PermissionError:
            self._assert_no_production_python_names_sudoers_dropin(sudoers_dropin)
            return
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EPERM):
                self._assert_no_production_python_names_sudoers_dropin(sudoers_dropin)
                return
            raise
        self.fail(f"unexpected host sudoers drop-in exists: {sudoers_dropin!r}")

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_permission_boundary.py").read_text(encoding="utf-8").lower()
        forbidden_patterns = [
            r"\bvisudo\b",
            r"\bsudo\s",
            r"chmod\(",
            r"chown\(",
            r"subprocess\.",
            r"os\.system\(",
            r"shell\s*=\s*true",
            r"\bdd\b",
            r"\bmkfs\b",
            r"\bparted\b",
            r"\bfdisk\b",
            r"\bsfdisk\b",
            r"mount\(",
            r"umount\(",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(re.search(pat, src), msg=pat)

    def test_audit_routes_registered(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        paths = {getattr(r, "path", "") for r in app.routes}
        self.assertIn("/api/deploy/runner/audit/sudoers", paths)
        self.assertIn("/api/deploy/runner/audit/environment", paths)
        self.assertIn("/api/deploy/runner/audit/path", paths)
        self.assertIn("/api/deploy/runner/audit/jobdir", paths)

