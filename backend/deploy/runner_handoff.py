from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from deploy.real_write_runner_contract import (
    build_real_write_job,
    validate_real_write_job,
    validate_runner_job_file_location,
)
from deploy.runner_lifecycle import append_runner_audit

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_ROOT.parent
_RUNNER_SCRIPT = _BACKEND_ROOT / "tools" / "deploy_write_runner.py"
_RUNNER_JOBS_DIR = _BACKEND_ROOT / "cache" / "deploy" / "runner-jobs"
_HANDOFF_TTL_SECONDS = 3600


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_job_filename(job_id: str) -> str:
    raw = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in str(job_id or ""))
    if not raw:
        raw = "unknown"
    return f"runner-job-{raw}.json"


def _runner_job_path(job_id: str) -> Path:
    return _RUNNER_JOBS_DIR / _safe_job_filename(job_id)


def _ensure_runner_jobs_dir() -> None:
    _RUNNER_JOBS_DIR.mkdir(parents=True, exist_ok=True)


def _write_atomic_json(target: Path, payload: dict[str, Any]) -> tuple[Path | None, str | None]:
    try:
        resolved = target.resolve(strict=False)
        root = _RUNNER_JOBS_DIR.resolve(strict=False)
        resolved.relative_to(root)
    except ValueError:
        return None, "runner_job_path_outside_prefix"
    try:
        if target.exists() and target.is_symlink():
            return None, "runner_job_path_symlink"
    except OSError:
        return None, "runner_job_path_symlink_check_failed"

    tmp = target.with_suffix(".tmp")
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True) + "\n"
    try:
        with tmp.open("w", encoding="utf-8") as f:
            f.write(raw)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        tmp.replace(target)
        try:
            os.chmod(target, 0o600)
        except OSError:
            pass
        return target, None
    except OSError as e:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        return None, f"runner_job_write_failed:{e}"


def create_runner_job_handoff(request: dict[str, Any]) -> dict[str, Any]:
    final_confirmation_result = request.get("final_confirmation_result") if isinstance(request.get("final_confirmation_result"), dict) else {}
    real_write_guard_result = request.get("real_write_guard_result") if isinstance(request.get("real_write_guard_result"), dict) else {}
    hardware_gate_report = request.get("hardware_gate_report") if isinstance(request.get("hardware_gate_report"), dict) else {}
    image_inspect_result = request.get("image_inspect_result") if isinstance(request.get("image_inspect_result"), dict) else {}
    write_execute_result = request.get("write_execute_result") if isinstance(request.get("write_execute_result"), dict) else {}

    out: dict[str, Any] = {
        "code": "DEPLOY_RUNNER_HANDOFF_FAILED",
        "handoff_id": None,
        "runner_job_path": None,
        "runner_exit_code": None,
        "runner_response": {},
        "audit_entries_written": 0,
        "warnings": [],
        "errors": [],
    }

    if str(real_write_guard_result.get("code") or "") != "DEPLOY_REAL_WRITE_READY":
        out["errors"].append("real_write_guard_not_ready")
        return out
    if str(final_confirmation_result.get("code") or "") != "DEPLOY_FINAL_CONFIRMATION_READY":
        out["errors"].append("final_confirmation_not_ready")
        return out
    readiness = str(
        hardware_gate_report.get("readiness_level")
        or ((hardware_gate_report.get("report") or {}).get("readiness_level") if isinstance(hardware_gate_report.get("report"), dict) else "")
        or ""
    )
    if readiness != "test_ready":
        out["errors"].append("hardware_gate_not_test_ready")
        return out

    target_device = str(write_execute_result.get("target_device") or "").strip()
    image_path = str(write_execute_result.get("image_path") or "").strip()
    expected_checksum = str((image_inspect_result.get("verification") or {}).get("checksum_actual") or "").strip()
    if not expected_checksum:
        expected_checksum = str((image_inspect_result.get("verification") or {}).get("checksum_expected_value") or "").strip()
    image_size = int((image_inspect_result.get("image") or {}).get("size_bytes") or 0)
    max_bytes = image_size
    if not target_device or not image_path or image_size <= 0:
        out["errors"].append("write_execute_or_image_invalid")
        return out

    guard = {
        "real_write_guard_id": str(real_write_guard_result.get("real_write_guard_id") or "unknown_guard"),
        "snapshot_fingerprint": str((real_write_guard_result.get("snapshot") or {}).get("fingerprint") or ""),
        "hardware_gate_readiness": "test_ready",
        "final_confirmation_id": str(final_confirmation_result.get("final_confirmation_id") or "unknown_fc"),
        "harness_proof_hash": "dryrun-placeholder-proof",
    }
    if not guard["snapshot_fingerprint"]:
        out["errors"].append("missing_snapshot_fingerprint")
        return out

    created_at = _now()
    expires_at = created_at + timedelta(minutes=10)
    handoff_id = secrets.token_hex(12)
    job_id = f"handoff_{handoff_id}"

    job = build_real_write_job(
        job_id=job_id,
        created_at=created_at,
        expires_at=expires_at,
        target_device=target_device,
        image_path=image_path,
        image_sha256=expected_checksum,
        image_size_bytes=image_size,
        max_bytes=max_bytes,
        guard=guard,
    )
    v = validate_real_write_job(job)
    if str(v.get("code") or "") != "DEPLOY_RUNNER_JOB_VALID":
        out["errors"] = [str(v.get("code") or "DEPLOY_RUNNER_HANDOFF_FAILED")] + list(v.get("errors") or [])
        return out

    _ensure_runner_jobs_dir()
    path = _runner_job_path(job_id)
    written, err = _write_atomic_json(path, job)
    if err or written is None:
        out["errors"].append(str(err or "runner_job_write_failed"))
        return out

    loc_ok, loc_err = validate_runner_job_file_location(str(written))
    if loc_err or loc_ok is None:
        out["errors"].append(str(loc_err or "runner_job_path_rejected"))
        return out

    append_runner_audit(
        runner_state="created",
        job_id=job_id,
        target_device=target_device,
        event="handoff_create",
        code="DEPLOY_RUNNER_HANDOFF_CREATED",
    )

    out["code"] = "DEPLOY_RUNNER_HANDOFF_CREATED"
    out["handoff_id"] = handoff_id
    out["runner_job_path"] = str(written)
    out["audit_entries_written"] = 1
    return out


