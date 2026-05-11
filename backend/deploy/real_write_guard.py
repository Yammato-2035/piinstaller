from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_DEPLOY_REAL_WRITE_GUARD_STORE: dict[str, dict[str, Any]] = {}
_DEPLOY_REAL_WRITE_GUARD_TTL_SECONDS = 300

_NETWORK_TRANSPORTS = {"iscsi", "rbd", "nbd", "nfs", "network"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload or {}, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_size_bytes(size_val: Any) -> int | None:
    if size_val is None:
        return None
    if isinstance(size_val, (int, float)):
        return int(size_val)
    s = str(size_val).strip().upper()
    if not s:
        return None
    mult = 1
    for suffix, m in (("K", 1024), ("M", 1024**2), ("G", 1024**3), ("T", 1024**4)):
        if s.endswith(suffix):
            s = s[: -len(suffix)].strip()
            mult = m
            break
    if s.endswith("B"):
        s = s[:-1].strip()
    try:
        return int(float(s) * mult)
    except Exception:
        return None


def _safety_target(safety_summary: dict[str, Any], device: str) -> dict[str, Any] | None:
    targets = safety_summary.get("targets")
    if not isinstance(targets, list):
        return None
    for t in targets:
        if isinstance(t, dict) and str(t.get("device") or "") == device:
            return t
    return None


def _snapshot_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_device": snapshot.get("target_device"),
        "device_path_resolved": snapshot.get("device_path_resolved"),
        "device_summary": snapshot.get("device_summary") or {},
        "mount_state": snapshot.get("mount_state") or {},
        "filesystem_summary": snapshot.get("filesystem_summary") or {},
        "partition_summary": snapshot.get("partition_summary") or {},
        "transport": snapshot.get("transport"),
        "removable": snapshot.get("removable"),
        "size_bytes": snapshot.get("size_bytes"),
    }


def build_real_write_snapshot(target_device: str, inspect_result: dict[str, Any], safety_summary: dict[str, Any]) -> dict[str, Any]:
    storage = inspect_result.get("storage") if isinstance(inspect_result, dict) else {}
    disks = storage.get("devices_classified") if isinstance(storage, dict) else []
    disk = None
    if isinstance(disks, list):
        for d in disks:
            if isinstance(d, dict) and str(d.get("device") or "") == target_device:
                disk = d
                break
    partitions = disk.get("partitions") if isinstance(disk, dict) and isinstance(disk.get("partitions"), list) else []
    detected = (inspect_result.get("filesystems") or {}).get("detected") if isinstance(inspect_result, dict) else {}
    fs_types: list[str] = []
    mountpoints: list[str] = []
    part_devices: list[str] = []
    for p in partitions:
        if not isinstance(p, dict):
            continue
        dev = str(p.get("device") or "")
        if dev:
            part_devices.append(dev)
        mp = str(p.get("mountpoint") or "")
        if mp:
            mountpoints.append(mp)
        if isinstance(detected, dict):
            meta = detected.get(dev)
            if isinstance(meta, dict) and str(meta.get("type") or ""):
                fs_types.append(str(meta.get("type")))
    fs_types = sorted(list(dict.fromkeys(fs_types)))
    mountpoints = sorted(list(dict.fromkeys(mountpoints)))
    resolved = str(Path(target_device).resolve(strict=False)) if target_device else ""
    safety = _safety_target(safety_summary if isinstance(safety_summary, dict) else {}, target_device)
    device_summary = {
        "model": (disk or {}).get("model"),
        "vendor": (disk or {}).get("vendor"),
        "safety_reason_code": str((safety or {}).get("reason_code") or ""),
        "write_allowed": bool((safety or {}).get("write_allowed")),
        "readonly": bool((disk or {}).get("read_only") or (disk or {}).get("ro")),
    }
    snapshot = {
        "snapshot_id": secrets.token_hex(8),
        "target_device": target_device or None,
        "device_path_resolved": resolved or None,
        "device_summary": device_summary,
        "mount_state": {"mounted": bool(mountpoints), "mountpoints": mountpoints},
        "filesystem_summary": {"types": fs_types, "count": len(fs_types)},
        "partition_summary": {"count": len(partitions), "devices": part_devices},
        "transport": (disk or {}).get("transport"),
        "removable": (disk or {}).get("removable"),
        "size_bytes": _parse_size_bytes((disk or {}).get("size")),
        "warnings": [],
        "errors": [],
    }
    snapshot["fingerprint"] = _hash_payload(_snapshot_payload(snapshot))
    return snapshot


