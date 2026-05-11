"""Runtime-/Containment-Tests für deploy_write_runner (Dry-run, kein Device-Write)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
_REPO = _BACKEND.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import tools.deploy_write_runner as rw_mod
from deploy.real_write_runner_contract import (
    build_real_write_job,
    compute_job_hash,
    job_file_allowed_roots,
    validate_real_write_job,
    validate_runner_job_file_location,
)


def _guard(**overrides):
    g = {
        "real_write_guard_id": "rg0123456789ab",
        "snapshot_fingerprint": "a" * 64,
        "hardware_gate_readiness": "test_ready",
        "final_confirmation_id": "fc0123456789ab",
        "harness_proof_hash": "b" * 64,
    }
    g.update(overrides)
    return g


class TestDeployWriteRunnerRuntimeV1(unittest.TestCase):
    def setUp(self):
        self._cache = _BACKEND / "cache" / "deploy"
        self._cache.mkdir(parents=True, exist_ok=True)
        self._img = self._cache / "runner_rt.img"
        self._img.write_bytes(b"\x00" * 2048)
        self._img_path = str(self._img.resolve())
        rw_mod._clear_replay_guard_state_for_tests()
        if _REPLAY_ENV in os.environ:
            del os.environ[_REPLAY_ENV]

    def tearDown(self):
        rw_mod._clear_replay_guard_state_for_tests()
        if _REPLAY_ENV in os.environ:
            del os.environ[_REPLAY_ENV]

    def _build_job(self, **kwargs):
        now = datetime.now(timezone.utc)
        return build_real_write_job(
            job_id=kwargs.get("job_id", "job_rt_01"),
            created_at=kwargs.get("created_at", now),
            expires_at=kwargs.get("expires_at", now + timedelta(hours=1)),
            target_device=kwargs.get("target_device", "/dev/sdz"),
            image_path=kwargs.get("image_path", self._img_path),
            image_sha256=kwargs.get("image_sha256", "0" * 64),
            image_size_bytes=kwargs.get("image_size_bytes", 2048),
            max_bytes=kwargs.get("max_bytes", 2048),
            guard=kwargs.get("guard", _guard()),
            constraints=kwargs.get("constraints"),
        )

    def test_valid_dry_run_cli(self):
        j = self._build_job()
        p = self._cache / "job_rt_ok.json"
        p.write_text(json.dumps(j), encoding="utf-8")
        script = _BACKEND / "tools" / "deploy_write_runner.py"
        r = subprocess.run(
            [sys.executable, str(script), "--job", str(p), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(_REPO),
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        out = json.loads(r.stdout.strip())
        self.assertEqual(out["code"], "DEPLOY_RUNNER_DRY_RUN_OK")
        self.assertEqual(
            sorted(out.keys()),
            sorted(
                [
                    "audit_entries_written",
                    "code",
                    "errors",
                    "image_path",
                    "job_id",
                    "lock_id",
                    "runner_state",
                    "target_device",
                    "warnings",
                    "would_write",
                ]
            ),
        )
        self.assertEqual(out["runner_state"], "completed")
        self.assertGreaterEqual(int(out["audit_entries_written"]), 1)

    def test_hash_mismatch_cli(self):
        j = self._build_job()
        j["job_hash"] = "f" * 64
        p = self._cache / "job_rt_badhash.json"
        p.write_text(json.dumps(j), encoding="utf-8")
        script = _BACKEND / "tools" / "deploy_write_runner.py"
        r = subprocess.run(
            [sys.executable, str(script), "--job", str(p), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(_REPO),
        )
        self.assertEqual(r.returncode, 1)
        out = json.loads(r.stdout.strip())
        self.assertEqual(out["code"], "DEPLOY_RUNNER_DRY_RUN_BLOCKED")
        self.assertIn("DEPLOY_RUNNER_JOB_HASH_MISMATCH", out["errors"])

    def test_expired_cli(self):
        now = datetime.now(timezone.utc)
        j = self._build_job(created_at=now - timedelta(hours=2), expires_at=now - timedelta(minutes=1))
        p = self._cache / "job_rt_expired.json"
        p.write_text(json.dumps(j), encoding="utf-8")
        script = _BACKEND / "tools" / "deploy_write_runner.py"
        r = subprocess.run(
            [sys.executable, str(script), "--job", str(p), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(_REPO),
        )
        self.assertEqual(r.returncode, 1)
        out = json.loads(r.stdout.strip())
        self.assertEqual(out["code"], "DEPLOY_RUNNER_DRY_RUN_BLOCKED")
        self.assertIn("DEPLOY_RUNNER_JOB_EXPIRED", out["errors"])

    def test_symlink_job_path_blocked(self):
        j = self._build_job()
        real = self._cache / "job_rt_real.json"
        link = self._cache / "job_rt_link.json"
        real.write_text(json.dumps(j), encoding="utf-8")
        try:
            link.unlink(missing_ok=True)
        except TypeError:
            if link.exists():
                link.unlink()
        link.symlink_to(real.name)
        script = _BACKEND / "tools" / "deploy_write_runner.py"
        r = subprocess.run(
            [sys.executable, str(script), "--job", str(link), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(_REPO),
        )
        self.assertEqual(r.returncode, 1)
        out = json.loads(r.stdout.strip())
        self.assertEqual(out["code"], "DEPLOY_RUNNER_DRY_RUN_BLOCKED")
        self.assertTrue(any("symlink" in e for e in out["errors"]))

    def test_traversal_job_path_blocked(self):
        outside = _BACKEND / "job_rt_outside.json"
        j = self._build_job()
        outside.write_text(json.dumps(j), encoding="utf-8")
        script = _BACKEND / "tools" / "deploy_write_runner.py"
        rel = os.path.join("backend", "cache", "deploy", "..", "..", "job_rt_outside.json")
        r = subprocess.run(
            [sys.executable, str(script), "--job", rel, "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(_REPO),
        )
        self.assertEqual(r.returncode, 1)
        out = json.loads(r.stdout.strip())
        self.assertEqual(out["code"], "DEPLOY_RUNNER_DRY_RUN_BLOCKED")
        self.assertTrue(any("outside" in e or "prefix" in e for e in out["errors"]))

    def test_job_outside_prefix_blocked(self):
        import tempfile

        j = self._build_job()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(j, f)
            tmp = f.name
        try:
            script = _BACKEND / "tools" / "deploy_write_runner.py"
            r = subprocess.run(
                [sys.executable, str(script), "--job", tmp, "--dry-run"],
                capture_output=True,
                text=True,
                cwd=str(_REPO),
            )
            self.assertEqual(r.returncode, 1)
            out = json.loads(r.stdout.strip())
            self.assertEqual(out["code"], "DEPLOY_RUNNER_DRY_RUN_BLOCKED")
            self.assertTrue(any("outside" in e or "prefix" in e for e in out["errors"]))
        finally:
            os.unlink(tmp)

    def test_replay_second_valid_call_blocked_in_process(self):
        os.environ[_REPLAY_ENV] = "1"
        j = self._build_job(job_id="replay_once")
        c1, p1 = rw_mod.dry_run_with_loaded_job(j)
        self.assertEqual(c1, 0, msg=p1)
        c2, p2 = rw_mod.dry_run_with_loaded_job(dict(j))
        self.assertEqual(c2, 1)
        self.assertEqual(p2["code"], "DEPLOY_RUNNER_DRY_RUN_BLOCKED")
        self.assertTrue(any("REPLAY" in str(e) for e in p2["errors"]))

    def test_manipulated_target_hash_mismatch(self):
        j = self._build_job()
        j["target_device"] = "/dev/sdy"
        v = validate_real_write_job(j)
        self.assertEqual(v["code"], "DEPLOY_RUNNER_JOB_HASH_MISMATCH")

    def test_manipulated_image_path_hash_mismatch(self):
        j = self._build_job()
        j["image_path"] = str((self._cache / "other.img").resolve())
        v = validate_real_write_job(j)
        self.assertEqual(v["code"], "DEPLOY_RUNNER_JOB_HASH_MISMATCH")

    def test_validate_runner_job_file_resolve_under_backend_cache(self):
        p = self._cache / "subü" / "job.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}", encoding="utf-8")
        resolved, err = validate_runner_job_file_location(str(p))
        self.assertIsNone(err)
        self.assertIsNotNone(resolved)
        root = (_BACKEND / "cache" / "deploy").resolve()
        resolved.relative_to(root)

    def test_hardlink_alias_allowed_not_symlink(self):
        j = self._build_job()
        p1 = self._cache / "job_hl_a.json"
        p2 = self._cache / "job_hl_b.json"
        p1.write_text(json.dumps(j), encoding="utf-8")
        try:
            p2.unlink()
        except OSError:
            pass
        os.link(p1, p2)
        code, payload = rw_mod.dry_run_job_path(str(p2))
        self.assertEqual(code, 0, msg=payload)

    def test_dry_run_no_file_mutate(self):
        j = self._build_job()
        p = self._cache / "job_rt_immutable.json"
        p.write_text(json.dumps(j), encoding="utf-8")
        before = p.read_bytes()
        script = _BACKEND / "tools" / "deploy_write_runner.py"
        subprocess.run(
            [sys.executable, str(script), "--job", str(p), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(_REPO),
            check=True,
        )
        self.assertEqual(p.read_bytes(), before)

    def test_no_forbidden_calls_in_runner_and_contract(self):
        files = [
            _BACKEND / "deploy" / "real_write_runner_contract.py",
            _BACKEND / "tools" / "deploy_write_runner.py",
        ]
        for fp in files:
            src = fp.read_text(encoding="utf-8")
            lower = src.lower()
            self.assertNotIn("os.system", lower)
            self.assertNotIn("subprocess", lower)
            self.assertNotIn("shell=true", lower)
            for token in ("mkfs", "parted", "fdisk", "sfdisk", "losetup", "wipefs"):
                self.assertIsNone(re.search(rf"\b{re.escape(token)}\b", lower), msg=f"{token} in {fp}")
            self.assertIsNone(re.search(r"\bdd\b", lower), msg=f"dd in {fp}")
            self.assertIsNone(re.search(r"\bmount\b", lower), msg=f"mount in {fp}")

    def test_job_allowed_roots_include_production_and_backend_cache(self):
        roots = job_file_allowed_roots()
        self.assertTrue(any("deploy-jobs" in str(r).replace("\\", "/") for r in roots))
        self.assertTrue(any(str(r).endswith(os.path.join("cache", "deploy")) or r.name == "deploy" for r in roots))


_REPLAY_ENV = "DEPLOY_RUNNER_REPLAY_GUARD"


if __name__ == "__main__":
    unittest.main()
