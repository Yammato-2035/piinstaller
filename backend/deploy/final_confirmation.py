from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from deploy.write_execute import _DEPLOY_WRITE_SESSION_STORE

_DEPLOY_FINAL_CONFIRMATION_STORE: dict[str, dict[str, Any]] = {}
_DEPLOY_FINAL_CONFIRMATION_TTL_SECONDS = 600
_REQUIRED_CONFIRMATIONS = [
    "CONFIRM_ALL_DATA_WILL_BE_DESTROYED",
    "CONFIRM_TARGET_DEVICE_AGAIN",
    "CONFIRM_NO_SYSTEM_DISK",
    "CONFIRM_NO_WINDOWS_DUALBOOT",
    "CONFIRM_IMAGE_AND_PROFILE_MATCH",
    "CONFIRM_FINAL_DEPLOY_DRYRUN",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload or {}, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_target_snapshot(write_execute_result: dict[str, Any], inspect_result: dict[str, Any]) -> dict[str, Any]:
    target_device = str(write_execute_result.get("target_device") or "")
    storage = inspect_result.get("storage") if isinstance(inspect_result, dict) else {}
    classified = storage.get("devices_classified") if isinstance(storage, dict) else []
    disk = None
    if isinstance(classified, list):
        for row in classified:
            if isinstance(row, dict) and str(row.get("device") or "") == target_device:
                disk = row
                break
    detected = (inspect_result.get("filesystems") or {}).get("detected") if isinstance(inspect_result, dict) else {}
    fs_types: list[str] = []
    part_count = 0
    mount_summary: list[str] = []
    if isinstance(disk, dict):
        partitions = disk.get("partitions") if isinstance(disk.get("partitions"), list) else []
        part_count = len(partitions)
        for p in partitions:
            if not isinstance(p, dict):
                continue
            dev = str(p.get("device") or "")
            if isinstance(detected, dict):
                meta = detected.get(dev)
                if isinstance(meta, dict) and str(meta.get("type") or ""):
                    fs_types.append(str(meta.get("type")))
            mp = str(p.get("mountpoint") or "")
            if mp:
                mount_summary.append(f"{dev}:{mp}")
    fs_types = sorted(list(dict.fromkeys(fs_types)))
    mount_summary = sorted(list(dict.fromkeys(mount_summary)))
    device_summary = {
        "size": (disk or {}).get("size"),
        "transport": (disk or {}).get("transport"),
        "removable": (disk or {}).get("removable"),
        "model": (disk or {}).get("model"),
        "vendor": (disk or {}).get("vendor"),
        "filesystem_types": fs_types,
        "partition_count": part_count,
        "mount_summary": mount_summary,
    }
    snap_data = {"target_device": target_device, "device_summary": device_summary}
    fingerprint = _hash_payload(snap_data)
    return {
        "snapshot_id": secrets.token_hex(8),
        "target_device": target_device or None,
        "device_summary": device_summary,
        "fingerprint": fingerprint,
        "warnings": [],
        "errors": [],
    }


def _confirmations_valid(confirmations: list[Any]) -> tuple[bool, str]:
    got = [str(x) for x in confirmations]
    req = list(_REQUIRED_CONFIRMATIONS)
    if len(set(got)) != len(got):
        return False, "DEPLOY_FINAL_CONFIRMATION_CONFIRMATION_INVALID"
    if any(x not in req for x in got):
        return False, "DEPLOY_FINAL_CONFIRMATION_CONFIRMATION_INVALID"
    if any(x not in got for x in req):
        return False, "DEPLOY_FINAL_CONFIRMATION_CONFIRMATION_INVALID"
    return True, ""


def _write_plan_still_valid(write_plan: dict[str, Any]) -> bool:
    st = str(write_plan.get("plan_status") or "")
    if st not in {"ok", "review_required"}:
        return False
    if write_plan.get("blocked_reasons"):
        return False
    return True


def create_final_confirmation_session(request: dict[str, Any]) -> dict[str, Any]:
    write_execute_result = request.get("write_execute_result") if isinstance(request.get("write_execute_result"), dict) else {}
    write_plan = request.get("write_plan") if isinstance(request.get("write_plan"), dict) else {}
    inspect_result = request.get("inspect_result") if isinstance(request.get("inspect_result"), dict) else {}
    confirmations = request.get("confirmations") if isinstance(request.get("confirmations"), list) else []
    out = {
        "code": "DEPLOY_FINAL_CONFIRMATION_INVALID",
        "final_confirmation_id": None,
        "confirmation_token": None,
        "target_snapshot": {},
        "expires_at": None,
        "warnings": [],
        "errors": [],
    }
    if str(write_execute_result.get("code") or "") != "DEPLOY_WRITE_EXECUTE_READY":
        out["errors"].append("DEPLOY_FINAL_CONFIRMATION_INVALID")
        return out
    if not isinstance(write_execute_result.get("simulated_execution"), list) or not write_execute_result.get("simulated_execution"):
        out["errors"].append("DEPLOY_FINAL_CONFIRMATION_INVALID")
        return out
    target_device = str(write_execute_result.get("target_device") or "")
    selected_profile = str(write_execute_result.get("selected_profile") or "")
    image_path = str(write_execute_result.get("image_path") or "")
    write_session_id = str(write_execute_result.get("write_session_id") or "")
    if not target_device or not selected_profile or not image_path or not write_session_id:
        out["errors"].append("DEPLOY_FINAL_CONFIRMATION_INVALID")
        return out
    if not _write_plan_still_valid(write_plan):
        out["code"] = "DEPLOY_FINAL_CONFIRMATION_BLOCKED"
        out["errors"].append("DEPLOY_FINAL_CONFIRMATION_BLOCKED")
        return out
    ok_conf, conf_err = _confirmations_valid(confirmations)
    if not ok_conf:
        out["code"] = conf_err
        out["errors"].append(conf_err)
        return out
    snapshot = build_target_snapshot(write_execute_result, inspect_result)
    fid = secrets.token_hex(8)
    token = secrets.token_urlsafe(24)
    created = _now()
    expires = created + timedelta(seconds=_DEPLOY_FINAL_CONFIRMATION_TTL_SECONDS)
    _DEPLOY_FINAL_CONFIRMATION_STORE[fid] = {
        "final_confirmation_id": fid,
        "confirmation_token": token,
        "target_snapshot_fingerprint": str(snapshot.get("fingerprint") or ""),
        "write_session_id": write_session_id,
        "target_device": target_device,
        "selected_profile": selected_profile,
        "image_path": image_path,
        "created_at": created.isoformat(),
        "expires_at": expires.isoformat(),
        "used": False,
    }
    out["code"] = "DEPLOY_FINAL_CONFIRMATION_CREATED"
    out["final_confirmation_id"] = fid
    out["confirmation_token"] = token
    out["target_snapshot"] = snapshot
    out["expires_at"] = expires.isoformat()
    return out


def check_final_confirmation_dryrun(request: dict[str, Any]) -> dict[str, Any]:
    fid = str(request.get("final_confirmation_id") or "")
    token = str(request.get("confirmation_token") or "")
    target_snapshot = request.get("target_snapshot") if isinstance(request.get("target_snapshot"), dict) else {}
    out = {
        "code": "DEPLOY_FINAL_CONFIRMATION_BLOCKED",
        "final_confirmation_id": fid or None,
        "target_snapshot": target_snapshot if isinstance(target_snapshot, dict) else {},
        "risk_summary": [],
        "destructive_operations": [],
        "warnings": [],
        "errors": [],
    }
    sess = _DEPLOY_FINAL_CONFIRMATION_STORE.get(fid)
    if not sess:
        out["code"] = "DEPLOY_FINAL_CONFIRMATION_NOT_FOUND"
        out["errors"].append("DEPLOY_FINAL_CONFIRMATION_NOT_FOUND")
        return out
    if token != str(sess.get("confirmation_token") or ""):
        out["code"] = "DEPLOY_FINAL_CONFIRMATION_TOKEN_INVALID"
        out["errors"].append("DEPLOY_FINAL_CONFIRMATION_TOKEN_INVALID")
        return out
    try:
        expires = datetime.fromisoformat(str(sess.get("expires_at") or ""))
    except Exception:
        expires = _now() - timedelta(seconds=1)
    if _now() >= expires:
        out["code"] = "DEPLOY_FINAL_CONFIRMATION_SESSION_EXPIRED"
        out["errors"].append("DEPLOY_FINAL_CONFIRMATION_SESSION_EXPIRED")
        return out
    fp = str(target_snapshot.get("fingerprint") or "")
    if not fp or fp != str(sess.get("target_snapshot_fingerprint") or ""):
        out["code"] = "DEPLOY_FINAL_CONFIRMATION_SNAPSHOT_MISMATCH"
        out["errors"].append("DEPLOY_FINAL_CONFIRMATION_SNAPSHOT_MISMATCH")
        return out
    snap_target = str(target_snapshot.get("target_device") or "")
    if snap_target != str(sess.get("target_device") or ""):
        out["code"] = "DEPLOY_FINAL_CONFIRMATION_TARGET_MISMATCH"
        out["errors"].append("DEPLOY_FINAL_CONFIRMATION_TARGET_MISMATCH")
        return out
    wsid = str(sess.get("write_session_id") or "")
    ws = _DEPLOY_WRITE_SESSION_STORE.get(wsid)
    if not ws:
        out["code"] = "DEPLOY_FINAL_CONFIRMATION_BLOCKED"
        out["errors"].append("DEPLOY_FINAL_CONFIRMATION_BLOCKED")
        return out
    out["code"] = "DEPLOY_FINAL_CONFIRMATION_READY"
    out["target_snapshot"] = target_snapshot
    out["risk_summary"] = ["DEPLOY_WRITE_RISK_DATA_LOSS", "DEPLOY_WRITE_RISK_WRONG_TARGET"]
    out["destructive_operations"] = [
        "DEPLOY_EXEC_WRITE_IMAGE",
        "DEPLOY_EXEC_EXPAND_FILESYSTEM",
        "DEPLOY_EXEC_INSTALL_SETUPHELPER",
    ]
    return out


def get_final_confirmation_bindings(final_confirmation_id: str) -> dict[str, Any] | None:
    """Nach bestandenem check_final_confirmation_dryrun: gebundene Pfade aus der Session (ohne Token)."""
    sess = _DEPLOY_FINAL_CONFIRMATION_STORE.get(str(final_confirmation_id or ""))
    if not sess:
        return None
    return {
        "image_path": str(sess.get("image_path") or ""),
        "target_device": str(sess.get("target_device") or ""),
    }