def _validate_harness_proof(write_harness_result: dict[str, Any]) -> bool:
    if not isinstance(write_harness_result, dict):
        return False
    execute_code = str(write_harness_result.get("execute_code") or write_harness_result.get("code") or "")
    if execute_code != "DEPLOY_WRITE_HARNESS_COMPLETED":
        return False
    if not bool(write_harness_result.get("sha256_matches")):
        return False
    if str(write_harness_result.get("single_use_code") or "") != "DEPLOY_WRITE_HARNESS_SESSION_ALREADY_USED":
        return False
    if bool(write_harness_result.get("host_changes_detected")):
        return False
    return True


def _collect_blocks(snapshot: dict[str, Any], inspect_result: dict[str, Any], safety_summary: dict[str, Any], harness_ok: bool) -> list[str]:
    blocks: list[str] = []
    dev = str(snapshot.get("target_device") or "")
    resolved = str(snapshot.get("device_path_resolved") or "")

    # High-priority hard device class blocks.
    if dev.startswith("/dev/mapper/") or resolved.startswith("/dev/mapper/"):
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_LVM")
    if dev.startswith("/dev/loop") or resolved.startswith("/dev/loop"):
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_LOOP")
    if dev.startswith("/dev/md") or "linux_raid_member" in set((snapshot.get("filesystem_summary") or {}).get("types") or []):
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_RAID")
    transport = str(snapshot.get("transport") or "").lower()
    if transport in _NETWORK_TRANSPORTS or dev.startswith("/dev/nbd"):
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_NETWORK_DEVICE")

    cls = inspect_result.get("classification") if isinstance(inspect_result, dict) else {}
    system_type = str((cls or {}).get("system_type") or "")
    if system_type == "WINDOWS":
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_WINDOWS")
    if system_type == "DUALBOOT":
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT")
    if system_type in {"UNKNOWN", "PARTIAL_SYSTEM"}:
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN")
    if system_type == "BROKEN_BOOT":
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN")

    target = _safety_target(safety_summary if isinstance(safety_summary, dict) else {}, str(snapshot.get("target_device") or ""))
    reason = str((target or {}).get("reason_code") or "")
    if reason == "SAFETY_SYSTEM_DISK":
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_SYSTEM_DISK")
    if reason == "SAFETY_LIVE_SYSTEM":
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_LIVE_SYSTEM")
    if reason == "SAFETY_WINDOWS_DETECTED":
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_WINDOWS")
    if reason == "SAFETY_DUALBOOT":
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT")
    if reason == "SAFETY_UNKNOWN_DEVICE":
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN")
    if not bool((target or {}).get("write_allowed")):
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN")

    if bool((snapshot.get("mount_state") or {}).get("mounted")):
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_MOUNTED")
    if bool(snapshot.get("removable")) is False:
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_NON_REMOVABLE")
    if bool((snapshot.get("device_summary") or {}).get("readonly")):
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_READONLY")

    if not harness_ok:
        blocks.append("DEPLOY_REAL_WRITE_BLOCKED_NO_HARNESS_PROOF")
    return list(dict.fromkeys(blocks))


