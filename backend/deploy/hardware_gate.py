from __future__ import annotations

import hashlib
import json
import secrets
from typing import Any

_LINUX_FS = frozenset({"ext2", "ext3", "ext4", "xfs", "btrfs"})
_GLOBAL_REVIEW_SYSTEM_TYPES = frozenset({"WINDOWS", "DUALBOOT", "UNKNOWN", "PARTIAL_SYSTEM", "BROKEN_BOOT"})


def _hash_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload or {}, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _safety_target(safety_summary: dict[str, Any], device: str) -> dict[str, Any] | None:
    targets = safety_summary.get("targets")
    if not isinstance(targets, list):
        return None
    for t in targets:
        if isinstance(t, dict) and str(t.get("device") or "") == device:
            return t
    return None


def _parse_size_bytes(size_val: Any) -> int | None:
    if isinstance(size_val, (int, float)):
        return int(size_val)
    if size_val is None:
        return None
    s = str(size_val).strip().upper().replace("IB", "B")
    mult = 1
    for suf, m in (("KB", 1024), ("MB", 1024**2), ("GB", 1024**3), ("TB", 1024**4)):
        if s.endswith(suf):
            s = s[: -len(suf)].strip()
            mult = m
            break
    if s.endswith("B"):
        s = s[:-1].strip()
    try:
        return int(float(s) * mult)
    except Exception:
        return None


def _parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if int(value) in {0, 1}:
            return bool(int(value))
        return None
    s = str(value or "").strip().lower()
    if s in {"1", "true", "yes", "on"}:
        return True
    if s in {"0", "false", "no", "off"}:
        return False
    return None


