from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from core.storage_facade import build_storage_inventory_snapshot, classify_storage_devices
from deploy.runner_rescue_io import (
    ensure_rescue_workspace_dirs,
    guard_handoff_overwrite,
    load_json_handoff,
    resolve_handoff_path,
    write_json_handoff,
)

_PLAN_REL = "docs/evidence/runtime-results/handoff/rescue_storage_discovery_plan.json"
_RESULT_REL = "docs/evidence/runtime-results/handoff/rescue_storage_discovery_result.json"
_MAX_BYTES = 1_500_000


def _emit_plan(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_storage_discovery_plan_status": status,
        "rescue_storage_discovery_plan_file_path": _PLAN_REL,
        "rescue_storage_discovery_plan": body,
        "rescue_storage_discovery_plan_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _emit_result(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_storage_discovery_result_status": status,
        "rescue_storage_discovery_result_file_path": _RESULT_REL,
        "rescue_storage_discovery_result": body,
        "rescue_storage_discovery_result_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_storage_discovery_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_PLAN_REL, "RESCUE_STGPLAN")
    if oerr or out_path is None:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_STGPLAN_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_STGPLAN")
    if gerr:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    ensure_rescue_workspace_dirs()
    body: dict[str, Any] = {
        "rescue_storage_discovery_plan_schema_version": 1,
        "strict_mode": "rescue_live_storage_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "storage_facade": "core.storage_facade.build_storage_inventory_snapshot",
        "allowed_readonly_commands": [
            {"cmd": "lsblk", "args": ["-J", "-o", "NAME,TYPE,FSTYPE,LABEL,UUID,MOUNTPOINT,SIZE,MODEL,TRAN"]},
            {"cmd": "blkid"},
        ],
        "forbidden": ["mkfs", "fdisk", "parted", "dd", "wipefs", "mount", "-o", "rw", "fsck", "--repair"],
        "classification_targets": [
            "nvme",
            "sata",
            "usb",
            "sd",
            "efi_system_partition",
            "linux_fs",
            "ntfs",
            "btrfs",
            "xfs",
            "crypto_luks",
            "backup_candidate",
            "system_disk_candidate",
        ],
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_plan("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit_plan("ok", body, wrote=True, warnings=[], errors=[])


def execute_rescue_storage_discovery(
    *,
    explicit_overwrite: bool = False,
    explicit_execute_storage_discovery: bool = False,
) -> dict[str, Any]:
    if not explicit_execute_storage_discovery:
        return _emit_result(
            "blocked",
            {"reason": "EXECUTE_REQUIRES_EXPLICIT_EXECUTE_STORAGE_DISCOVERY"},
            wrote=False,
            warnings=[],
            errors=["EXECUTE_REQUIRES_EXPLICIT_EXECUTE_STORAGE_DISCOVERY"],
        )

    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_STGRES")
    if oerr or out_path is None:
        return _emit_result(
            "blocked",
            {},
            wrote=False,
            warnings=[],
            errors=[oerr or "RESCUE_STGRES_INVALID"],
        )
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_STGRES")
    if g0:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[g0])

    _, perr = load_json_handoff(_PLAN_REL, "RESCUE_STGPLAN")
    warnings: list[str] = []
    if perr:
        warnings.append(str(perr))

    snapshot = build_storage_inventory_snapshot(mode="rescue")
    warnings.extend(snapshot.get("warnings") or [])

    raw_body: dict[str, Any] = {
        "rescue_storage_discovery_result_schema_version": 1,
        "strict_mode": "rescue_live_storage_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "storage_facade_status": snapshot.get("status"),
        "lsblk_rows": snapshot.get("lsblk_rows") or [],
        "classification": snapshot.get("classification") or classify_storage_devices(snapshot.get("lsblk_rows") or []),
        "backup_target_candidates": snapshot.get("backup_target_candidates") or [],
        "restore_target_candidates": snapshot.get("restore_target_candidates") or [],
        "lsblk_excerpt": snapshot.get("lsblk_excerpt") or "",
        "blkid_excerpt": snapshot.get("blkid_excerpt") or "",
    }
    werr = write_json_handoff(out_path, raw_body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", raw_body, wrote=False, warnings=warnings, errors=[werr])
    return build_rescue_storage_discovery_result(explicit_overwrite=True, warnings=warnings)


def build_rescue_storage_discovery_result(
    *,
    explicit_overwrite: bool = False,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_STGRES")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_STGRES_INVALID"])
    if not out_path.is_file():
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_STGRES_MISSING_RUN_EXECUTE"])

    g1 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_STGRES")
    if g1:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[g1])

    try:
        data = json.loads(out_path.read_text(encoding="utf-8"))
    except Exception:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_STGRES_JSON_INVALID"])

    warn = list(warnings or [])
    errs: list[str] = []

    cls = data.get("classification") if isinstance(data.get("classification"), dict) else {}
    uuid_conf = list(cls.get("uuid_conflicts") or []) if isinstance(cls.get("uuid_conflicts"), list) else []

    eval_status = "ok"
    if errs:
        eval_status = "blocked"
    elif uuid_conf:
        eval_status = "review_required"
        warn.append("RESCUE_STORAGE_UUID_CONFLICT_HINT")
    elif int(cls.get("row_count") or 0) == 0 and not data.get("lsblk_rows"):
        eval_status = "review_required"
        warn.append("RESCUE_STORAGE_NO_ROWS")

    merged = dict(data)
    merged["evaluation"] = {
        "rescue_storage_discovery_eval_status": eval_status,
        "readonly_analysis_only": True,
        "uuid_conflicts": uuid_conf,
        "flags": cls.get("flags") if isinstance(cls.get("flags"), dict) else {},
    }
    werr = write_json_handoff(out_path, merged, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", merged, wrote=False, warnings=warn, errors=[werr])
    return _emit_result(eval_status, merged, wrote=True, warnings=warn, errors=errs)
