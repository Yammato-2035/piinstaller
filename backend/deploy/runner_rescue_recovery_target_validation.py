from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import (
    REPO_ROOT,
    guard_handoff_overwrite,
    load_json_handoff,
    resolve_handoff_path,
    resolve_under_build_rescue,
    write_json_handoff,
)

_PLAN_REL = "docs/evidence/runtime-results/handoff/rescue_recovery_target_validation_plan.json"
_RESULT_REL = "docs/evidence/runtime-results/handoff/rescue_recovery_target_validation_result.json"
_DISC_REL = "docs/evidence/runtime-results/handoff/rescue_storage_discovery_result.json"
_MNT_REL = "docs/evidence/runtime-results/handoff/readonly_mount_result.json"
_MAX_BYTES = 768 * 1024


def _emit_plan(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_recovery_target_validation_plan_status": status,
        "rescue_recovery_target_validation_plan_file_path": _PLAN_REL,
        "rescue_recovery_target_validation_plan": body,
        "rescue_recovery_target_validation_plan_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _emit_result(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_recovery_target_validation_result_status": status,
        "rescue_recovery_target_validation_result_file_path": _RESULT_REL,
        "rescue_recovery_target_validation_result": body,
        "rescue_recovery_target_validation_result_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_recovery_target_validation_plan(
    *,
    explicit_overwrite: bool = False,
    proposed_recovery_target: str | None = None,
) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_PLAN_REL, "RESCUE_RTVPLAN")
    if oerr or out_path is None:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_RTVPLAN_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RTVPLAN")
    if gerr:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    body: dict[str, Any] = {
        "rescue_recovery_target_validation_plan_schema_version": 1,
        "strict_mode": "rescue_recovery_target_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "proposed_recovery_target": (proposed_recovery_target or "").strip()[:512] or None,
        "checks": [
            "medium_plausible",
            "system_disk_hint",
            "external_backup_disk_hint",
            "readonly_enforced",
            "free_space_hint",
            "wrong_target_patterns",
            "internal_active_system_partition",
            "legacy_target",
            "uuid_conflict",
        ],
        "writes_forbidden": True,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_plan("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit_plan("ok", body, wrote=True, warnings=[], errors=[])


def _bad_target(raw: str) -> tuple[bool, str]:
    s = raw.replace("\\", "/").strip().lower()
    if not s:
        return False, ""
    if (
        s in ("/", "/boot", "/efi", "/home", "/root")
        or s.startswith("/boot/")
        or s.startswith("/efi/")
        or s.startswith("/home/")
        or s.startswith("/root/")
    ):
        return True, "BLOCKED_SYSTEM_PATH"
    if s.startswith("/dev/sd") and "p" not in s and len(s) <= 8:
        return True, "WHOLE_DISK_RISK_PATTERN"
    return False, ""


def execute_rescue_recovery_target_validation(
    *,
    explicit_overwrite: bool = False,
    explicit_execute_recovery_target_validation: bool = False,
) -> dict[str, Any]:
    if not explicit_execute_recovery_target_validation:
        return _emit_result(
            "blocked",
            {"reason": "EXECUTE_REQUIRES_EXPLICIT_RECOVERY_TARGET_VALIDATION"},
            wrote=False,
            warnings=[],
            errors=["EXECUTE_REQUIRES_EXPLICIT_RECOVERY_TARGET_VALIDATION"],
        )

    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_RTVRES")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_RTVRES_INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RTVRES")
    if g0:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[g0])

    plan, perr = load_json_handoff(_PLAN_REL, "RESCUE_RTVPLAN")
    disc, _ = load_json_handoff(_DISC_REL, "RESCUE_RTVDISC")
    mnt, _ = load_json_handoff(_MNT_REL, "RESCUE_RTVMNT")

    proposed = ""
    if isinstance(plan, dict) and plan.get("proposed_recovery_target"):
        proposed = str(plan.get("proposed_recovery_target")).strip()

    warnings: list[str] = []
    errors: list[str] = []
    if perr:
        warnings.append(str(perr))

    bad, reason = _bad_target(proposed)
    if bad:
        errors.append(f"RESCUE_RTV_TARGET_{reason}")

    under_lab = False
    if proposed:
        rp, rerr = resolve_under_build_rescue(proposed.replace("\\", "/").lstrip("/"), "RESCUE_RTV")
        if not rerr and rp is not None:
            under_lab = True
        elif proposed.startswith("build/rescue/"):
            try:
                (REPO_ROOT / proposed).resolve().relative_to((REPO_ROOT / "build" / "rescue").resolve(strict=False))
                under_lab = True
            except (OSError, ValueError):
                pass

    cls = disc.get("classification") if isinstance(disc, dict) else {}
    uuid_conf = list(cls.get("uuid_conflicts") or []) if isinstance(cls, dict) and isinstance(cls.get("uuid_conflicts"), list) else []

    ro_ok = False
    if isinstance(mnt, dict):
        me = mnt.get("evaluation") if isinstance(mnt.get("evaluation"), dict) else {}
        ro_ok = bool(me.get("readonly_enforced", False)) and str(me.get("readonly_mount_eval_status") or "") != "blocked"
    else:
        warnings.append("RESCUE_RTV_READONLY_MOUNT_HANDOFF_MISSING")

    flags = cls.get("flags") if isinstance(cls, dict) and isinstance(cls.get("flags"), dict) else {}
    system_hint = bool(flags.get("system_disk_candidate")) if flags else False
    backup_hint = bool(flags.get("backup_candidate")) if flags else False

    raw: dict[str, Any] = {
        "rescue_recovery_target_validation_result_schema_version": 1,
        "strict_mode": "rescue_recovery_target_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "proposed_recovery_target": proposed or None,
        "findings": {
            "medium_plausible": bool(proposed) and (under_lab or proposed.startswith("/media/") or proposed.startswith("/run/media/")),
            "system_disk_detected": system_hint,
            "external_backup_disk_detected": backup_hint,
            "readonly_enforced": ro_ok,
            "free_space_hint_unknown": True,
            "wrong_target": bad,
            "internal_active_system_partition_risk": bad and "BLOCKED_SYSTEM_PATH" in reason,
            "legacy_target_hint": ("legacy" in proposed.lower() or "pi_installer" in proposed.lower()) if proposed else False,
            "uuid_conflict": bool(uuid_conf),
        },
        "uuid_conflicts": uuid_conf,
    }
    werr = write_json_handoff(out_path, raw, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", raw, wrote=False, warnings=warnings, errors=[werr])
    return build_rescue_recovery_target_validation_result(explicit_overwrite=True, warnings=warnings, errors=errors)


def build_rescue_recovery_target_validation_result(
    *,
    explicit_overwrite: bool = False,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_RTVRES")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_RTVRES_INVALID"])
    if not out_path.is_file():
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_RTVRES_MISSING"])
    g1 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RTVRES")
    if g1:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[g1])

    data = json.loads(out_path.read_text(encoding="utf-8"))
    warn = list(warnings or [])
    errs = list(errors or [])
    findings = data.get("findings") if isinstance(data.get("findings"), dict) else {}

    st = "ok"
    if errs or findings.get("wrong_target"):
        st = "blocked"
    elif not findings.get("readonly_enforced"):
        st = "blocked"
    elif findings.get("uuid_conflict"):
        st = "review_required"
        warn.append("RESCUE_RTV_UUID_CONFLICT")
    elif not data.get("proposed_recovery_target"):
        st = "review_required"
        warn.append("RESCUE_RTV_NO_TARGET_PROPOSED")
    elif not findings.get("medium_plausible"):
        st = "review_required"
        warn.append("RESCUE_RTV_TARGET_NOT_UNDER_ALLOWED_PREFIX")

    merged = dict(data)
    merged["evaluation"] = {
        "rescue_recovery_target_validation_eval_status": st,
        "writes_performed": False,
    }
    werr = write_json_handoff(out_path, merged, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", merged, wrote=False, warnings=warn, errors=[werr])
    return _emit_result(st, merged, wrote=True, warnings=warn, errors=errs if st == "blocked" else [])
