"""Rescue backup execute — partition/USB test images with optional verify (RS-P3O)."""

from __future__ import annotations

import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.msi_windows_image_backup import run_f2_preflight, sha256_file
from core.rescue_backup_plan_contract import build_rescue_full_backup_plan

RESCUE_MEDIUM = Path("/run/live/medium")


def _booted_from_rescue() -> bool:
    return RESCUE_MEDIUM.is_dir()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def execute_rescue_backup(body: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(body or {})
    if not _booted_from_rescue():
        return {
            "success": False,
            "code": "not_rescue_boot",
            "message": "Backup-Ausführung nur nach Boot vom Rettungsstick.",
        }

    payload["booted_from_rescue"] = True
    plan = build_rescue_full_backup_plan(payload)
    if not plan.get("execute_allowed"):
        return {
            "success": False,
            "code": "execute_not_allowed",
            "message": "Plan erlaubt keine Ausführung — Preflight prüfen.",
            "plan_status": plan.get("plan_status"),
            "errors": plan.get("errors"),
            "warnings": plan.get("warnings"),
        }

    pf_dict = plan.get("preflight") or {}
    if not pf_dict.get("ok"):
        return {
            "success": False,
            "code": "preflight_failed",
            "message": "Preflight nicht bestanden.",
            "preflight": pf_dict,
        }

    paths = pf_dict.get("paths") or {}
    partial = paths.get("image_partial")
    final = paths.get("image_final")
    sha_path = paths.get("sha256_file")
    status_path = paths.get("status_json")
    if not partial or not final:
        return {"success": False, "code": "paths_missing", "message": "Backup-Pfade fehlen."}

    job_id = str(payload.get("plan_id") or uuid.uuid4().hex[:16])
    source = str(pf_dict.get("source_device") or payload.get("source_device") or "")
    size_bytes = int(pf_dict.get("source_size_bytes") or 0)

    status_payload: dict[str, Any] = {
        "job_id": job_id,
        "status": "running",
        "phase": "image_read_write",
        "source_device": source,
        "backup_scope": plan.get("source_scope"),
        "started_at": _utc_now(),
        "bytes_total": size_bytes,
    }

    partial_path = Path(partial)
    final_path = Path(final)
    partial_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        proc = subprocess.run(
            ["dd", f"if={source}", f"of={partial}", "bs=4M", "conv=fsync"],
            capture_output=True,
            text=True,
            timeout=max(3600, size_bytes // (2 * 1024 * 1024) + 120),
        )
    except subprocess.TimeoutExpired:
        return {"success": False, "code": "dd_timeout", "job_id": job_id}
    except (OSError, FileNotFoundError) as exc:
        return {"success": False, "code": "dd_failed", "message": str(exc), "job_id": job_id}

    if proc.returncode != 0:
        return {
            "success": False,
            "code": "dd_failed",
            "job_id": job_id,
            "stderr": (proc.stderr or "")[-500:],
        }

    partial_path.rename(final_path)
    written = final_path.stat().st_size
    status_payload["bytes_written"] = written
    status_payload["updated_at"] = _utc_now()

    digest = ""
    if payload.get("verify_requested", True) and sha_path:
        digest = sha256_file(final_path)
        Path(sha_path).write_text(f"{digest}  {final_path.name}\n", encoding="utf-8")
        status_payload["sha256"] = digest
        status_payload["verify_status"] = "ok"
        status_payload["phase"] = "complete"
    else:
        status_payload["phase"] = "complete"

    status_payload["status"] = "complete"
    status_payload["completed_at"] = _utc_now()
    status_payload["image_path"] = str(final_path)
    if status_path:
        Path(status_path).write_text(json.dumps(status_payload, indent=2) + "\n", encoding="utf-8")

    return {
        "success": True,
        "code": "backup_complete",
        "job_id": job_id,
        "source_device": source,
        "image_path": str(final_path),
        "sha256": digest or None,
        "bytes_written": written,
        "verify_requested": bool(payload.get("verify_requested", True)),
        "backup_scope": plan.get("source_scope"),
        "status": status_payload,
    }
