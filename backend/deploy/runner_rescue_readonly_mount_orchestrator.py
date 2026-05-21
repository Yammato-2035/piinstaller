from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from core.mount_facade import plan_readonly_source_mount
from core.storage_facade import build_storage_inventory_snapshot
from deploy.runner_rescue_io import REPO_ROOT, ensure_rescue_workspace_dirs, guard_handoff_overwrite, load_json_handoff, resolve_handoff_path, write_json_handoff

_PLAN_REL = "docs/evidence/runtime-results/handoff/readonly_mount_plan.json"
_RESULT_REL = "docs/evidence/runtime-results/handoff/readonly_mount_result.json"
_MOUNT_PREFIX = "build/rescue/runtime-mounts/"
_MAX_BYTES = 768 * 1024


def _emit_plan(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "readonly_mount_plan_status": status,
        "readonly_mount_plan_file_path": _PLAN_REL,
        "readonly_mount_plan": body,
        "readonly_mount_plan_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _emit_result(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "readonly_mount_result_status": status,
        "readonly_mount_result_file_path": _RESULT_REL,
        "readonly_mount_result": body,
        "readonly_mount_result_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _under_runtime_mounts(rel: str) -> bool:
    s = rel.replace("\\", "/").strip()
    return s.startswith(_MOUNT_PREFIX) and ".." not in s


def build_readonly_mount_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_PLAN_REL, "RESCUE_RDMPLAN")
    if oerr or out_path is None:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_RDMPLAN_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RDMPLAN")
    if gerr:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    ensure_rescue_workspace_dirs()
    (REPO_ROOT / _MOUNT_PREFIX.rstrip("/")).mkdir(parents=True, exist_ok=True)

    disc, _ = load_json_handoff("docs/evidence/runtime-results/handoff/rescue_storage_discovery_result.json", "RESCUE_RDMDISC")
    storage_snapshot: dict[str, Any]
    if isinstance(disc, dict) and disc.get("lsblk_rows"):
        storage_snapshot = {
            "lsblk_rows": disc.get("lsblk_rows"),
            "status": "ok",
        }
    else:
        storage_snapshot = build_storage_inventory_snapshot(mode="rescue")

    plan_core = plan_readonly_source_mount(storage_snapshot, mount_root_prefix=_MOUNT_PREFIX)
    body: dict[str, Any] = {
        "readonly_mount_plan_schema_version": 1,
        "strict_mode": "rescue_readonly_mount_only",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mount_facade": "core.mount_facade.plan_readonly_source_mount",
        "mount_root_prefix": _MOUNT_PREFIX,
        "cleanup_policy": plan_core.get("cleanup_policy"),
        "forbidden": plan_core.get("forbidden"),
        "planned_operations": plan_core.get("planned_operations") or [],
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_plan("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit_plan("ok", body, wrote=True, warnings=[], errors=[])


def execute_readonly_mount_validation(
    *,
    explicit_overwrite: bool = False,
    explicit_execute_readonly_mount: bool = False,
) -> dict[str, Any]:
    if not explicit_execute_readonly_mount:
        return _emit_result(
            "blocked",
            {"reason": "EXECUTE_REQUIRES_EXPLICIT_READONLY_MOUNT"},
            wrote=False,
            warnings=[],
            errors=["EXECUTE_REQUIRES_EXPLICIT_READONLY_MOUNT"],
        )

    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_RDMRES")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_RDMRES_INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RDMRES")
    if g0:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[g0])

    plan, perr = load_json_handoff(_PLAN_REL, "RESCUE_RDMPLAN")
    if perr or not isinstance(plan, dict):
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[str(perr or "RESCUE_RDMPLAN_MISSING")])

    ops = plan.get("planned_operations")
    if not isinstance(ops, list):
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_RDM_OPS_INVALID"])

    warnings: list[str] = []
    errors: list[str] = []
    lab = os.environ.get("SETUPHELFER_RESCUE_READONLY_MOUNT_LAB") == "1"

    validated: list[dict[str, Any]] = []
    for op in ops:
        if not isinstance(op, dict):
            continue
        mp = str(op.get("mountpoint") or "")
        ro = bool(op.get("read_only"))
        if not ro:
            errors.append(f"RESCUE_RDM_RW_NOT_ALLOWED:{mp}")
        if not _under_runtime_mounts(mp):
            errors.append(f"RESCUE_RDM_BAD_MOUNTPOINT:{mp}")
        validated.append(
            {
                "mountpoint": mp,
                "read_only": ro,
                "lab_real_mount_attempted": bool(lab),
                "mount_executed": False,
                "validation_only": not lab,
            }
        )

    raw: dict[str, Any] = {
        "readonly_mount_result_schema_version": 1,
        "strict_mode": "rescue_readonly_mount_only",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "operations": validated,
        "efi_mountable_hint": not errors and any("vfat" in str(x.get("filesystem")) for x in ops if isinstance(x, dict)),
        "linux_root_mountable_hint": not errors and any(str(x.get("filesystem") or "").startswith("ext") for x in ops if isinstance(x, dict)),
    }
    werr = write_json_handoff(out_path, raw, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", raw, wrote=False, warnings=warnings, errors=[werr])
    return build_readonly_mount_result(explicit_overwrite=True, warnings=warnings)


def build_readonly_mount_result(*, explicit_overwrite: bool = False, warnings: list[str] | None = None) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_RDMRES")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_RDMRES_INVALID"])
    if not out_path.is_file():
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_RDMRES_MISSING"])
    g1 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RDMRES")
    if g1:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[g1])

    data = json.loads(out_path.read_text(encoding="utf-8"))
    warn = list(warnings or [])
    ops = data.get("operations") if isinstance(data.get("operations"), list) else []
    any_rw = any(not bool(x.get("read_only")) for x in ops if isinstance(x, dict))
    st = "blocked" if any_rw else "ok"
    if any_rw:
        warn.append("RESCUE_RDM_EVAL_RW_DETECTED")

    merged = dict(data)
    merged["evaluation"] = {
        "readonly_mount_eval_status": st,
        "readonly_enforced": not any_rw,
        "no_host_root_mount": True,
    }
    werr = write_json_handoff(out_path, merged, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", merged, wrote=False, warnings=warn, errors=[werr])
    return _emit_result(st, merged, wrote=True, warnings=warn, errors=[] if st == "ok" else ["RESCUE_RDM_READONLY_VIOLATION"])
