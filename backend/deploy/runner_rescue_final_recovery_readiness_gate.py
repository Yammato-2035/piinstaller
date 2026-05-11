from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, load_json_handoff, resolve_handoff_path, write_json_handoff

_RTV_REL = "docs/evidence/runtime-results/handoff/rescue_recovery_target_validation_result.json"
_BKV_REL = "docs/evidence/runtime-results/handoff/rescue_backup_verify_result.json"
_RSV_REL = "docs/evidence/runtime-results/handoff/rescue_restore_preview_result.json"
_HW_REL = "docs/evidence/runtime-results/handoff/rescue_hardware_recovery_test_chain.json"
_LVRG_REL = "docs/evidence/runtime-results/handoff/rescue_live_runtime_safety_gate.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_final_recovery_readiness_gate.json"
_MAX_BYTES = 512 * 1024


def _emit(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_final_recovery_readiness_gate_status": status,
        "rescue_final_recovery_readiness_gate_file_path": _OUT_REL,
        "rescue_final_recovery_readiness_gate": body,
        "rescue_final_recovery_readiness_gate_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_final_recovery_readiness_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_FRG")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_FRG_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_FRG")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    warnings: list[str] = []
    errors: list[str] = []

    rtv, e1 = load_json_handoff(_RTV_REL, "FRG_RTV")
    bkv, e2 = load_json_handoff(_BKV_REL, "FRG_BKV")
    rsv, e3 = load_json_handoff(_RSV_REL, "FRG_RSV")
    hw, e4 = load_json_handoff(_HW_REL, "FRG_HW")
    lvrg, e5 = load_json_handoff(_LVRG_REL, "FRG_LVRG")
    for code in (e1, e2, e3, e4, e5):
        if code:
            errors.append(str(code))

    if isinstance(rtv, dict):
        ev = rtv.get("evaluation") if isinstance(rtv.get("evaluation"), dict) else {}
        if str(ev.get("rescue_recovery_target_validation_eval_status") or "") == "blocked":
            errors.append("FRG_TARGET_BLOCKED")
        elif str(ev.get("rescue_recovery_target_validation_eval_status") or "") == "review_required":
            warnings.append("FRG_TARGET_REVIEW")

    if isinstance(bkv, dict):
        ev = bkv.get("evaluation") if isinstance(bkv.get("evaluation"), dict) else {}
        if str(ev.get("rescue_backup_verify_eval_status") or "") == "blocked":
            errors.append("FRG_BACKUP_VERIFY_BLOCKED")
        elif ev.get("restore_preview_possible") is False:
            warnings.append("FRG_RESTORE_PREVIEW_NOT_POSSIBLE")

    if isinstance(rsv, dict):
        ev = rsv.get("evaluation") if isinstance(rsv.get("evaluation"), dict) else {}
        if str(ev.get("rescue_restore_preview_eval_status") or "") == "blocked":
            errors.append("FRG_RESTORE_PREVIEW_BLOCKED")
        if ev.get("writes_performed"):
            errors.append("FRG_RESTORE_PREVIEW_WRITE_FORBIDDEN")

    if isinstance(hw, dict):
        if str(hw.get("chain_summary_status") or "") != "ok":
            warnings.append("FRG_HW_CHAIN_NOT_OK")

    if isinstance(lvrg, dict):
        gs = str(lvrg.get("gate_status") or "")
        if gs == "blocked":
            errors.append("FRG_LIVE_RUNTIME_BLOCKED")
        elif gs == "review_required":
            warnings.append("FRG_LIVE_RUNTIME_REVIEW")

    status = "ready"
    if errors:
        status = "blocked"
    elif warnings:
        status = "review_required"

    body: dict[str, Any] = {
        "rescue_final_recovery_readiness_gate_schema_version": 1,
        "strict_mode": "rescue_final_recovery_readiness_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_status": status,
        "inputs": {
            "rescue_recovery_target_validation_result": _RTV_REL,
            "rescue_backup_verify_result": _BKV_REL,
            "rescue_restore_preview_result": _RSV_REL,
            "rescue_hardware_recovery_test_chain": _HW_REL,
            "rescue_live_runtime_safety_gate": _LVRG_REL,
        },
    }

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit(status, body, wrote=True, warnings=warnings, errors=errors)
