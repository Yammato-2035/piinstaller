from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, load_json_handoff, resolve_handoff_path, write_json_handoff

_PLAN_REL = "docs/evidence/runtime-results/handoff/rescue_restore_preview_plan.json"
_RESULT_REL = "docs/evidence/runtime-results/handoff/rescue_restore_preview_result.json"
_BKV_REL = "docs/evidence/runtime-results/handoff/rescue_backup_verify_result.json"
_DISC_REL = "docs/evidence/runtime-results/handoff/rescue_storage_discovery_result.json"
_EFI_REL = "docs/evidence/runtime-results/handoff/rescue_efi_boot_analysis.json"
_MAX_BYTES = 1_500_000


def _emit_plan(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_restore_preview_plan_status": status,
        "rescue_restore_preview_plan_file_path": _PLAN_REL,
        "rescue_restore_preview_plan": body,
        "rescue_restore_preview_plan_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _emit_result(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_restore_preview_result_status": status,
        "rescue_restore_preview_result_file_path": _RESULT_REL,
        "rescue_restore_preview_result": body,
        "rescue_restore_preview_result_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_restore_preview_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_PLAN_REL, "RESCUE_RSVPLAN")
    if oerr or out_path is None:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_RSVPLAN_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RSVPLAN")
    if gerr:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    body: dict[str, Any] = {
        "rescue_restore_preview_plan_schema_version": 1,
        "strict_mode": "rescue_restore_preview_only",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "inputs": {"rescue_backup_verify_result": _BKV_REL, "rescue_storage_discovery_result": _DISC_REL, "rescue_efi_boot_analysis": _EFI_REL},
        "writes_forbidden": True,
        "preview_only": True,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_plan("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit_plan("ok", body, wrote=True, warnings=[], errors=[])


def execute_rescue_restore_preview(
    *,
    explicit_overwrite: bool = False,
    explicit_execute_restore_preview: bool = False,
) -> dict[str, Any]:
    if not explicit_execute_restore_preview:
        return _emit_result(
            "blocked",
            {"reason": "EXECUTE_REQUIRES_EXPLICIT_RESTORE_PREVIEW"},
            wrote=False,
            warnings=[],
            errors=["EXECUTE_REQUIRES_EXPLICIT_RESTORE_PREVIEW"],
        )

    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_RSVRES")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_RSVRES_INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RSVRES")
    if g0:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[g0])

    bkv, _ = load_json_handoff(_BKV_REL, "RESCUE_RSVBKV")
    disc, _ = load_json_handoff(_DISC_REL, "RESCUE_RSVDISC")
    efi, _ = load_json_handoff(_EFI_REL, "RESCUE_RSVEFI")

    warnings: list[str] = []
    files_would_touch: list[str] = []
    mountpoints_affected: list[str] = []
    partition_hints: list[str] = []
    conflicts: list[str] = []
    risks: list[str] = ["RESCUE_RSV_NO_REAL_RESTORE"]
    rollback_hints = ["Stop session", "Do not remount rw on system disk", "Keep evidence export"]

    ev = {}
    if isinstance(bkv, dict):
        ev = bkv.get("evaluation") if isinstance(bkv.get("evaluation"), dict) else {}
    if not ev.get("restore_preview_possible"):
        warnings.append("RESCUE_RSV_PREVIEW_DEGRADED_BACKUP")

    if isinstance(bkv, dict):
        v = bkv.get("verify") if isinstance(bkv.get("verify"), dict) else {}
        for c in v.get("files_checked") or []:
            if isinstance(c, dict) and c.get("path"):
                files_would_touch.append(f"restore_target_relative:{c['path']}")

    if isinstance(disc, dict):
        for row in disc.get("lsblk_rows") or []:
            if not isinstance(row, dict):
                continue
            mp = row.get("mountpoint")
            fst = row.get("fstype")
            if mp and fst in ("ext4", "xfs", "btrfs"):
                mountpoints_affected.append(str(mp))
            if row.get("name"):
                partition_hints.append(str(row.get("name")))

    efi_affected = False
    if isinstance(efi, dict):
        efi_affected = bool(efi.get("efi_present"))
        if efi.get("fstab_problems_hint"):
            conflicts.append("fstab_uuid_hint")
        if not efi.get("grub_configuration_hints") and efi.get("efi_present"):
            conflicts.append("grub_missing_hint")

    if isinstance(disc, dict):
        cls = disc.get("classification") if isinstance(disc.get("classification"), dict) else {}
        if cls.get("uuid_conflicts"):
            conflicts.append("uuid_conflict")

    raw: dict[str, Any] = {
        "rescue_restore_preview_result_schema_version": 1,
        "strict_mode": "rescue_restore_preview_only",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "would_write_paths_preview": files_would_touch[:500],
        "mountpoints_affected_preview": list(dict.fromkeys(mountpoints_affected))[:40],
        "partition_hints_preview": list(dict.fromkeys(partition_hints))[:40],
        "efi_affected_preview": efi_affected,
        "conflicts_preview": conflicts,
        "recovery_risks_preview": risks,
        "rollback_hints_preview": rollback_hints,
        "writes_executed": False,
    }
    werr = write_json_handoff(out_path, raw, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", raw, wrote=False, warnings=warnings, errors=[werr])
    return build_rescue_restore_preview_result(explicit_overwrite=True, warnings=warnings)


def build_rescue_restore_preview_result(
    *,
    explicit_overwrite: bool = False,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_RSVRES")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_RSVRES_INVALID"])
    if not out_path.is_file():
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_RSVRES_MISSING"])
    g1 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RSVRES")
    if g1:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[g1])

    data = json.loads(out_path.read_text(encoding="utf-8"))
    warn = list(warnings or [])
    st = "ok"
    if data.get("writes_executed"):
        st = "blocked"
        warn.append("RESCUE_RSV_WRITE_FLAG_FORBIDDEN")
    elif any("RESCUE_RSV_PREVIEW_DEGRADED_BACKUP" in w for w in warn):
        st = "review_required"

    merged = dict(data)
    merged["evaluation"] = {
        "rescue_restore_preview_eval_status": st,
        "preview_only": True,
        "writes_performed": False,
    }
    werr = write_json_handoff(out_path, merged, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", merged, wrote=False, warnings=warn, errors=[werr])
    return _emit_result(st, merged, wrote=True, warnings=warn, errors=[])
