from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, load_json_handoff, resolve_handoff_path, write_json_handoff

_STG_REL = "docs/evidence/runtime-results/handoff/rescue_storage_discovery_result.json"
_MNT_REL = "docs/evidence/runtime-results/handoff/readonly_mount_result.json"
_EFI_REL = "docs/evidence/runtime-results/handoff/rescue_efi_boot_analysis.json"
_EV_REL = "docs/evidence/runtime-results/handoff/rescue_evidence_export_result.json"
_RH_REL = "docs/evidence/runtime-results/handoff/rescue_remote_help_result.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_live_runtime_safety_gate.json"
_MAX_BYTES = 512 * 1024


def _emit(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_live_runtime_safety_gate_status": status,
        "rescue_live_runtime_safety_gate_file_path": _OUT_REL,
        "rescue_live_runtime_safety_gate": body,
        "rescue_live_runtime_safety_gate_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_live_runtime_safety_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_LVRG")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_LVRG_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_LVRG")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    warnings: list[str] = []
    errors: list[str] = []

    stg, e1 = load_json_handoff(_STG_REL, "LVRG_STG")
    mnt, e2 = load_json_handoff(_MNT_REL, "LVRG_MNT")
    efi, e3 = load_json_handoff(_EFI_REL, "LVRG_EFI")
    ev, e4 = load_json_handoff(_EV_REL, "LVRG_EV")
    rh, e5 = load_json_handoff(_RH_REL, "LVRG_RH")
    for code in (e1, e2, e3, e4, e5):
        if code:
            errors.append(str(code))

    st_eval = ""
    if isinstance(stg, dict):
        evs = stg.get("evaluation") if isinstance(stg.get("evaluation"), dict) else {}
        st_eval = str(evs.get("rescue_storage_discovery_eval_status") or "")
        if st_eval == "blocked":
            errors.append("RESCUE_LVRG_STORAGE_BLOCKED")

    mnt_ev = ""
    if isinstance(mnt, dict):
        me = mnt.get("evaluation") if isinstance(mnt.get("evaluation"), dict) else {}
        mnt_ev = str(me.get("readonly_mount_eval_status") or "")
        if not bool(me.get("readonly_enforced", True)):
            errors.append("RESCUE_LVRG_RW_MOUNT")
        if mnt_ev == "blocked":
            errors.append("RESCUE_LVRG_MOUNT_BLOCKED")

    if isinstance(efi, dict):
        if str(efi.get("rescue_efi_boot_analysis_status") or "") == "blocked":
            errors.append("RESCUE_LVRG_EFI_BLOCKED")

    if isinstance(ev, dict):
        ee = ev.get("evaluation") if isinstance(ev.get("evaluation"), dict) else {}
        if str(ee.get("rescue_evidence_export_eval_status") or "") == "blocked":
            errors.append("RESCUE_LVRG_EVIDENCE_BLOCKED")

    if isinstance(rh, dict):
        if rh.get("ssh_service_auto_started") is True:
            errors.append("RESCUE_LVRG_SSH_AUTO_FORBIDDEN")

    status = "ready"
    if errors:
        status = "blocked"
    elif st_eval == "review_required" or mnt_ev == "review_required":
        status = "review_required"
        warnings.append("RESCUE_LVRG_SUB_REVIEW")

    body: dict[str, Any] = {
        "rescue_live_runtime_safety_gate_schema_version": 1,
        "strict_mode": "rescue_live_runtime_safety",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_status": status,
        "inputs": {
            "rescue_storage_discovery_result": _STG_REL,
            "readonly_mount_result": _MNT_REL,
            "rescue_efi_boot_analysis": _EFI_REL,
            "rescue_evidence_export_result": _EV_REL,
            "rescue_remote_help_result": _RH_REL,
        },
    }

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit(status, body, wrote=True, warnings=warnings, errors=errors)