def execute_runner_dryrun_handoff(request: dict[str, Any]) -> dict[str, Any]:
    created = create_runner_job_handoff(request)
    if str(created.get("code") or "") != "DEPLOY_RUNNER_HANDOFF_CREATED":
        return created

    handoff_id = str(created.get("handoff_id") or "")
    runner_job_path = str(created.get("runner_job_path") or "")
    minimal_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C", "LC_ALL": "C", "HOME": str(_REPO_ROOT)}
    try:
        proc = subprocess.run(
            [sys.executable, str(_RUNNER_SCRIPT), "--job", runner_job_path, "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(_REPO_ROOT),
            env=minimal_env,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired:
        append_runner_audit(
            runner_state="failed",
            job_id=f"handoff_{handoff_id}",
            target_device=str((request.get("write_execute_result") or {}).get("target_device") or ""),
            event="handoff_execute",
            code="DEPLOY_RUNNER_HANDOFF_TIMEOUT",
        )
        return {
            "code": "DEPLOY_RUNNER_HANDOFF_TIMEOUT",
            "handoff_id": handoff_id,
            "runner_job_path": runner_job_path,
            "runner_exit_code": None,
            "runner_response": {},
            "audit_entries_written": int(created.get("audit_entries_written") or 0) + 1,
            "warnings": [],
            "errors": ["runner_timeout"],
        }

    text = (proc.stdout or "").strip()
    try:
        runner_response = json.loads(text) if text else {}
    except json.JSONDecodeError:
        return {
            "code": "DEPLOY_RUNNER_HANDOFF_INVALID_RESPONSE",
            "handoff_id": handoff_id,
            "runner_job_path": runner_job_path,
            "runner_exit_code": proc.returncode,
            "runner_response": {},
            "audit_entries_written": int(created.get("audit_entries_written") or 0),
            "warnings": [],
            "errors": ["runner_response_json_invalid"],
        }

    if not isinstance(runner_response, dict) or "code" not in runner_response:
        return {
            "code": "DEPLOY_RUNNER_HANDOFF_INVALID_RESPONSE",
            "handoff_id": handoff_id,
            "runner_job_path": runner_job_path,
            "runner_exit_code": proc.returncode,
            "runner_response": runner_response if isinstance(runner_response, dict) else {},
            "audit_entries_written": int(created.get("audit_entries_written") or 0),
            "warnings": [],
            "errors": ["runner_response_contract_invalid"],
        }

    if int(proc.returncode) != 0:
        return {
            "code": "DEPLOY_RUNNER_HANDOFF_FAILED",
            "handoff_id": handoff_id,
            "runner_job_path": runner_job_path,
            "runner_exit_code": proc.returncode,
            "runner_response": runner_response,
            "audit_entries_written": int(created.get("audit_entries_written") or 0),
            "warnings": [],
            "errors": ["runner_exit_code_nonzero"],
        }

    append_runner_audit(
        runner_state=str(runner_response.get("runner_state") or "completed"),
        job_id=str(runner_response.get("job_id") or f"handoff_{handoff_id}"),
        target_device=str(runner_response.get("target_device") or ""),
        event="handoff_execute",
        code="DEPLOY_RUNNER_HANDOFF_COMPLETED",
    )

    return {
        "code": "DEPLOY_RUNNER_HANDOFF_COMPLETED",
        "handoff_id": handoff_id,
        "runner_job_path": runner_job_path,
        "runner_exit_code": proc.returncode,
        "runner_response": {
            "code": runner_response.get("code"),
            "runner_state": runner_response.get("runner_state"),
            "job_id": runner_response.get("job_id"),
        },
        "audit_entries_written": int(created.get("audit_entries_written") or 0) + 1,
        "warnings": [],
        "errors": [],
    }


def cleanup_runner_job_handoff(*, ttl_seconds: int = _HANDOFF_TTL_SECONDS, now: datetime | None = None) -> int:
    _ensure_runner_jobs_dir()
    now_utc = now or _now()
    removed = 0
    root = _RUNNER_JOBS_DIR.resolve(strict=False)
    for p in _RUNNER_JOBS_DIR.glob("runner-job-*.json"):
        try:
            if p.is_symlink():
                continue
            rp = p.resolve(strict=False)
            rp.relative_to(root)
        except (OSError, ValueError):
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        age = now_utc - datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
        if age.total_seconds() > int(ttl_seconds):
            try:
                p.unlink()
                removed += 1
            except OSError:
                pass
    return removed
