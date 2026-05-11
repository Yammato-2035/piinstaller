from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import (
    guard_handoff_overwrite,
    load_json_handoff,
    resolve_handoff_path,
    under_build_rescue,
    write_json_handoff,
)

_LIVE_REL = "docs/evidence/runtime-results/handoff/rescue_live_os_base_decision.json"
_INV_REL = "docs/evidence/runtime-results/handoff/rescue_stick_component_inventory.json"
_MVP_REL = "docs/evidence/runtime-results/handoff/rescue_mvp_scope_gate.json"
_PLAN_REL = "docs/evidence/runtime-results/handoff/rescue_debian_live_build_plan.json"
_MATRIX_REL = "docs/evidence/runtime-results/handoff/rescue_iso_test_matrix.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_build_readiness_gate.json"
_MAX_BYTES = 512 * 1024

_FORBIDDEN_PLAN_SUBSTRINGS = ("/dev/sd", "dd if=", "dd of=", " mkfs ", "systemctl enable", "restore-execute", "write-usb")


def _emit(
    status: str,
    body: dict[str, Any],
    *,
    wrote: bool,
    warnings: list[str],
    errors: list[str],
) -> dict[str, Any]:
    return {
        "rescue_build_readiness_gate_status": status,
        "rescue_build_readiness_gate_file_path": _OUT_REL,
        "rescue_build_readiness_gate": body,
        "rescue_build_readiness_gate_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_build_readiness_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_READY")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_READY_OUTPUT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_READY")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    errors: list[str] = []
    warnings: list[str] = []

    live, e1 = load_json_handoff(_LIVE_REL, "RESCUE_READY_LIVE")
    inv, e2 = load_json_handoff(_INV_REL, "RESCUE_READY_INV")
    mvp, e3 = load_json_handoff(_MVP_REL, "RESCUE_READY_MVP")
    plan, e4 = load_json_handoff(_PLAN_REL, "RESCUE_READY_PLAN")
    matrix, e5 = load_json_handoff(_MATRIX_REL, "RESCUE_READY_MATRIX")

    for code in (e1, e2, e3, e4, e5):
        if code:
            errors.append(str(code))

    if isinstance(live, dict):
        if str(live.get("recommended_live_os_base") or "") != "debian_live":
            errors.append("RESCUE_READY_LIVE_OS_NOT_DEBIAN")
        if str(live.get("secure_boot_status") or "") == "blocked":
            errors.append("RESCUE_READY_SECUREBOOT_BLOCKED_UNEXPECTED")
    else:
        errors.append("RESCUE_READY_LIVE_OS_BODY_INVALID")

    if not isinstance(inv, dict) or not isinstance(inv.get("components"), list):
        errors.append("RESCUE_READY_INVENTORY_INVALID")

    mvp_status = ""
    if isinstance(mvp, dict):
        if mvp.get("forbidden_auto_operations_absent") is not True:
            errors.append("RESCUE_READY_MVP_FORBIDDEN_FLAG_FALSE")
        mvp_status = str(mvp.get("mvp_scope_evaluation_status") or "")
    else:
        errors.append("RESCUE_READY_MVP_INVALID")

    if mvp_status == "blocked":
        errors.append("RESCUE_READY_MVP_BLOCKED")
    elif mvp_status == "review_required":
        warnings.append("RESCUE_READY_MVP_REVIEW_REQUIRED")

    if isinstance(plan, dict):
        root = str(plan.get("artifact_output_root") or "")
        if not under_build_rescue(root):
            errors.append("RESCUE_READY_PLAN_ROOT_INVALID")
        outs = plan.get("output_paths")
        if isinstance(outs, list):
            for p in outs:
                if not under_build_rescue(str(p)):
                    errors.append(f"RESCUE_READY_PLAN_PATH_OUTSIDE:{p}")
        plan_blob = json.dumps(plan, sort_keys=True).lower()
        for bad in _FORBIDDEN_PLAN_SUBSTRINGS:
            if bad in plan_blob:
                errors.append(f"RESCUE_READY_PLAN_FORBIDDEN_TOKEN:{bad.strip()}")
                break
    else:
        errors.append("RESCUE_READY_PLAN_INVALID")

    if isinstance(matrix, dict):
        if "vm" not in matrix or "laptop" not in matrix:
            errors.append("RESCUE_READY_MATRIX_MISSING_VM_OR_LAPTOP")
    else:
        errors.append("RESCUE_READY_MATRIX_INVALID")

    status = "ready"
    if errors:
        status = "blocked"
    elif warnings:
        status = "review_required"

    body: dict[str, Any] = {
        "rescue_build_readiness_gate_schema_version": 1,
        "strict_mode": "setuphelfer_rescue_stick_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_status": status,
        "inputs": {
            "rescue_live_os_base_decision": _LIVE_REL,
            "rescue_stick_component_inventory": _INV_REL,
            "rescue_mvp_scope_gate": _MVP_REL,
            "rescue_debian_live_build_plan": _PLAN_REL,
            "rescue_iso_test_matrix": _MATRIX_REL,
        },
        "checks": {
            "debian_live_recommended": True,
            "mvp_okish": mvp_status in ("ok", "review_required"),
            "artifact_root_build_rescue_only": True,
            "test_matrix_present": isinstance(matrix, dict),
        },
    }

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit(status, body, wrote=True, warnings=warnings, errors=errors)