def create_real_write_guard_session(request: dict[str, Any]) -> dict[str, Any]:
    final_confirmation_result = request.get("final_confirmation_result") if isinstance(request.get("final_confirmation_result"), dict) else {}
    write_session_result = request.get("write_session_result") if isinstance(request.get("write_session_result"), dict) else {}
    write_execute_result = request.get("write_execute_result") if isinstance(request.get("write_execute_result"), dict) else {}
    write_plan = request.get("write_plan") if isinstance(request.get("write_plan"), dict) else {}
    inspect_result = request.get("inspect_result") if isinstance(request.get("inspect_result"), dict) else {}
    safety_summary = request.get("safety_summary") if isinstance(request.get("safety_summary"), dict) else {}
    write_harness_result = request.get("write_harness_result") if isinstance(request.get("write_harness_result"), dict) else {}

    out = {
        "code": "DEPLOY_REAL_WRITE_GUARD_INVALID",
        "real_write_guard_id": None,
        "confirmation_token": None,
        "snapshot": {},
        "expires_at": None,
        "warnings": [],
        "errors": [],
    }

    if str(final_confirmation_result.get("code") or "") != "DEPLOY_FINAL_CONFIRMATION_READY":
        out["errors"].append("DEPLOY_REAL_WRITE_GUARD_INVALID")
        return out
    if str(write_session_result.get("code") or "") != "DEPLOY_WRITE_SESSION_CREATED":
        out["errors"].append("DEPLOY_REAL_WRITE_GUARD_INVALID")
        return out
    if str(write_execute_result.get("code") or "") != "DEPLOY_WRITE_EXECUTE_READY":
        out["errors"].append("DEPLOY_REAL_WRITE_GUARD_INVALID")
        return out
    if str(write_plan.get("plan_status") or "") not in {"ok", "review_required"} or bool(write_plan.get("blocked_reasons")):
        out["code"] = "DEPLOY_REAL_WRITE_GUARD_BLOCKED"
        out["errors"].append("DEPLOY_REAL_WRITE_GUARD_BLOCKED")
        return out

    target_device = str(write_execute_result.get("target_device") or "")
    selected_profile = str(write_execute_result.get("selected_profile") or "")
    image_path = str(write_execute_result.get("image_path") or "")
    if not target_device or not selected_profile or not image_path:
        out["errors"].append("DEPLOY_REAL_WRITE_GUARD_INVALID")
        return out

    snapshot = build_real_write_snapshot(target_device, inspect_result, safety_summary)
    harness_ok = _validate_harness_proof(write_harness_result)
    blocks = _collect_blocks(snapshot, inspect_result, safety_summary, harness_ok)
    if blocks:
        out["code"] = blocks[0]
        out["errors"] = blocks
        out["snapshot"] = snapshot
        return out

    gid = secrets.token_hex(8)
    token = secrets.token_urlsafe(24)
    created = _now()
    expires = created + timedelta(seconds=_DEPLOY_REAL_WRITE_GUARD_TTL_SECONDS)
    _DEPLOY_REAL_WRITE_GUARD_STORE[gid] = {
        "real_write_guard_id": gid,
        "confirmation_token": token,
        "target_device": target_device,
        "image_path": image_path,
        "selected_profile": selected_profile,
        "snapshot_fingerprint": str(snapshot.get("fingerprint") or ""),
        "snapshot_payload_hash": _hash_payload(_snapshot_payload(snapshot)),
        "harness_proof_hash": _hash_payload(write_harness_result),
        "created_at": created.isoformat(),
        "expires_at": expires.isoformat(),
        "used": False,
    }
    out["code"] = "DEPLOY_REAL_WRITE_GUARD_SESSION_CREATED"
    out["real_write_guard_id"] = gid
    out["confirmation_token"] = token
    out["snapshot"] = snapshot
    out["expires_at"] = expires.isoformat()
    return out


def _would_execute_steps() -> list[dict[str, Any]]:
    codes = [
        "DEPLOY_REAL_WRITE_UNMOUNT",
        "DEPLOY_REAL_WRITE_WRITE_IMAGE",
        "DEPLOY_REAL_WRITE_SYNC",
        "DEPLOY_REAL_WRITE_VERIFY",
        "DEPLOY_REAL_WRITE_EXPAND",
        "DEPLOY_REAL_WRITE_FINALIZE",
    ]
    return [{"code": c, "would_write": True, "auto_allowed": False, "requires_confirmation": True} for c in codes]


