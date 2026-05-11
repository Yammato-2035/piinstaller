"""Tests für Deploy-Write-Runner Job-Contract und Dry-Run-CLI (kein Device-Write)."""

from __future__ import annotations

import json
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

from deploy.real_write_runner_contract import (
    SCHEMA_VERSION,
    _MAX_IMAGE_BYTES,
    build_real_write_job,
    compute_job_hash,
    default_constraints,
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


class TestDeployWriteRunnerContractV1(unittest.TestCase):
    def setUp(self):
        self._cache = _BACKEND / "cache" / "deploy"
        self._cache.mkdir(parents=True, exist_ok=True)
        self._img = self._cache / "runner_contract.img"
        self._img.write_bytes(b"\x00" * 2048)
        self._img_path = str(self._img.resolve())

    def _build_base(self, **kwargs):
        now = datetime.now(timezone.utc)
        return build_real_write_job(
            job_id=kwargs.get("job_id", "job_integration_01"),
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

    def test_valid_job_valid(self):
        j = self._build_base()
        v = validate_real_write_job(j)
        self.assertEqual(v["code"], "DEPLOY_RUNNER_JOB_VALID", msg=v)

    def test_missing_guard_field_invalid(self):
        j = self._build_base()
        del j["guard"]
        j["job_hash"] = compute_job_hash({k: v for k, v in j.items() if k != "job_hash"})
        v = validate_real_write_job(j)
        self.assertEqual(v["code"], "DEPLOY_RUNNER_JOB_INVALID")
        self.assertTrue(any("guard" in str(e) for e in v.get("errors", [])))

    def test_expired_job_expired(self):
        now = datetime.now(timezone.utc)
        j = self._build_base(created_at=now - timedelta(hours=2), expires_at=now - timedelta(hours=1))
        v = validate_real_write_job(j)
        self.assertEqual(v["code"], "DEPLOY_RUNNER_JOB_EXPIRED")

    def test_hash_mismatch(self):
        j = self._build_base()
        j["job_hash"] = "0" * 64
        v = validate_real_write_job(j)
        self.assertEqual(v["code"], "DEPLOY_RUNNER_JOB_HASH_MISMATCH")

    def test_image_over_max_invalid(self):
        j = self._build_base(image_size_bytes=_MAX_IMAGE_BYTES + 1, max_bytes=1024)
        v = validate_real_write_job(j)
        self.assertEqual(v["code"], "DEPLOY_RUNNER_JOB_IMAGE_INVALID")

    def test_image_path_outside_cache_invalid(self):
        outside = _REPO / "tmp_runner_img.img"
        outside.parent.mkdir(parents=True, exist_ok=True)
        outside.write_bytes(b"x")
        j = self._build_base(image_path=str(outside.resolve()))
        v = validate_real_write_job(j)
        self.assertEqual(v["code"], "DEPLOY_RUNNER_JOB_IMAGE_INVALID")

    def test_empty_target_invalid(self):
        j = self._build_base(target_device="")
        j["job_hash"] = compute_job_hash({k: v for k, v in j.items() if k != "job_hash"})
        v = validate_real_write_job(j)
        self.assertEqual(v["code"], "DEPLOY_RUNNER_JOB_TARGET_INVALID")

    def test_dry_run_cli_ok(self):
        j = self._build_base()
        p = self._cache / "job_ok.json"
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
        self.assertTrue(out.get("would_write"))

    def test_dry_run_cli_does_not_modify_job_file(self):
        j = self._build_base()
        p = self._cache / "job_immutable.json"
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

    def test_no_forbidden_calls_in_runner_sources(self):
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

    def test_schema_version_constant(self):
        self.assertEqual(SCHEMA_VERSION, 1)

    def test_default_constraints_max_matches_module(self):
        self.assertEqual(default_constraints()["max_image_size_bytes"], _MAX_IMAGE_BYTES)

    def test_validate_runner_job_file_location_empty(self):
        p, err = validate_runner_job_file_location("")
        self.assertIsNone(p)
        self.assertIsNotNone(err)

    def test_validate_runner_job_file_location_under_cache_ok(self):
        p = self._cache / "loc_check.json"
        p.write_text("{}", encoding="utf-8")
        resolved, err = validate_runner_job_file_location(str(p))
        self.assertIsNone(err)
        self.assertIsNotNone(resolved)


if __name__ == "__main__":
    unittest.main()
