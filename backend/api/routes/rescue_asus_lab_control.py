"""ASUS lab control API — PI-RS-ASUS-LAB-CONTROL-006.

Machine-bound identity, capture prepare/finalize, lab jobs, BitLocker policy (RO).
No BitLocker mutation routes.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from core.rescue_asus_lab_authorization import (
    PROFILE_ID,
    evaluate_disk_fingerprint_gate,
    evaluate_machine_identity_match,
    load_lab_target_profile,
    profile_authorization_hash,
)
from core.rescue_lab_job_contract import build_lab_job, validate_lab_job
from core.rescue_lab_job_store import cancel_job, get_job, put_job
from core.rescue_win11_live_capture import (
    finalize_capture_status,
    generate_win11_run_id,
    validate_run_id,
)

router = APIRouter(tags=["rescue-asus-lab"])

_SEEN_NONCES: set[str] = set()


@router.get("/api/lab/targets")
def lab_targets() -> dict[str, Any]:
    prof = load_lab_target_profile()
    return {
        "targets": [
            {
                "profile_id": prof.get("profile_id"),
                "authorization_scope": prof.get("authorization_scope"),
                "board_name": prof.get("board_name"),
                "bitlocker_mutation": False,
            }
        ]
    }


@router.get("/api/lab/targets/{profile_id}")
def lab_target(profile_id: str) -> dict[str, Any]:
    if profile_id != PROFILE_ID:
        raise HTTPException(status_code=404, detail="unknown_lab_target")
    prof = load_lab_target_profile()
    auth = dict(prof.get("authorization") or {})
    auth["bitlocker_mutation"] = False
    return {**prof, "authorization": auth}


@router.post("/api/lab/targets/{profile_id}/identity-check")
def lab_identity_check(profile_id: str, body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    if profile_id != PROFILE_ID:
        raise HTTPException(status_code=404, detail="unknown_lab_target")
    match = evaluate_machine_identity_match(observed=body)
    disks = body.get("disks") if isinstance(body.get("disks"), list) else None
    disk_gate = evaluate_disk_fingerprint_gate(observed_disks=disks)
    return {**match, "disk_gate": disk_gate}


@router.get("/api/lab/authorization/{profile_id}")
def lab_authorization(profile_id: str) -> dict[str, Any]:
    if profile_id != PROFILE_ID:
        raise HTTPException(status_code=404, detail="unknown_lab_target")
    prof = load_lab_target_profile()
    auth = dict(prof.get("authorization") or {})
    auth["bitlocker_mutation"] = False
    return {
        "profile_id": PROFILE_ID,
        "authorization": auth,
        "authorization_profile_hash": profile_authorization_hash(prof),
        "notice": "FREIGABE GILT NUR FUER ASUS_ROG_GABRIEL_LAB",
    }


@router.get("/api/lab/bitlocker-policy")
def lab_bitlocker_policy() -> dict[str, Any]:
    return {
        "bitlocker_mutation": False,
        "read_only_status_allowed": True,
        "forbidden": [
            "enable",
            "disable",
            "suspend",
            "resume",
            "add_protector",
            "remove_protector",
            "rotate_recovery_key",
        ],
        "routes_for_mutation": [],
    }


@router.post("/api/rescue/win11-capture/prepare")
def win11_capture_prepare(body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    run_id = str(body.get("run_id") or "") or generate_win11_run_id()
    gate = validate_run_id(run_id)
    if not gate["ok"]:
        raise HTTPException(status_code=400, detail=gate["blocked_reason"])
    return {
        "run_id": run_id,
        "setup_logs_label": "SETUP_LOGS",
        "layout": [
            "collector",
            "heartbeats",
            "winpe",
            "panther",
            "rollback",
            "setupdiag",
            "disk-layout",
            "firmware",
            "screenshots",
            "result",
        ],
        "status": "prepared",
        "bitlocker_mutation": False,
    }


@router.post("/api/rescue/win11-capture/finalize")
def win11_capture_finalize(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    run_id = str(body.get("run_id") or "")
    return finalize_capture_status(
        run_id=run_id,
        panther_files=int(body.get("panther_files") or 0),
        rollback_files=int(body.get("rollback_files") or 0),
        heartbeats=int(body.get("heartbeats") or 0),
    )


@router.get("/api/rescue/win11-capture/{run_id}")
def win11_capture_get(run_id: str) -> dict[str, Any]:
    gate = validate_run_id(run_id)
    return {
        "run_id": run_id,
        "run_id_valid": gate["ok"],
        "status": "lookup_client_side_on_stick",
        "hint": "Import SETUP_LOGS/asus-win11/<run_id>/ after physical run",
    }


@router.post("/api/lab/jobs/plan")
def lab_jobs_plan(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Plan-only: validate shape without executing."""
    return {
        "planned": True,
        "action_type": body.get("action_type"),
        "risk_class": body.get("risk_class"),
        "target_profile": PROFILE_ID,
        "bitlocker_mutation": False,
        "notice": "FREIGABE GILT NUR FUER ASUS_ROG_GABRIEL_LAB",
    }


@router.post("/api/lab/jobs")
def lab_jobs_create(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    if body.get("bitlocker_mutation") is True:
        raise HTTPException(status_code=400, detail="bitlocker_mutation_forbidden")
    prof = load_lab_target_profile()
    job = build_lab_job(
        action_type=str(body.get("action_type") or "diagnostic"),
        risk_class=str(body.get("risk_class") or "read_only"),
        target_fingerprint=str(body.get("target_fingerprint") or prof.get("machine_id") or ""),
        requested_by=str(body.get("requested_by") or "operator"),
        authorization_profile_hash=profile_authorization_hash(prof),
        command=body.get("command"),
        parameters=body.get("parameters") if isinstance(body.get("parameters"), dict) else {},
        run_id=body.get("run_id"),
    )
    return put_job(job)


@router.get("/api/lab/jobs/{job_id}")
def lab_jobs_get(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return job


@router.post("/api/lab/jobs/{job_id}/cancel")
def lab_jobs_cancel(job_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    if get_job(job_id) is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    try:
        return cancel_job(job_id, reason=str(body.get("reason") or "operator_cancel"))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/api/lab/jobs/{job_id}/validate")
def lab_jobs_validate(job_id: str, body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    job = body.get("job") if isinstance(body.get("job"), dict) else body
    if str(job.get("job_id") or "") != job_id:
        raise HTTPException(status_code=400, detail="job_id_mismatch")
    observed = body.get("observed_identity") if isinstance(body.get("observed_identity"), dict) else {}
    result = validate_lab_job(job, observed_identity=observed, seen_nonces=_SEEN_NONCES)
    if result.get("ok") and job.get("nonce"):
        _SEEN_NONCES.add(str(job["nonce"]))
        stored = get_job(job_id) or dict(job)
        stored["state"] = "validated"
        put_job(stored)
    elif not result.get("ok"):
        stored = get_job(job_id) or dict(job)
        stored["state"] = "blocked"
        stored["block_reasons"] = result.get("reasons")
        put_job(stored)
    return result