def check_real_write_guard(request: dict[str, Any]) -> dict[str, Any]:
    gid = str(request.get("real_write_guard_id") or "")
    token = str(request.get("confirmation_token") or "")
    snapshot = request.get("snapshot") if isinstance(request.get("snapshot"), dict) else {}
    inspect_result = request.get("inspect_result") if isinstance(request.get("inspect_result"), dict) else {}
    safety_summary = request.get("safety_summary") if isinstance(request.get("safety_summary"), dict) else {}
    write_plan = request.get("write_plan") if isinstance(request.get("write_plan"), dict) else {}
    write_harness_result = request.get("write_harness_result") if isinstance(request.get("write_harness_result"), dict) else {}

    out = {
        "code": "DEPLOY_REAL_WRITE_GUARD_BLOCKED",
        "target": {"target_device": snapshot.get("target_device")},
        "snapshot": snapshot,
        "guard": {"allowed": False},
        "would_execute_steps": [],
        "warnings": [],
        "errors": [],
    }

    sess = _DEPLOY_REAL_WRITE_GUARD_STORE.get(gid)
    if not sess:
        out["code"] = "DEPLOY_REAL_WRITE_GUARD_NOT_FOUND"
        out["errors"].append("DEPLOY_REAL_WRITE_GUARD_NOT_FOUND")
        return out
    if bool(sess.get("used")):
        out["code"] = "DEPLOY_REAL_WRITE_GUARD_BLOCKED"
        out["errors"].append("DEPLOY_REAL_WRITE_GUARD_BLOCKED")
        return out
    if token != str(sess.get("confirmation_token") or ""):
        out["code"] = "DEPLOY_REAL_WRITE_GUARD_TOKEN_INVALID"
        out["errors"].append("DEPLOY_REAL_WRITE_GUARD_TOKEN_INVALID")
        return out
    try:
        expires = datetime.fromisoformat(str(sess.get("expires_at") or ""))
    except Exception:
        expires = _now() - timedelta(seconds=1)
    if _now() >= expires:
        out["code"] = "DEPLOY_REAL_WRITE_GUARD_SESSION_EXPIRED"
        out["errors"].append("DEPLOY_REAL_WRITE_GUARD_SESSION_EXPIRED")
        return out

    # Single-use must be consumed at check entry.
    sess["used"] = True

    snap_fp = str(snapshot.get("fingerprint") or "")
    if not snap_fp or snap_fp != str(sess.get("snapshot_fingerprint") or ""):
        out["code"] = "DEPLOY_REAL_WRITE_BLOCKED_FINGERPRINT_MISMATCH"
        out["errors"].append("DEPLOY_REAL_WRITE_BLOCKED_FINGERPRINT_MISMATCH")
        return out
    if _hash_payload(_snapshot_payload(snapshot)) != str(sess.get("snapshot_payload_hash") or ""):
        out["code"] = "DEPLOY_REAL_WRITE_BLOCKED_SNAPSHOT_CHANGED"
        out["errors"].append("DEPLOY_REAL_WRITE_BLOCKED_SNAPSHOT_CHANGED")
        return out
    if str(snapshot.get("target_device") or "") != str(sess.get("target_device") or ""):
        out["code"] = "DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN"
        out["errors"].append("DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN")
        return out

    if str(write_plan.get("plan_status") or "") not in {"ok", "review_required"} or bool(write_plan.get("blocked_reasons")):
        out["code"] = "DEPLOY_REAL_WRITE_GUARD_BLOCKED"
        out["errors"].append("DEPLOY_REAL_WRITE_GUARD_BLOCKED")
        return out

    harness_ok = _validate_harness_proof(write_harness_result)
    blocks = _collect_blocks(snapshot, inspect_result, safety_summary, harness_ok)
    if blocks:
        out["code"] = blocks[0]
        out["errors"] = blocks
        return out

    out["code"] = "DEPLOY_REAL_WRITE_READY"
    out["target"] = {"target_device": str(sess.get("target_device") or ""), "selected_profile": str(sess.get("selected_profile") or ""), "image_path": str(sess.get("image_path") or "")}
    out["snapshot"] = snapshot
    out["guard"] = {"allowed": True, "harness_proof_bound": True}
    out["would_execute_steps"] = _would_execute_steps()
    return out
