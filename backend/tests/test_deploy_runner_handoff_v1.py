"""Tests für Backend->Runner Handoff (Dry-run only)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

_BACKEND = Path(__file__).resolve().parent.parent
_REPO = _BACKEND.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_handoff import (
    _RUNNER_JOBS_DIR,
    cleanup_runner_job_handoff,
    create_runner_job_handoff,
    execute_runner_dryrun_handoff,
)


def _req() -> dict:
    cache = _BACKEND / "cache" / "deploy"
    cache.mkdir(parents=True, exist_ok=True)
    img = cache / "handoff.img"
    if not img.exists():
        img.write_bytes(b"\x01" * 2048)
    return {
        "final_confirmation_result": {"code": "DEPLOY_FINAL_CONFIRMATION_READY", "final_confirmation_id": "fc12345678"},
        "real_write_guard_result": {
            "code": "DEPLOY_REAL_WRITE_READY",
            "real_write_guard_id": "rg12345678",
            "snapshot": {"fingerprint": "a" * 64},
        },
        "hardware_gate_report": {"readiness_level": "test_ready"},
        "image_inspect_result": {
            "image": {"path": str(img.resolve()), "size_bytes": 2048},
            "verification": {"checksum_actual": "b" * 64},
        },
        "write_plan": {"plan_status": "ok", "blocked_reasons": []},
        "write_execute_result": {
            "code": "DEPLOY_WRITE_EXECUTE_READY",
            "target_device": "/dev/sdz",
            "image_path": str(img.resolve()),
        },
    }


class TestDeployRunnerHandoffV1(unittest.TestCase):
    def setUp(self) -> None:
        _RUNNER_JOBS_DIR.mkdir(parents=True, exist_ok=True)
        for p in _RUNNER_JOBS_DIR.glob("runner-job-*.json"):
            try:
                p.unlink()
            except OSError:
                pass

    def test_valid_dry_run_handoff(self):
        out = execute_runner_dryrun_handoff(_req())
        self.assertEqual(out["code"], "DEPLOY_RUNNER_HANDOFF_COMPLETED", msg=out)
        self.assertEqual(int(out["runner_exit_code"]), 0)
        self.assertEqual(str((out.get("runner_response") or {}).get("code")), "DEPLOY_RUNNER_DRY_RUN_OK")

    @patch("deploy.runner_handoff.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="runner", timeout=30))
    def test_runner_timeout(self, _mock_run):
        out = execute_runner_dryrun_handoff(_req())
        self.assertEqual(out["code"], "DEPLOY_RUNNER_HANDOFF_TIMEOUT")

    @patch("deploy.runner_handoff.subprocess.run")
    def test_invalid_json_response(self, mock_run):
        class P:
            returncode = 0
            stdout = "{not-json"

        mock_run.return_value = P()
        out = execute_runner_dryrun_handoff(_req())
        self.assertEqual(out["code"], "DEPLOY_RUNNER_HANDOFF_INVALID_RESPONSE")

    @patch("deploy.runner_handoff.subprocess.run")
    def test_manipulated_runner_response(self, mock_run):
        class P:
            returncode = 0
            stdout = json.dumps({"evil": True})

        mock_run.return_value = P()
        out = execute_runner_dryrun_handoff(_req())
        self.assertEqual(out["code"], "DEPLOY_RUNNER_HANDOFF_INVALID_RESPONSE")

    def test_jobfile_outside_prefix_blocked(self):
        req = _req()
        req["write_execute_result"]["image_path"] = str((_REPO / "outside.img").resolve())
        out = create_runner_job_handoff(req)
        self.assertEqual(out["code"], "DEPLOY_RUNNER_HANDOFF_FAILED")

    def test_symlink_jobfile_blocked(self):
        out = create_runner_job_handoff(_req())
        self.assertEqual(out["code"], "DEPLOY_RUNNER_HANDOFF_CREATED")
        p = Path(str(out["runner_job_path"]))
        link = p.with_name("runner-job-link.json")
        if link.exists():
            link.unlink()
        link.symlink_to(p.name)
        from deploy.real_write_runner_contract import validate_runner_job_file_location

        _, err = validate_runner_job_file_location(str(link))
        self.assertEqual(err, "job_path_symlink")

    def test_traversal_blocked(self):
        from deploy.real_write_runner_contract import validate_runner_job_file_location

        _, err = validate_runner_job_file_location(str(_RUNNER_JOBS_DIR / ".." / ".." / "x.json"))
        self.assertEqual(err, "job_path_outside_allowed_prefix")

    def test_missing_guard_blocked(self):
        req = _req()
        req["real_write_guard_result"] = {}
        out = create_runner_job_handoff(req)
        self.assertEqual(out["code"], "DEPLOY_RUNNER_HANDOFF_FAILED")

    def test_missing_final_confirmation_blocked(self):
        req = _req()
        req["final_confirmation_result"] = {}
        out = create_runner_job_handoff(req)
        self.assertEqual(out["code"], "DEPLOY_RUNNER_HANDOFF_FAILED")

    def test_hardware_gate_not_ready_blocked(self):
        req = _req()
        req["hardware_gate_report"] = {"readiness_level": "blocked"}
        out = create_runner_job_handoff(req)
        self.assertEqual(out["code"], "DEPLOY_RUNNER_HANDOFF_FAILED")

    def test_no_shell_true_and_no_device_write_patterns(self):
        src = (_BACKEND / "deploy" / "runner_handoff.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("shell=true", src)
        self.assertNotIn("dd", src)
        self.assertNotIn("mkfs", src)
        self.assertNotIn(" mount ", src)
        self.assertNotIn("losetup", src)

    def test_cleanup_deletes_expired_jobs(self):
        p = _RUNNER_JOBS_DIR / "runner-job-old.json"
        p.write_text("{}", encoding="utf-8")
        old = datetime.now(timezone.utc) - timedelta(hours=2)
        os_ts = old.timestamp()

        os.utime(p, (os_ts, os_ts))
        n = cleanup_runner_job_handoff(ttl_seconds=60)
        self.assertGreaterEqual(n, 1)
        self.assertFalse(p.exists())

    def test_atomic_write_creates_final_file_no_tmp(self):
        out = create_runner_job_handoff(_req())
        self.assertEqual(out["code"], "DEPLOY_RUNNER_HANDOFF_CREATED")
        p = Path(str(out["runner_job_path"]))
        self.assertTrue(p.exists())
        self.assertFalse(p.with_suffix(".tmp").exists())

    @patch("deploy.runner_handoff.subprocess.run")
    def test_runner_exitcode_nonzero_blocked(self, mock_run):
        class P:
            returncode = 5
            stdout = json.dumps({"code": "DEPLOY_RUNNER_DRY_RUN_BLOCKED", "runner_state": "failed", "job_id": "x"})

        mock_run.return_value = P()
        out = execute_runner_dryrun_handoff(_req())
        self.assertEqual(out["code"], "DEPLOY_RUNNER_HANDOFF_FAILED")

    @patch("deploy.runner_handoff.subprocess.run")
    def test_runner_subprocess_called_with_safe_args(self, mock_run):
        class P:
            returncode = 0
            stdout = json.dumps({"code": "DEPLOY_RUNNER_DRY_RUN_OK", "runner_state": "completed", "job_id": "x"})

        mock_run.return_value = P()
        out = execute_runner_dryrun_handoff(_req())
        self.assertEqual(out["code"], "DEPLOY_RUNNER_HANDOFF_COMPLETED")
        _, kwargs = mock_run.call_args
        self.assertIs(kwargs.get("shell"), False)
        self.assertEqual(int(kwargs.get("timeout")), 30)

    def test_api_route_registered(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        routes = [getattr(r, "path", None) for r in app.routes]
        self.assertIn("/api/deploy/runner/handoff", routes)

