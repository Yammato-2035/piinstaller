#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PKIT_ACTION = "org.setuphelfer.backup.start"

JOB_ID_RE = re.compile(r"^[a-zA-Z0-9._-]{1,80}$")
ALLOWED_BACKUP_ROOT = Path("/mnt/setuphelfer/backups").resolve()
JOB_BASE_DIR = Path("/var/lib/setuphelfer/backup-jobs")
UNIT_PREFIX = "setuphelfer-backup@"
UNIT_SUFFIX = ".service"


def _emit(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload.get("ok") else 1


def _unit_name_for(job_id: str) -> str:
    return f"{UNIT_PREFIX}{job_id}{UNIT_SUFFIX}"


def _validate_job_id(job_id: str) -> bool:
    if not isinstance(job_id, str):
        return False
    if not JOB_ID_RE.fullmatch(job_id):
        return False
    return True


def _safe_resolve_under(base: Path, target: Path) -> Path | None:
    try:
        resolved = target.resolve(strict=True)
        resolved.relative_to(base.resolve())
        return resolved
    except Exception:
        return None


def _load_job(job_id: str) -> tuple[dict[str, Any] | None, str]:
    job_dir = JOB_BASE_DIR / job_id
    safe_job_dir = _safe_resolve_under(JOB_BASE_DIR, job_dir)
    if safe_job_dir is None:
        return None, "backup.starter_job_not_found"
    job_file = safe_job_dir / "job.json"
    if not job_file.is_file():
        return None, "backup.starter_job_not_found"
    try:
        payload = json.loads(job_file.read_text(encoding="utf-8") or "{}")
    except Exception:
        return None, "backup.starter_job_not_found"
    if not isinstance(payload, dict):
        return None, "backup.starter_job_not_found"
    return payload, ""


def _validate_backup_dir(path_value: str) -> bool:
    p = Path(path_value)
    if not p.is_absolute():
        return False
    resolved = _safe_resolve_under(ALLOWED_BACKUP_ROOT, p)
    return resolved is not None


def _result(ok: bool, action: str, job_id: str, code: str) -> dict[str, Any]:
    return {
        "ok": ok,
        "action": action,
        "job_id": job_id,
        "unit": _unit_name_for(job_id) if _validate_job_id(job_id) else "",
        "code": code,
    }


def _run_systemctl(action: str, unit: str) -> subprocess.CompletedProcess[str]:
    cmd = ["systemctl", action, unit]
    return subprocess.run(cmd, capture_output=True, text=True, check=False, shell=False)


def _authorized_for_starter() -> bool:
    """Root darf immer; sonst Polkit pkcheck für diese Binärinstanz."""
    if os.geteuid() == 0:
        return True
    try:
        cp = subprocess.run(
            [
                "pkcheck",
                "-a",
                PKIT_ACTION,
                "-p",
                str(os.getpid()),
            ],
            capture_output=True,
            text=True,
            shell=False,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return cp.returncode == 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        return _emit(
            {
                "ok": False,
                "action": "",
                "job_id": "",
                "unit": "",
                "code": "backup.starter_failed",
            }
        )
    action, job_id = args[0].strip().lower(), args[1].strip()
    if action not in {"start", "stop", "status"}:
        return _emit(_result(False, action, job_id, "backup.starter_failed"))
    if not _validate_job_id(job_id):
        return _emit(_result(False, action, job_id, "backup.starter_invalid_job_id"))
    if not _authorized_for_starter():
        return _emit(_result(False, action, job_id, "backup.starter_permission_denied"))
    job_payload, err_code = _load_job(job_id)
    if job_payload is None:
        return _emit(_result(False, action, job_id, err_code or "backup.starter_job_not_found"))
    backup_dir = str(job_payload.get("backup_dir") or "")
    if not _validate_backup_dir(backup_dir):
        return _emit(_result(False, action, job_id, "backup.starter_invalid_path"))

    unit = _unit_name_for(job_id)
    cp = _run_systemctl(action, unit)
    if cp.returncode != 0:
        return _emit(_result(False, action, job_id, "backup.starter_failed"))
    return _emit(_result(True, action, job_id, "backup.starter_started"))


if __name__ == "__main__":
    raise SystemExit(main())