def _parse_int(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _iter_nodes(nodes: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        out.append(node)
        parts = node.get("partitions")
        if isinstance(parts, list):
            out.extend(_iter_nodes(parts))
    return out


def _find_target_disk(storage: dict[str, Any], target_device: str) -> dict[str, Any] | None:
    classified = storage.get("devices_classified")
    devices_classified = classified if isinstance(classified, list) else []
    devices_raw = storage.get("devices_raw")
    raw_list = devices_raw if isinstance(devices_raw, list) else []

    classified_disk = None
    classified_target_part = None
    for d in devices_classified:
        if not isinstance(d, dict):
            continue
        if str(d.get("device") or "") == target_device:
            classified_disk = d
            break
        for p in _iter_nodes(d.get("partitions") if isinstance(d.get("partitions"), list) else []):
            if str(p.get("device") or "") == target_device:
                classified_disk = d
                classified_target_part = p
                break
        if classified_disk is not None:
            break

    raw_disk = None
    raw_target_part = None
    for d in raw_list:
        if not isinstance(d, dict):
            continue
        if str(d.get("device") or "") == target_device:
            raw_disk = d
            break
        for p in _iter_nodes(d.get("partitions") if isinstance(d.get("partitions"), list) else []):
            if str(p.get("device") or "") == target_device:
                raw_disk = d
                raw_target_part = p
                break
        if raw_disk is not None:
            break

    if classified_disk is None and raw_disk is None:
        return None

    merged: dict[str, Any] = {}
    if isinstance(raw_disk, dict):
        merged.update(raw_disk)
    if isinstance(classified_disk, dict):
        merged.update(classified_disk)

    if not isinstance(merged.get("partitions"), list):
        merged["partitions"] = []
    merged["target_device"] = target_device
    merged["target_partition"] = classified_target_part or raw_target_part
    return merged


def _normalize_fs_types(inspect_result: dict[str, Any], partitions: list[dict[str, Any]]) -> set[str]:
    fs_types: set[str] = set()
    detected = (inspect_result.get("filesystems") or {}).get("detected") if isinstance(inspect_result, dict) else {}
    if isinstance(detected, dict):
        for p in partitions:
            if not isinstance(p, dict):
                continue
            meta = detected.get(str(p.get("device") or ""))
            if isinstance(meta, dict):
                t = str(meta.get("type") or "")
                if t:
                    fs_types.add(t.lower())
    for p in partitions:
        if not isinstance(p, dict):
            continue
        t = str(p.get("fstype") or "")
        if t:
            fs_types.add(t.lower())
    return fs_types


def validate_test_device(target_device: str, inspect_result: dict[str, Any], safety_summary: dict[str, Any]) -> dict[str, Any]:
    storage = inspect_result.get("storage") if isinstance(inspect_result, dict) else {}
    disk = _find_target_disk(storage if isinstance(storage, dict) else {}, target_device)
    reasons: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    review_required = False
    if not isinstance(disk, dict):
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN")
        return {
            "eligible": False,
            "review_required": False,
            "risk_level": "high",
            "device_class": "blocked_device",
            "reasons": reasons,
            "warnings": warnings,
            "errors": errors,
            "transport": None,
            "removable": None,
            "size_bytes": None,
            "mounted": None,
        }

    target_partition = disk.get("target_partition") if isinstance(disk.get("target_partition"), dict) else {}
    transport = str(disk.get("transport") or target_partition.get("transport") or "").lower()
    removable = _parse_bool(disk.get("removable"))
    if removable is None:
        removable = _parse_bool(target_partition.get("removable"))
    size_bytes = _parse_size_bytes(disk.get("size"))
    if size_bytes is None:
        size_bytes = _parse_size_bytes(target_partition.get("size"))
    partitions = disk.get("partitions") if isinstance(disk.get("partitions"), list) else []
    mounted = any(bool((p or {}).get("mountpoint")) for p in partitions if isinstance(p, dict))
    if isinstance(target_partition, dict) and target_partition.get("mountpoint"):
        mounted = True
    ro_val = _parse_bool(disk.get("read_only"))
    if ro_val is None:
        ro_val = _parse_bool(disk.get("ro"))
    if ro_val is None:
        ro_val = _parse_bool(target_partition.get("read_only"))
    if ro_val is None:
        ro_val = _parse_bool(target_partition.get("ro"))
    readonly = bool(ro_val)
    dev = str(disk.get("device") or "")
    target_dev = str(target_partition.get("device") or target_device)
    fs_types = _normalize_fs_types(inspect_result if isinstance(inspect_result, dict) else {}, partitions)
    if isinstance(target_partition, dict):
        target_fs = str(target_partition.get("fstype") or "").lower()
        if target_fs:
            fs_types.add(target_fs)
    has_ntfs = "ntfs" in fs_types
    has_linux_fs = bool(fs_types & _LINUX_FS)

    if removable is False:
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_NON_REMOVABLE")
    if removable is None:
        warnings.append("DEPLOY_HARDWARE_GATE_WARN_REMOVABLE_UNVERIFIED")
    if transport and transport not in {"usb", "sdcard"}:
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN")
    if not transport:
        warnings.append("DEPLOY_HARDWARE_GATE_WARN_TRANSPORT_UNVERIFIED")
    if mounted:
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_MOUNTED")
    if readonly:
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_READONLY")
    if dev.startswith("/dev/mapper/"):
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_LVM")
    if dev.startswith("/dev/md"):
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_RAID")
    if dev.startswith("/dev/loop"):
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_LOOP")
    if "linux_raid_member" in fs_types:
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_RAID")
    if has_ntfs and has_linux_fs:
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT")
    elif has_ntfs and not has_linux_fs:
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_WINDOWS")

    tgt = _safety_target(safety_summary if isinstance(safety_summary, dict) else {}, target_device)
    rc = str((tgt or {}).get("reason_code") or "")
    if rc == "SAFETY_SYSTEM_DISK":
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_SYSTEM_DISK")
    if rc == "SAFETY_LIVE_SYSTEM":
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_LIVE_SYSTEM")
    if rc == "SAFETY_WINDOWS_DETECTED":
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_WINDOWS")
    if rc in {"SAFETY_DUALBOOT", "SAFETY_DUALBOOT_PRESENT"}:
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT")
    if rc == "SAFETY_UNKNOWN_DEVICE":
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN")
    if tgt and not bool((tgt or {}).get("write_allowed")) and rc not in {
        "SAFETY_SYSTEM_DISK",
        "SAFETY_LIVE_SYSTEM",
        "SAFETY_WINDOWS_DETECTED",
        "SAFETY_DUALBOOT",
        "SAFETY_DUALBOOT_PRESENT",
        "SAFETY_UNKNOWN_DEVICE",
    }:
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN")

    if size_bytes is None:
        warnings.append("DEPLOY_HARDWARE_GATE_WARN_SIZE_UNVERIFIED")
    elif size_bytes < 4 * 1024**3 or size_bytes > 2 * 1024**4:
        reasons.append("DEPLOY_REAL_WRITE_BLOCKED_UNKNOWN")

    rotational = _parse_int(disk.get("rotational"))
    if rotational is None:
        rotational = _parse_int(target_partition.get("rotational"))
    model = str(disk.get("model") or target_partition.get("model") or "").lower()
    if dev.startswith("/dev/mmcblk") or target_dev.startswith("/dev/mmcblk") or transport == "sdcard":
        device_class = "sd_card"
    elif transport == "usb":
        if rotational == 1:
            device_class = "usb_hdd"
        elif any(x in model for x in ("flash", "stick", "thumb", "intenso", "sandisk", "kingston")):
            device_class = "usb_flash"
        else:
            device_class = "usb_ssd"
    else:
        device_class = "unknown_test_media"

    cls = inspect_result.get("classification") if isinstance(inspect_result, dict) else {}
    system_type = str((cls or {}).get("system_type") or "")
    if system_type in _GLOBAL_REVIEW_SYSTEM_TYPES:
        warnings.append(f"DEPLOY_HARDWARE_GATE_HOST_{system_type}_CONTEXT")

    eligible = not reasons
    if not eligible:
        device_class = "blocked_device"
    risk = "high"
    if eligible and review_required:
        risk = "medium"
    elif eligible:
        risk = "low"
    return {
        "eligible": eligible,
        "review_required": review_required,
        "risk_level": risk,
        "device_class": device_class,
        "reasons": list(dict.fromkeys(reasons)),
        "warnings": warnings,
        "errors": errors,
        "transport": transport or None,
        "removable": removable,
        "size_bytes": size_bytes,
        "mounted": mounted,
        "target_device_resolved": target_dev or None,
        "filesystem_types": sorted(fs_types),
        "partition_count": len(partitions),
    }


def build_hardware_gate_report(request: dict[str, Any]) -> dict[str, Any]:
    inspect_result = request.get("inspect_result") if isinstance(request.get("inspect_result"), dict) else {}
    safety_summary = request.get("safety_summary") if isinstance(request.get("safety_summary"), dict) else {}
    target_device = str(request.get("target_device") or "")
    harness = request.get("write_harness_result") if isinstance(request.get("write_harness_result"), dict) else {}
    final_confirmation = request.get("final_confirmation_result") if isinstance(request.get("final_confirmation_result"), dict) else {}
    real_guard = request.get("real_write_guard_result") if isinstance(request.get("real_write_guard_result"), dict) else {}
    v = validate_test_device(target_device, inspect_result, safety_summary)
    blocked = list(v.get("reasons") or [])
    if str(harness.get("execute_code") or harness.get("code") or "") != "DEPLOY_WRITE_HARNESS_COMPLETED":
        blocked.append("DEPLOY_REAL_WRITE_BLOCKED_NO_HARNESS_PROOF")
    if str(final_confirmation.get("code") or "") != "DEPLOY_FINAL_CONFIRMATION_READY":
        blocked.append("DEPLOY_REAL_WRITE_GUARD_INVALID")
    if str(real_guard.get("code") or "") not in {"DEPLOY_REAL_WRITE_READY", "DEPLOY_REAL_WRITE_GUARD_SESSION_CREATED"}:
        blocked.append("DEPLOY_REAL_WRITE_GUARD_BLOCKED")
    blocked = list(dict.fromkeys(blocked))
    readiness = "blocked"
    if not blocked and bool(v.get("eligible")):
        readiness = "review_required" if bool(v.get("review_required")) else "test_ready"
    return {
        "report_status": "ok" if readiness == "test_ready" else ("review_required" if readiness == "review_required" else "blocked"),
        "readiness_level": readiness,
        "eligible": bool(v.get("eligible")),
        "device_class": v.get("device_class"),
        "removable": v.get("removable"),
        "transport": v.get("transport"),
        "size_bytes": v.get("size_bytes"),
        "target": {"target_device": target_device or None},
        "device_identity": {"device_class": v.get("device_class")},
        "physical_characteristics": {
            "removable": v.get("removable"),
            "transport": v.get("transport"),
            "size_bytes": v.get("size_bytes"),
        },
        "mount_state": {"mounted": bool(v.get("mounted"))},
        "partition_summary": {
            "count": v.get("partition_count"),
            "target_device_resolved": v.get("target_device_resolved"),
        },
        "filesystem_summary": {"types": v.get("filesystem_types") or [], "count": len(v.get("filesystem_types") or [])},
        "risk_assessment": {"risk_level": v.get("risk_level")},
        "required_operator_checks": [
            "OPERATOR_CHECK_DEVICE_LABEL",
            "OPERATOR_CHECK_DEVICE_SIZE",
            "OPERATOR_CHECK_DEVICE_PATH",
        ],
        "blocked_reasons": blocked,
        "warnings": list(dict.fromkeys(v.get("warnings") or [])),
        "errors": list(v.get("errors") or []) + blocked,
    }


def build_operator_protocol(request: dict[str, Any]) -> dict[str, Any]:
    target_device = str(request.get("target_device") or "")
    steps = [
        "OPERATOR_CHECK_DEVICE_LABEL",
        "OPERATOR_CHECK_DEVICE_SIZE",
        "OPERATOR_CHECK_DEVICE_PATH",
        "OPERATOR_CONFIRM_NO_SYSTEM_DISK",
        "OPERATOR_CONFIRM_NO_WINDOWS_DATA",
        "OPERATOR_CONFIRM_BACKUP_EXISTS",
        "OPERATOR_CONFIRM_IMAGE_MATCH",
        "OPERATOR_CONFIRM_PHYSICAL_DEVICE",
        "OPERATOR_CONFIRM_DEVICE_UNPLUGGED_FROM_OTHER_SYSTEMS",
        "OPERATOR_CONFIRM_READY_FOR_DESTRUCTIVE_WRITE",
    ]
    abort = [
        "ABORT_IF_DEVICE_CHANGED",
        "ABORT_IF_NEW_MOUNTS_APPEAR",
        "ABORT_IF_SNAPSHOT_CHANGED",
        "ABORT_IF_DEVICE_SIZE_CHANGED",
        "ABORT_IF_MULTIPLE_MATCHING_DEVICES",
        "ABORT_IF_UNKNOWN_PARTITIONS",
        "ABORT_IF_OPERATOR_UNSURE",
    ]
    return {
        "protocol_id": secrets.token_hex(8),
        "target": {"target_device": target_device or None},
        "protocol_steps": steps,
        "required_confirmations": [s for s in steps if s.startswith("OPERATOR_CONFIRM_")],
        "manual_checks": [s for s in steps if s.startswith("OPERATOR_CHECK_")],
        "abort_conditions": abort,
        "warnings": [],
        "errors": [],
    }

