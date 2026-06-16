"""Backup execute handlers — first POST slice (Phase B.4)."""

from __future__ import annotations

import os
import shutil
import signal
import threading
from pathlib import Path
from typing import Any, Optional

from fastapi import Request

from core import backup_readonly_runtime as rt
from core.backup_profiles import build_profile_preview


async def backup_job_cancel(job_id: str):
    job_id = (job_id or "").strip()
    runner_status = rt.read_backup_runner_status(job_id)
    if runner_status:
        rs_st = str(runner_status.get("status") or "").strip().lower()
        rt.sync_ram_job_from_runner(job_id)
        if rs_st == "cancelled":
            return rt.with_backup_contract(
                {"status": "success", "message": "Job bereits abgebrochen"},
                "backup.job_already_done",
                "info",
                {"job_id": job_id},
            )
        if rs_st in ("success", "error", "failed"):
            return rt.with_backup_contract(
                {"status": "success", "message": "Job ist bereits abgeschlossen"},
                "backup.job_already_done",
                "info",
                {"job_id": job_id, "runner_status": rs_st},
            )
        unit_name = str(runner_status.get("unit_name") or "").strip()
        unit_scope = str(runner_status.get("unit_scope") or "system").strip().lower()
        if not unit_name:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract({"status": "error", "message": "Runner-Unit unbekannt"}, "backup.cancel_failed", "error"),
            )
        if unit_scope == "user":
            stop_argv = ["systemctl", "--user", "stop", unit_name]
        else:
            stop_argv = ["systemctl", "stop", unit_name]
        stop_res = rt.systemctl_run_argv(stop_argv, timeout=30)
        if not stop_res.get("success"):
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Abbruch fehlgeschlagen"},
                    "backup.cancel_failed",
                    "error",
                    {"unit_name": unit_name, "stderr": (stop_res.get("stderr") or "")[:300]},
                ),
            )
        return rt.with_backup_contract(
            {"status": "success", "message": "Abbruch angefordert"},
            "backup.cancel_requested",
            "success",
            {"unit_name": unit_name, "unit_scope": unit_scope},
        )

    job = rt.get_backup_jobs().get(job_id)
    if not job:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract({"status": "error", "message": "Job nicht gefunden"}, "backup.job_not_found", "error"),
        )

    if job.get("status") in ("success", "error", "cancelled"):
        return rt.with_backup_contract(
            {"status": "success", "message": "Job ist bereits abgeschlossen"},
            "backup.job_already_done",
            "info",
        )

    cancel_map = rt.get_backup_job_cancel()
    ev = cancel_map.get(job_id)
    if not ev:
        ev = threading.Event()
        cancel_map[job_id] = ev
    ev.set()
    job["status"] = "cancel_requested"
    job["message"] = "Abbruch angefordert…"
    job["code"] = "backup.cancel_requested"
    job["severity"] = "info"

    try:
        pgid = job.get("pgid")
        if isinstance(pgid, int) and pgid > 1:
            os.killpg(pgid, signal.SIGTERM)
    except Exception:
        pass

    return rt.with_backup_contract({"status": "success", "message": "Abbruch angefordert"}, "backup.cancel_requested", "success")


async def backup_job_evidence_collect(job_id: str):
    """Sammelt Diagnose-Artefakte erneut ein (kein Backup-/Restore-Start)."""
    jid = (job_id or "").strip()
    if not rt.backup_job_id_re().fullmatch(jid):
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {
                    "status": "error",
                    "message": "Ungültige job_id",
                    "evidence": {
                        "evidence_status": "invalid_job_id",
                        "evidence_dir": None,
                        "manifest_path": None,
                        "collected_sources": [],
                        "permission_denied_sources": [],
                        "errors": ["invalid_job_id"],
                    },
                },
                "backup.evidence.invalid_job_id",
                "error",
                {"job_id": jid},
            ),
        )
    manifest, err = rt.run_backup_evidence_collect(jid)
    if err:
        ev = rt.normalize_evidence_api_payload(None, None)
        ev["evidence_status"] = "error"
        ev["errors"] = [err]
        return rt.with_backup_contract(
            {"status": "success", "evidence": ev},
            "backup.evidence.collect_failed",
            "info",
            {"job_id": jid},
        )
    mdir = manifest.get("output_dir") if isinstance(manifest, dict) else None
    mp = Path(str(mdir)) / "manifest.json" if mdir else None
    mp_resolved: Optional[Path] = mp if mp and mp.is_file() else None
    ev = rt.normalize_evidence_api_payload(manifest if isinstance(manifest, dict) else None, mp_resolved)
    if ev.get("permission_denied_sources"):
        return rt.with_backup_contract(
            {"status": "success", "evidence": ev},
            "backup.evidence.ok_with_permissions_denied",
            "info",
            {"job_id": jid},
        )
    return rt.with_backup_contract(
        {"status": "success", "evidence": ev},
        "backup.evidence.ok",
        "success",
        {"job_id": jid},
    )


async def backup_profiles_list_post():
    return rt.backup_profiles_list_payload()


async def backup_profile_preview(request: Request):
    """Read-only: Profilbeschreibung und Zielgroesse, kein Backup-Start."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    prof = str(body.get("profile") or "recommended").strip()
    bd_raw = body.get("backup_dir", "")
    try:
        bd = rt.validate_backup_dir(str(bd_raw))
    except Exception as ve:
        from core.backup_target_service_access import extract_backup_target_diagnosis_id

        det: dict[str, Any] = {"reason": str(ve)}
        btd = extract_backup_target_diagnosis_id(str(ve))
        if btd:
            det["diagnosis_id"] = btd
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": f"Ungültiges Backup-Ziel: {str(ve)}"},
                "backup.path_invalid",
                "error",
                det,
            ),
        )
    tf: Optional[int] = None
    try:
        p = Path(bd)
        if p.is_dir():
            tf = int(shutil.disk_usage(str(p)).free)
    except Exception:
        pass
    preview = build_profile_preview(profile_raw=prof, backup_dir=bd, target_free_bytes=tf)
    return rt.with_backup_contract(
        {"status": "success", "preview": preview},
        "backup.profile_preview",
        "success",
        {"profile": prof, "backup_dir": bd},
    )
