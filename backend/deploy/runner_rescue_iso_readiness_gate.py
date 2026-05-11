from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, load_json_handoff, resolve_handoff_path, write_json_handoff

_BUILD_REL = "docs/evidence/runtime-results/handoff/rescue_iso_build_result.json"
_VM_REL = "docs/evidence/runtime-results/handoff/rescue_vm_test_result.json"
_PROBE_REL = "docs/evidence/runtime-results/handoff/rescue_iso_live_runtime_probe_result.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_iso_readiness_gate.json"
_MAX_BYTES = 512 * 1024


def _emit(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_iso_readiness_gate_status": status,
        "rescue_iso_readiness_gate_file_path": _OUT_REL,
        "rescue_iso_readiness_gate": body,
        "rescue_iso_readiness_gate_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_iso_readiness_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_ISOREADY")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_ISOREADY_OUTPUT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ISOREADY")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    warnings: list[str] = []
    errors: list[str] = []

    br, e1 = load_json_handoff(_BUILD_REL, "RESCUE_ISOREADY_BUILD")
    vm, e2 = load_json_handoff(_VM_REL, "RESCUE_ISOREADY_VM")
    pr, e3 = load_json_handoff(_PROBE_REL, "RESCUE_ISOREADY_PROBE")
    for code in (e1, e2, e3):
        if code:
            errors.append(str(code))

    if isinstance(br, dict):
        if not bool(br.get("build_success")):
            errors.append("RESCUE_ISOREADY_BUILD_NOT_SUCCESS")
        if not bool(br.get("iso_found")):
            errors.append("RESCUE_ISOREADY_ISO_NOT_FOUND_IN_RESULT")
        fc = br.get("forbidden_commands_detected") or []
        if isinstance(fc, list) and len(fc) > 0:
            errors.append("RESCUE_ISOREADY_FORBIDDEN_IN_BUILD")
    else:
        errors.append("RESCUE_ISOREADY_BUILD_INVALID")

    vm_st = ""
    if isinstance(vm, dict):
        if bool(vm.get("vm_boot_simulated")) and bool(vm.get("iso_verified")) and bool(vm.get("qemu_available")):
            vm_st = "ok"
        elif bool(vm.get("vm_boot_simulated")) and bool(vm.get("iso_verified")) and not bool(vm.get("qemu_available")):
            vm_st = "review_required"
        else:
            vm_st = "blocked"
        if vm_st == "blocked":
            errors.append("RESCUE_ISOREADY_VM_BLOCKED")
        elif vm_st == "review_required":
            warnings.append("RESCUE_ISOREADY_VM_REVIEW_REQUIRED")
    else:
        errors.append("RESCUE_ISOREADY_VM_INVALID")

    probe_st = ""
    legacy = False
    if isinstance(pr, dict):
        ev = pr.get("evaluation") if isinstance(pr.get("evaluation"), dict) else {}
        probe_st = str(ev.get("iso_live_runtime_probe_status") or "")
        legacy = bool(ev.get("legacy_runtime_detected"))
        if legacy:
            errors.append("RESCUE_ISOREADY_LEGACY_DETECTED")
        if probe_st == "blocked":
            errors.append("RESCUE_ISOREADY_PROBE_BLOCKED")
        elif probe_st == "review_required":
            warnings.append("RESCUE_ISOREADY_PROBE_REVIEW_REQUIRED")
    else:
        errors.append("RESCUE_ISOREADY_PROBE_INVALID")

    status = "ready"
    if errors:
        status = "blocked"
    elif warnings or vm_st == "review_required" or probe_st == "review_required":
        status = "review_required"

    if status == "ready":
        if vm_st != "ok" or probe_st != "ok":
            status = "review_required"
            warnings.append("RESCUE_ISOREADY_SUBGATE_NOT_STRICT_OK")

    body: dict[str, Any] = {
        "rescue_iso_readiness_gate_schema_version": 1,
        "strict_mode": "setuphelfer_rescue_iso_phase1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_status": status,
        "inputs": {
            "rescue_iso_build_result": _BUILD_REL,
            "rescue_vm_test_result": _VM_REL,
            "rescue_iso_live_runtime_probe_result": _PROBE_REL,
        },
        "checks": {
            "iso_build_ok": isinstance(br, dict) and bool(br.get("build_success")),
            "vm_ok": vm_st == "ok",
            "probe_ok": probe_st == "ok",
            "no_legacy": not legacy,
        },
    }

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit(status, body, wrote=True, warnings=warnings, errors=errors)
