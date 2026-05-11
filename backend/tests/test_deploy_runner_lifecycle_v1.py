"""Tests für Runner-Lifecycle, Locks, TOCTOU-Rechecks, Audit (kein Device-Write)."""

from __future__ import annotations

import json
import os
import re
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy import runner_lifecycle as rl
from deploy.real_write_runner_contract import build_real_write_job
import tools.deploy_write_runner as rw_mod


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


class TestDeployRunnerLifecycleV1(unittest.TestCase):
    def setUp(self):
        self._cache = _BACKEND / "cache" / "deploy"
        self._cache.mkdir(parents=True, exist_ok=True)
        self._locks = self._cache / "runner-locks"
        self._audit = self._cache / "runner-audit"
        self._img = self._cache / "lifecycle.img"
        self._img.write_bytes(b"\x00" * 2048)
        self._img_path = str(self._img.resolve())
        for p in self._locks.glob("*.lock.json"):
            try:
                p.unlink()
            except OSError:
                pass
        rw_mod._clear_replay_guard_state_for_tests()
        if "DEPLOY_RUNNER_REPLAY_GUARD" in os.environ:
            del os.environ["DEPLOY_RUNNER_REPLAY_GUARD"]

    def tearDown(self):
        rw_mod._clear_replay_guard_state_for_tests()
        if "DEPLOY_RUNNER_REPLAY_GUARD" in os.environ:
            del os.environ["DEPLOY_RUNNER_REPLAY_GUARD"]
        for p in self._locks.glob("testlc*.lock.json"):
            try:
                p.unlink()
            except OSError:
                pass

    def _job(self, **kwargs):
        now = datetime.now(timezone.utc)
        return build_real_write_job(
            job_id=kwargs.get("job_id", "job_lc_01"),
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

    def test_illegal_transition_blocked(self):
        lc, _ = rl.build_runner_lifecycle(job_id="x1")
        self.assertEqual(lc.get("state"), rl.STATE_CREATED)
        lc2, code = rl.transition_runner_state(lc, rl.STATE_COMPLETED)
        self.assertEqual(code, rl.DEPLOY_RUNNER_STATE_TRANSITION_BLOCKED)
        self.assertEqual(lc2.get("state"), rl.STATE_CREATED)

    def test_stale_lock_cleanup(self):
        rl._ensure_dirs()
        path = rl._lock_path("stale_job_test")
        path.write_text(
            json.dumps(
                {
                    "lock_id": "old",
                    "job_id": "stale_job_test",
                    "pid": 999999001,
                    "created_at": "2019-01-01T00:00:00+00:00",
                    "state": rl.STATE_LOCKED,
                }
            ),
            encoding="utf-8",
        )
        n = rl.cleanup_stale_runner_locks(ttl_seconds=300)
        self.assertGreaterEqual(n, 1)
        self.assertFalse(path.exists())

    def test_duplicate_lock_blocked(self):
        ok1, e1 = rl.acquire_runner_lock(job_id="dup_lc", lock_id="k1")
        ok2, e2 = rl.acquire_runner_lock(job_id="dup_lc", lock_id="k2")
        self.assertTrue(ok1, msg=e1)
        self.assertFalse(ok2)
        self.assertEqual(e2, "DEPLOY_RUNNER_LOCK_BUSY")
        rl.release_runner_lock("dup_lc")

    def test_replay_blocked_in_process(self):
        os.environ["DEPLOY_RUNNER_REPLAY_GUARD"] = "1"
        j = self._job(job_id="replay_lc")
        c1, p1 = rw_mod.dry_run_with_loaded_job(j)
        self.assertEqual(c1, 0, msg=p1)
        c2, p2 = rw_mod.dry_run_with_loaded_job(dict(j))
        self.assertEqual(c2, 1)
        self.assertIn("REPLAY", str(p2.get("errors")))

    def test_snapshot_drift_blocked(self):
        base = rl.extract_runner_baseline_from_job(self._job())
        cur = dict(base)
        cur["guard_subset"] = dict(base.get("guard_subset") or {})
        cur["guard_subset"]["snapshot_fingerprint"] = "b" * 64
        ok, errs = rl.recheck_runner_consistency(checkpoint="pre_ready", baseline=base, current=cur)
        self.assertFalse(ok)
        self.assertTrue(any("guard_subset" in e for e in errs))

    def test_fingerprint_drift_blocked(self):
        base = rl.extract_runner_baseline_from_job(self._job())
        cur = dict(base)
        cur["snapshot_fingerprint"] = "c" * 64
        ok, errs = rl.recheck_runner_consistency(checkpoint="pre_ready", baseline=base, current=cur)
        self.assertFalse(ok)

    def test_mount_drift_blocked(self):
        base = rl.extract_runner_baseline_from_job(self._job())
        cur = dict(base)
        cur["mounted"] = True
        ok, errs = rl.recheck_runner_consistency(checkpoint="pre_writing", baseline=base, current=cur)
        self.assertFalse(ok)
        self.assertTrue(any("mounted" in e for e in errs))

    def test_readonly_drift_blocked(self):
        base = rl.extract_runner_baseline_from_job(self._job())
        cur = dict(base)
        cur["readonly"] = True
        ok, errs = rl.recheck_runner_consistency(checkpoint="pre_verifying", baseline=base, current=cur)
        self.assertFalse(ok)

    def test_audit_entries_written_on_dry_run(self):
        j = self._job(job_id="audit_lc_job")

        def _audit_line_count() -> int:
            total = 0
            for ap in rl._AUDIT_DIR.glob("audit-*.jsonl"):
                try:
                    total += sum(
                        1
                        for line in ap.read_text(encoding="utf-8").splitlines()
                        if line.strip()
                    )
                except OSError:
                    pass
            return total

        lines_before = _audit_line_count()
        code, payload = rw_mod.dry_run_with_loaded_job(j)
        self.assertEqual(code, 0, msg=payload)
        self.assertGreaterEqual(int(payload.get("audit_entries_written") or 0), 1)
        self.assertGreater(_audit_line_count(), lines_before)

    def test_cleanup_expired_lock_via_ttl(self):
        rl._ensure_dirs()
        path = rl._lock_path("exp_lock_job")
        path.write_text(
            json.dumps(
                {
                    "lock_id": "e",
                    "job_id": "exp_lock_job",
                    "pid": os.getpid(),
                    "created_at": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(),
                    "state": rl.STATE_LOCKED,
                }
            ),
            encoding="utf-8",
        )
        n = rl.cleanup_expired_runner_locks(ttl_seconds=3600)
        self.assertGreaterEqual(n, 1)
        self.assertFalse(path.exists())

    def test_cleanup_expired_runner_jobs_removes_file(self):
        now = datetime.now(timezone.utc)
        j = self._job(job_id="exp_job_json", expires_at=now - timedelta(hours=1))
        p = self._cache / "exp_job_json_cleanup.json"
        p.write_text(json.dumps(j), encoding="utf-8")
        n = rl.cleanup_expired_runner_jobs(jobs_root=self._cache)
        self.assertGreaterEqual(n, 1)
        self.assertFalse(p.exists())

    def test_no_forbidden_calls_in_lifecycle(self):
        src = (_BACKEND / "deploy" / "runner_lifecycle.py").read_text(encoding="utf-8")
        lower = src.lower()
        self.assertNotIn("os.system", lower)
        self.assertNotIn("subprocess", lower)
        self.assertNotIn("shell=true", lower)
        self.assertIsNone(re.search(r"\bopen\s*\([^)]*/dev/", lower), msg="direct /dev open pattern")
        for token in ("mkfs", "dd", "mount", "losetup", "parted"):
            self.assertIsNone(re.search(rf"\b{re.escape(token)}\b", lower), msg=token)

    def test_no_device_write_in_runner_module(self):
        src = (_BACKEND / "tools" / "deploy_write_runner.py").read_text(encoding="utf-8")
        self.assertNotIn("/dev/", src.replace('"""', ""), msg="runner tool should not embed device paths")

    def test_terminal_no_transition(self):
        lc, _ = rl.build_runner_lifecycle(job_id="t1")
        lc, _ = rl.transition_runner_state(lc, rl.STATE_VALIDATED)
        lc, _ = rl.transition_runner_state(lc, rl.STATE_LOCKED)
        lc, _ = rl.transition_runner_state(lc, rl.STATE_READY)
        lc, _ = rl.transition_runner_state(lc, rl.STATE_COMPLETED)
        lc2, code = rl.transition_runner_state(lc, rl.STATE_WRITING)
        self.assertEqual(code, rl.DEPLOY_RUNNER_STATE_TRANSITION_BLOCKED)


if __name__ == "__main__":
    unittest.main()
