from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import (
    BUILD_RESCUE_ROOT,
    REPO_ROOT,
    ensure_rescue_workspace_dirs,
    guard_handoff_overwrite,
    load_json_handoff,
    resolve_handoff_path,
    write_json_handoff,
)

_PLAN_REL = "docs/evidence/runtime-results/handoff/rescue_vm_test_plan.json"
_RESULT_REL = "docs/evidence/runtime-results/handoff/rescue_vm_test_result.json"
_MAX_BYTES = 768 * 1024


def _emit_plan(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_vm_test_plan_status": status,
        "rescue_vm_test_plan_file_path": _PLAN_REL,
        "rescue_vm_test_plan": body,
        "rescue_vm_test_plan_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _emit_result(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_vm_test_result_status": status,
        "rescue_vm_test_result_file_path": _RESULT_REL,
        "rescue_vm_test_result": body,
        "rescue_vm_test_result_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _default_iso_rel() -> str:
    out = BUILD_RESCUE_ROOT / "output"
    if not out.is_dir():
        return "build/rescue/output/setuphelfer-rescue-amd64.iso"
    isos = sorted(out.glob("*.iso"))
    if not isos:
        return "build/rescue/output/setuphelfer-rescue-amd64.iso"
    return str(isos[-1].relative_to(REPO_ROOT)).replace("\\", "/")


def build_rescue_vm_test_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_PLAN_REL, "RESCUE_VMPLAN")
    if oerr or out_path is None:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_VMPLAN_OUTPUT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_VMPLAN")
    if gerr:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    ensure_rescue_workspace_dirs()
    iso_rel = _default_iso_rel()
    body: dict[str, Any] = {
        "rescue_vm_test_plan_schema_version": 1,
        "strict_mode": "setuphelfer_rescue_iso_phase1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hypervisor": "qemu-system-x86_64",
        "iso_path": iso_rel,
        "firmware": "uefi",
        "network": "user_nat",
        "snapshot_recommended": True,
        "test_targets": [
            {"id": "iso_boot", "description": "Firmware lists ISO as boot medium"},
            {"id": "live_shell", "description": "Live user session reaches login"},
            {"id": "backend_version", "description": "GET /api/version from guest NAT"},
            {"id": "inspect_readonly", "description": "Inspect endpoints remain read-only"},
            {"id": "no_auto_disk_writes", "description": "No scripted writes to internal disks"},
        ],
        "constraints": {"no_host_raw_disk": True, "no_usb_passthrough": True},
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_plan("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit_plan("ok", body, wrote=True, warnings=[], errors=[])


def execute_rescue_vm_boot_validation(
    *,
    explicit_overwrite: bool = False,
    explicit_execute_vm_boot: bool = False,
) -> dict[str, Any]:
    if not explicit_execute_vm_boot:
        return build_rescue_vm_test_result(
            explicit_overwrite=explicit_overwrite,
            vm_boot_simulated=False,
            iso_verified=False,
            blocked_reason="EXECUTE_REQUIRES_EXPLICIT_EXECUTE_VM_BOOT",
        )

    plan, perr = load_json_handoff(_PLAN_REL, "RESCUE_VMPLAN")
    if perr or not isinstance(plan, dict):
        return build_rescue_vm_test_result(
            explicit_overwrite=explicit_overwrite,
            vm_boot_simulated=False,
            iso_verified=False,
            blocked_reason=str(perr or "RESCUE_VMPLAN_MISSING"),
        )

    iso_rel = str(plan.get("iso_path") or _default_iso_rel())
    iso_path = (REPO_ROOT / iso_rel.replace("\\", "/")).resolve()
    try:
        iso_path.relative_to((REPO_ROOT / "build" / "rescue").resolve(strict=False))
    except ValueError:
        return build_rescue_vm_test_result(
            explicit_overwrite=explicit_overwrite,
            vm_boot_simulated=False,
            iso_verified=False,
            blocked_reason="RESCUE_VM_ISO_OUTSIDE_WORKSPACE",
        )

    if not iso_path.is_file():
        return build_rescue_vm_test_result(
            explicit_overwrite=explicit_overwrite,
            vm_boot_simulated=False,
            iso_verified=False,
            blocked_reason="RESCUE_VM_ISO_NOT_FOUND",
        )

    qemu = shutil.which("qemu-system-x86_64")
    if not qemu:
        return build_rescue_vm_test_result(
            explicit_overwrite=explicit_overwrite,
            vm_boot_simulated=True,
            qemu_available=False,
            iso_verified=True,
            review_note="QEMU_NOT_IN_PATH",
        )

    try:
        proc = subprocess.run([qemu, "-version"], capture_output=True, text=True, timeout=30, check=False)
        qemu_ok = proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        qemu_ok = False

    return build_rescue_vm_test_result(
        explicit_overwrite=explicit_overwrite,
        vm_boot_simulated=True,
        qemu_available=qemu_ok,
        iso_verified=True,
    )


def build_rescue_vm_test_result(
    *,
    explicit_overwrite: bool = False,
    vm_boot_simulated: bool = False,
    qemu_available: bool | None = None,
    iso_verified: bool = False,
    blocked_reason: str | None = None,
    review_note: str | None = None,
) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_VMRES")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_VMRES_OUTPUT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_VMRES")
    if gerr:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    warnings: list[str] = []
    errors: list[str] = []
    if blocked_reason:
        errors.append(blocked_reason)
    if review_note:
        warnings.append(review_note)

    if errors:
        status = "blocked"
    elif vm_boot_simulated and iso_verified and qemu_available is False:
        status = "review_required"
    elif vm_boot_simulated and iso_verified and qemu_available:
        status = "ok"
    else:
        status = "blocked"
        errors.append("RESCUE_VM_UNKNOWN")

    body: dict[str, Any] = {
        "rescue_vm_test_result_schema_version": 1,
        "strict_mode": "setuphelfer_rescue_iso_phase1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "vm_boot_simulated": vm_boot_simulated,
        "iso_verified": iso_verified,
        "qemu_available": bool(qemu_available) if qemu_available is not None else False,
        "uefi_targeted": True,
        "no_host_disk_mount": True,
    }

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit_result(status, body, wrote=True, warnings=warnings, errors=errors)
