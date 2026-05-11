from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import (
    guard_handoff_overwrite,
    load_json_handoff,
    resolve_handoff_path,
    write_json_handoff,
)

_INV_REL = "docs/evidence/runtime-results/handoff/rescue_stick_component_inventory.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_mvp_scope_gate.json"
_MAX_BYTES = 512 * 1024

_MVP_FORBIDDEN_IDS = frozenset(
    {
        "automatic_restore_execute",
        "automatic_bootloader_repair",
        "automatic_partitioning",
        "automatic_installation",
        "automatic_efi_repair",
        "automatic_internal_disk_write",
    }
)


def _emit(
    status: str,
    body: dict[str, Any],
    *,
    wrote: bool,
    warnings: list[str],
    errors: list[str],
) -> dict[str, Any]:
    return {
        "rescue_mvp_scope_gate_status": status,
        "rescue_mvp_scope_gate_file_path": _OUT_REL,
        "rescue_mvp_scope_gate": body,
        "rescue_mvp_scope_gate_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_mvp_scope_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_MVP")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_MVP_OUTPUT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_MVP")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    inv, ierr = load_json_handoff(_INV_REL, "RESCUE_MVP_INV")
    if ierr or not isinstance(inv, dict):
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[str(ierr or "RESCUE_MVP_INVENTORY_MISSING")])

    rows = inv.get("components")
    if not isinstance(rows, list):
        return _emit("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_MVP_INVENTORY_COMPONENTS_INVALID"])

    errors: list[str] = []
    warnings: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        cid = str(row.get("component_id") or "")
        mvp = bool(row.get("required_for_mvp"))
        if mvp and cid in _MVP_FORBIDDEN_IDS:
            errors.append(f"RESCUE_MVP_FORBIDDEN_REQUIRED:{cid}")

    mvp_includes = [
        "bootable_debian_live",
        "setuphelfer_ui_local",
        "setuphelfer_backend_local",
        "hardware_disk_inspect",
        "backup_discovery",
        "verify",
        "restore_preview_only",
        "write_safety_checks",
        "evidence_export",
        "network_status",
        "optional_ssh_readonly_help",
    ]
    mvp_excludes = [
        "automatic_restore",
        "automatic_bootloader_fix",
        "automatic_partitioning",
        "automatic_installation",
        "automatic_efi_repair",
        "real_writes_to_internal_disks",
    ]

    status = "ok"
    if errors:
        status = "blocked"

    body: dict[str, Any] = {
        "rescue_mvp_scope_gate_schema_version": 1,
        "strict_mode": "setuphelfer_rescue_stick_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mvp_scope_evaluation_status": status,
        "mvp_includes": mvp_includes,
        "mvp_excludes": mvp_excludes,
        "forbidden_auto_operations_absent": len(errors) == 0,
        "inputs": {"rescue_stick_component_inventory": _INV_REL},
    }

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit(status, body, wrote=True, warnings=warnings, errors=errors)
