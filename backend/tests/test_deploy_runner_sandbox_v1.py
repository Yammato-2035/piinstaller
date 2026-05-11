"""Tests für simuliertes Runner-Sandbox-Modell (strict dry-run)."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_sandbox import (
    build_runner_privilege_model,
    build_runner_recovery_analysis,
    build_runner_sandbox_policy,
    build_runner_stdio_policy,
    build_runner_timeout_model,
    build_sandbox_environment,
)


class TestDeployRunnerSandboxV1(unittest.TestCase):
    def test_minimal_env_whitelist(self):
        out = build_sandbox_environment(source_environment={"PATH": "/usr/local/bin:/usr/bin", "LANG": "C.UTF-8"})
        env = out["allowed_environment"]
        self.assertEqual(env.get("PATH"), "/usr/bin:/bin")
        self.assertIn("LANG", env)
        self.assertNotIn("PYTHONPATH", env)

    def test_ld_preload_blocked(self):
        out = build_sandbox_environment(source_environment={"PATH": "/usr/bin:/bin", "LD_PRELOAD": "/tmp/x.so"})
        self.assertIn("LD_PRELOAD", out["blocked_environment"])

    def test_pythonpath_blocked(self):
        out = build_sandbox_environment(source_environment={"PATH": "/usr/bin:/bin", "PYTHONPATH": "/tmp/lib"})
        self.assertIn("PYTHONPATH", out["blocked_environment"])

    def test_path_relative_warning_or_block(self):
        out = build_sandbox_environment(source_environment={"PATH": "/usr/bin:bin:/bin"})
        self.assertIn("PATH_CONTAINS_RELATIVE_SEGMENT", out["warnings"])

    def test_stdin_disabled(self):
        out = build_runner_stdio_policy()
        self.assertEqual(out["stdin_policy"], "disabled")

    def test_close_fds_required(self):
        out = build_runner_stdio_policy()
        self.assertTrue(bool((out["fd_policy"] or {}).get("close_fds_required")))

    def test_no_inherited_descriptors(self):
        out = build_runner_stdio_policy()
        self.assertFalse(bool((out["fd_policy"] or {}).get("inherit_extra_descriptors")))

    def test_one_shot_execution_set(self):
        out = build_runner_sandbox_policy()
        self.assertTrue(bool((out["execution_model"] or {}).get("one_shot_only")))

    def test_no_background_execution(self):
        out = build_runner_sandbox_policy()
        self.assertTrue(bool((out["execution_model"] or {}).get("no_background_mode")))

    def test_timeout_model_complete(self):
        out = build_runner_timeout_model()
        for k in [
            "max_runtime_seconds",
            "graceful_shutdown_timeout",
            "hard_kill_timeout",
            "stale_runner_timeout",
            "lock_cleanup_timeout",
            "would_send_signals",
        ]:
            self.assertIn(k, out)

    def test_signal_model_contains_term_and_kill(self):
        out = build_runner_timeout_model()
        self.assertIn("SIGTERM", out["would_send_signals"])
        self.assertIn("SIGKILL", out["would_send_signals"])

    def test_privilege_model_never_backend_root(self):
        out = build_runner_privilege_model()
        self.assertTrue(bool(out["never_run_backend_as_root"]))

    def test_recovery_model_contains_expected_modes(self):
        out = build_runner_recovery_analysis()
        modes = set(out["detected_failure_modes"])
        self.assertIn("stale_locks", modes)
        self.assertIn("orphan_audit_entries", modes)
        self.assertIn("replay_after_crash", modes)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_sandbox.py").read_text(encoding="utf-8").lower()
        forbidden_patterns = [
            r"\bsudo\b",
            r"\bsetuid\b",
            r"\bsetgid\b",
            r"subprocess\.",
            r"os\.system\(",
            r"shell\s*=\s*true",
            r"kill\(",
            r"sigkill",
            r"sigterm",
            r"\bdd\b",
            r"\bmkfs\b",
            r"\bparted\b",
            r"\bfdisk\b",
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
        self.assertIn("/api/deploy/runner/sandbox/policy", paths)
        self.assertIn("/api/deploy/runner/sandbox/environment", paths)
        self.assertIn("/api/deploy/runner/sandbox/stdio", paths)
        self.assertIn("/api/deploy/runner/sandbox/timeout", paths)
        self.assertIn("/api/deploy/runner/sandbox/privileges", paths)
        self.assertIn("/api/deploy/runner/sandbox/recovery", paths)

