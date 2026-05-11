from __future__ import annotations

import importlib.util
import os
import re
from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import REPO_ROOT, guard_handoff_overwrite, load_json_handoff, resolve_handoff_path, write_json_handoff

_MAX_BASE = 768 * 1024
_MAX_LARGE = 1_200_000

_BASELINE_REL = "docs/evidence/runtime-results/handoff/rescue_iso_baseline.json"
_FS_LAYOUT_REL = "docs/evidence/runtime-results/handoff/rescue_iso_filesystem_layout.json"
_OFFLINE_REL = "docs/evidence/runtime-results/handoff/offline_recovery_runtime_validation.json"
_BOOTFLOW_REL = "docs/evidence/runtime-results/handoff/rescue_bootflow_simulation.json"
_SAFETY_REL = "docs/evidence/runtime-results/handoff/rescue_iso_safety_validation.json"
_FINAL_REL = "docs/evidence/runtime-results/handoff/rescue_iso_final_readiness_gate.json"
_BUILD_PLAN_REL = "docs/evidence/runtime-results/handoff/rescue_iso_build_plan.json"

_DEBIAN_PLAN_HANDOFF = "docs/evidence/runtime-results/handoff/rescue_debian_live_build_plan.json"
_LIVE_CFG_HANDOFF = "docs/evidence/runtime-results/handoff/rescue_live_build_config.json"
_BRANDING_REL = "docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json"
_ZERO_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_zero_state_verification.json"
_FRG_REL = "docs/evidence/runtime-results/handoff/rescue_final_recovery_readiness_gate.json"


def _emit_simple(prefix: str, file_rel: str, status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    sk = f"{prefix}_status"
    out = {
        sk: status,
        f"{prefix}_file_path": file_rel,
        prefix: body,
        f"{prefix}_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
    return out


def _routes_text() -> str:
    p = REPO_ROOT / "backend" / "deploy" / "routes.py"
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def _count_rescue_posts(txt: str) -> int:
    return len(re.findall(r'@router\.post\("/rescue/', txt))


def build_rescue_iso_baseline(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_BASELINE_REL, "RESCUE_ISO_BASE")
    if oerr or out_path is None:
        return _emit_simple("rescue_iso_baseline", _BASELINE_REL, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_ISO_BASE_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ISO_BASE")
    if gerr:
        return _emit_simple("rescue_iso_baseline", _BASELINE_REL, "blocked", {}, wrote=False, warnings=[], errors=[gerr])

    warnings: list[str] = []
    errors: list[str] = []

    controlled = REPO_ROOT / "scripts" / "rescue" / "build-rescue-iso-controlled.sh"
    build_sh = REPO_ROOT / "scripts" / "rescue" / "build-rescue-iso.sh"
    debian_runner = REPO_ROOT / "backend" / "deploy" / "runner_rescue_debian_live_build_plan.py"
    backend_pkg = REPO_ROOT / "backend" / "deploy"
    frontend_pkg = REPO_ROOT / "frontend" / "package.json"

    h_debian = (REPO_ROOT / _DEBIAN_PLAN_HANDOFF).is_file()
    h_live = (REPO_ROOT / _LIVE_CFG_HANDOFF).is_file()

    checks: dict[str, Any] = {
        "debian_live_documented": h_debian or h_live,
        "live_build_or_documented_alternative": h_debian or h_live or debian_runner.is_file(),
        "boot_grub_structure_documented": build_sh.is_file() or controlled.is_file(),
        "efi_structure_documented": controlled.is_file(),
        "squashfs_readiness": "documented_only_no_iso_write",
        "overlayfs_readiness": "documented_only",
        "setuphelfer_backend_present": backend_pkg.is_dir(),
        "frontend_build_present": frontend_pkg.is_file(),
        "recovery_modules_present": _count_rescue_posts(_routes_text()) >= 12,
        "safety_modules_present": (REPO_ROOT / "backend" / "deploy" / "runner_rescue_readonly_mount_orchestrator.py").is_file(),
    }

    if not controlled.is_file():
        errors.append("RESCUE_ISO_BASELINE_MISSING_CONTROLLED_BUILD_SCRIPT")
    if not debian_runner.is_file():
        errors.append("RESCUE_ISO_BASELINE_MISSING_DEBIAN_PLAN_RUNNER")
    if not (h_debian or h_live):
        if os.environ.get("RESCUE_ISO_PIPELINE_TEST") == "missing_debian":
            errors.append("RESCUE_ISO_BASELINE_DEBIAN_LIVE_HANDOFF_MISSING_SIMULATED")
        else:
            warnings.append("RESCUE_ISO_BASELINE_DEBIAN_LIVE_HANDOFF_MISSING")
    if not checks["recovery_modules_present"]:
        warnings.append("RESCUE_ISO_BASELINE_RESCUE_API_COUNT_LOW")

    st = "ok"
    if errors:
        st = "blocked"
    elif warnings:
        st = "review_required"

    body: dict[str, Any] = {
        "rescue_iso_baseline_schema_version": 1,
        "strict_mode": "rescue_iso_readiness_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checks": checks,
        "iso_build_executed": False,
        "publish_forbidden": True,
        "evaluation": {"rescue_iso_baseline_eval_status": st},
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BASE)
    if werr:
        return _emit_simple("rescue_iso_baseline", _BASELINE_REL, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit_simple("rescue_iso_baseline", _BASELINE_REL, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_iso_filesystem_layout(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_FS_LAYOUT_REL, "RESCUE_ISO_FSL")
    if oerr or out_path is None:
        return _emit_simple("rescue_iso_filesystem_layout", _FS_LAYOUT_REL, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_ISO_FSL_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ISO_FSL")
    if gerr:
        return _emit_simple("rescue_iso_filesystem_layout", _FS_LAYOUT_REL, "blocked", {}, wrote=False, warnings=[], errors=[gerr])

    layout: dict[str, Any] = {
        "paths": [
            {"path": "/opt/setuphelfer", "purpose": "application_bundle", "mode": "readonly_overlay"},
            {"path": "/etc/setuphelfer", "purpose": "config", "mode": "readonly_overlay"},
            {"path": "/var/log/setuphelfer", "purpose": "logs", "mode": "tmpfs_or_overlay"},
            {"path": "/run/setuphelfer", "purpose": "temporary_runtime", "mode": "tmpfs"},
            {"path": "/run/setuphelfer/evidence", "purpose": "recovery_evidence", "mode": "tmpfs"},
            {"path": "/run/setuphelfer/backup-discovery", "purpose": "backup_discovery_scratch", "mode": "tmpfs"},
        ],
        "readonly_overlay_strategy": "upper_tmpfs_lower_squashfs_documented_only",
        "no_iso_materialization_in_this_phase": True,
    }
    body: dict[str, Any] = {
        "rescue_iso_filesystem_layout_schema_version": 1,
        "strict_mode": "rescue_iso_readiness_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "layout": layout,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BASE)
    if werr:
        return _emit_simple("rescue_iso_filesystem_layout", _FS_LAYOUT_REL, "blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit_simple("rescue_iso_filesystem_layout", _FS_LAYOUT_REL, "ok", body, wrote=True, warnings=[], errors=[])


def validate_offline_recovery_runtime(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OFFLINE_REL, "RESCUE_OFFRT")
    if oerr or out_path is None:
        return _emit_simple("offline_recovery_runtime_validation", _OFFLINE_REL, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_OFFRT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_OFFRT")
    if gerr:
        return _emit_simple("offline_recovery_runtime_validation", _OFFLINE_REL, "blocked", {}, wrote=False, warnings=[], errors=[gerr])

    warnings: list[str] = []
    errors: list[str] = []

    rt = _routes_text()
    n_rescue = _count_rescue_posts(rt)
    recovery_api_surface_ok = n_rescue >= 20

    mod_checks: list[dict[str, Any]] = []
    for mod in ("deploy.runner_rescue_io", "deploy.runner_rescue_storage_discovery", "deploy.runner_rescue_backup_discovery_verify"):
        spec = importlib.util.find_spec(mod)
        mod_checks.append({"module": mod, "importable": spec is not None and spec.loader is not None})

    if not all(x["importable"] for x in mod_checks):
        errors.append("RESCUE_OFFLINE_MODULE_IMPORT_FAILED")

    if not recovery_api_surface_ok:
        errors.append("RESCUE_OFFLINE_RESCUE_API_SURFACE_INSUFFICIENT")

    brand, _ = load_json_handoff(_BRANDING_REL, "OFFRT_BRAND")
    if not isinstance(brand, dict):
        warnings.append("RESCUE_OFFLINE_BRANDING_HANDOFF_MISSING")
    elif str(brand.get("branding_guard_status") or "") == "blocked":
        errors.append("RESCUE_OFFLINE_BRANDING_BLOCKED")

    zero, _ = load_json_handoff(_ZERO_REL, "OFFRT_ZERO")
    if isinstance(zero, dict):
        if str(zero.get("zero_state_status") or "") == "blocked":
            errors.append("RESCUE_OFFLINE_ZERO_STATE_BLOCKED")

    verify_preview_ok = all(
        x in rt for x in ("runner_rescue_backup_discovery_verify", "runner_rescue_restore_preview_orchestrator")
    ) or ("backup-discovery-verify" in rt and "restore-preview" in rt)

    if not verify_preview_ok:
        errors.append("RESCUE_OFFLINE_VERIFY_PREVIEW_MISSING")

    st = "ok"
    if errors:
        st = "blocked"
    elif warnings:
        st = "review_required"

    body: dict[str, Any] = {
        "offline_recovery_runtime_validation_schema_version": 1,
        "strict_mode": "rescue_iso_readiness_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "python_module_checks": mod_checks,
        "rescue_post_route_count": n_rescue,
        "recovery_api_surface_ok": recovery_api_surface_ok,
        "frontend_assets_path": "frontend/package.json",
        "verify_preview_modules_ok": verify_preview_ok,
        "branding_guard_handoff_present": isinstance(brand, dict),
        "zero_state_handoff_present": isinstance(zero, dict),
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_LARGE)
    if werr:
        return _emit_simple("offline_recovery_runtime_validation", _OFFLINE_REL, "blocked", body, wrote=False, warnings=warnings, errors=[werr])

    merged = dict(body)
    merged["evaluation"] = {
        "offline_recovery_runtime_validation_eval_status": st,
        "recovery_api_surface_ok": recovery_api_surface_ok,
    }
    werr2 = write_json_handoff(out_path, merged, max_bytes=_MAX_LARGE)
    if werr2:
        return _emit_simple("offline_recovery_runtime_validation", _OFFLINE_REL, "blocked", merged, wrote=False, warnings=warnings, errors=[werr2])
    return _emit_simple("offline_recovery_runtime_validation", _OFFLINE_REL, st, merged, wrote=True, warnings=warnings, errors=errors)


def build_rescue_bootflow_simulation(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_BOOTFLOW_REL, "RESCUE_BOOTSIM")
    if oerr or out_path is None:
        return _emit_simple("rescue_bootflow_simulation", _BOOTFLOW_REL, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_BOOTSIM_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BOOTSIM")
    if gerr:
        return _emit_simple("rescue_bootflow_simulation", _BOOTFLOW_REL, "blocked", {}, wrote=False, warnings=[], errors=[gerr])

    steps = [
        {"id": 1, "name": "iso_boot", "simulated": True, "vm_execute": False},
        {"id": 2, "name": "overlay_mount", "simulated": True, "vm_execute": False},
        {"id": 3, "name": "setuphelfer_backend_start", "simulated": True, "vm_execute": False},
        {"id": 4, "name": "frontend_available", "simulated": True, "vm_execute": False},
        {"id": 5, "name": "backup_discovery", "simulated": True, "vm_execute": False},
        {"id": 6, "name": "verify", "simulated": True, "vm_execute": False},
        {"id": 7, "name": "restore_preview", "simulated": True, "vm_execute": False},
        {"id": 8, "name": "recovery_guide", "simulated": True, "vm_execute": False},
        {"id": 9, "name": "shutdown", "simulated": True, "vm_execute": False},
    ]
    body: dict[str, Any] = {
        "rescue_bootflow_simulation_schema_version": 1,
        "strict_mode": "rescue_iso_readiness_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "steps": steps,
        "no_vm_execution": True,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BASE)
    if werr:
        return _emit_simple("rescue_bootflow_simulation", _BOOTFLOW_REL, "blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit_simple("rescue_bootflow_simulation", _BOOTFLOW_REL, "ok", body, wrote=True, warnings=[], errors=[])


def validate_rescue_iso_safety(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_SAFETY_REL, "RESCUE_ISO_SAFE")
    if oerr or out_path is None:
        return _emit_simple("rescue_iso_safety_validation", _SAFETY_REL, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_ISO_SAFE_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ISO_SAFE")
    if gerr:
        return _emit_simple("rescue_iso_safety_validation", _SAFETY_REL, "blocked", {}, wrote=False, warnings=[], errors=[gerr])

    rt = _routes_text().lower()
    warnings: list[str] = []
    errors: list[str] = []

    forbidden_segments = (
        "restore-execute",
        "publish-release",
        "deploy-release",
        "partition-write",
        "grub-repair",
        "efi-write",
        "auto-repair",
    )
    for seg in forbidden_segments:
        if seg in rt:
            errors.append(f"RESCUE_ISO_SAFETY_FORBIDDEN_ROUTE_SEGMENT:{seg}")

    destructive_tokens = ("mkfs", "dd if=", "dd of=", "wipefs", "systemctl enable", "systemctl disable")
    for tok in destructive_tokens:
        if tok in rt:
            errors.append(f"RESCUE_ISO_SAFETY_DESTRUCTIVE_TOKEN_IN_ROUTES:{tok}")

    st = "ok" if not errors else "blocked"
    body: dict[str, Any] = {
        "rescue_iso_safety_validation_schema_version": 1,
        "strict_mode": "rescue_iso_readiness_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "readonly_default": True,
        "no_auto_restore_paths": True,
        "no_destructive_defaults": len(errors) == 0,
        "no_productive_auto_mounts": True,
        "no_auto_writes": True,
        "forbidden_segments_scanned": list(forbidden_segments),
        "evaluation": {"rescue_iso_safety_validation_eval_status": st},
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BASE)
    if werr:
        return _emit_simple("rescue_iso_safety_validation", _SAFETY_REL, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit_simple("rescue_iso_safety_validation", _SAFETY_REL, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_iso_final_readiness_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_FINAL_REL, "RESCUE_ISO_FRG")
    if oerr or out_path is None:
        return _emit_simple("rescue_iso_final_readiness_gate", _FINAL_REL, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_ISO_FRG_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ISO_FRG")
    if gerr:
        return _emit_simple("rescue_iso_final_readiness_gate", _FINAL_REL, "blocked", {}, wrote=False, warnings=[], errors=[gerr])

    warnings: list[str] = []
    errors: list[str] = []

    inputs: dict[str, tuple[str, str]] = {
        "baseline": (_BASELINE_REL, "FRG_BASE"),
        "filesystem_layout": (_FS_LAYOUT_REL, "FRG_FSL"),
        "offline_runtime": (_OFFLINE_REL, "FRG_OFF"),
        "bootflow": (_BOOTFLOW_REL, "FRG_BOOT"),
        "safety": (_SAFETY_REL, "FRG_SAFE"),
        "branding_guard": (_BRANDING_REL, "FRG_BRAND"),
        "zero_state_verification": (_ZERO_REL, "FRG_ZERO"),
        "final_recovery_readiness_gate": (_FRG_REL, "FRG_FRG"),
    }

    loaded: dict[str, Any] = {}
    for key, (rel, pfx) in inputs.items():
        data, err = load_json_handoff(rel, pfx)
        if err:
            errors.append(f"FRG_INPUT_MISSING:{key}")
        loaded[key] = data

    base = loaded.get("baseline") if isinstance(loaded.get("baseline"), dict) else {}
    bev = base.get("evaluation") if isinstance(base.get("evaluation"), dict) else {}
    if str(bev.get("rescue_iso_baseline_eval_status") or "") == "blocked":
        errors.append("FRG_BASELINE_BLOCKED")
    elif str(bev.get("rescue_iso_baseline_eval_status") or "") == "review_required":
        warnings.append("FRG_BASELINE_REVIEW")

    off = loaded.get("offline_runtime") if isinstance(loaded.get("offline_runtime"), dict) else {}
    evo = off.get("evaluation") if isinstance(off.get("evaluation"), dict) else {}
    if str(evo.get("offline_recovery_runtime_validation_eval_status") or "") == "blocked":
        errors.append("FRG_OFFLINE_RUNTIME_BLOCKED")
    elif str(evo.get("offline_recovery_runtime_validation_eval_status") or "") == "review_required":
        warnings.append("FRG_OFFLINE_RUNTIME_REVIEW")
    elif evo.get("recovery_api_surface_ok") is False:
        errors.append("FRG_RECOVERY_API_SURFACE_FAIL")

    safe = loaded.get("safety") if isinstance(loaded.get("safety"), dict) else {}
    sev = safe.get("evaluation") if isinstance(safe.get("evaluation"), dict) else {}
    if str(sev.get("rescue_iso_safety_validation_eval_status") or "") == "blocked":
        errors.append("FRG_SAFETY_FAILED")
    if os.environ.get("RESCUE_ISO_PIPELINE_TEST") == "safety_fail":
        errors.append("FRG_SAFETY_FORCED_FAIL")

    brand = loaded.get("branding_guard") if isinstance(loaded.get("branding_guard"), dict) else {}
    if str(brand.get("branding_guard_status") or "") == "blocked":
        errors.append("FRG_BRANDING_BLOCKED")

    zero = loaded.get("zero_state_verification") if isinstance(loaded.get("zero_state_verification"), dict) else {}
    if str(zero.get("zero_state_status") or "") == "blocked":
        errors.append("FRG_ZERO_STATE_BLOCKED")

    frg = loaded.get("final_recovery_readiness_gate") if isinstance(loaded.get("final_recovery_readiness_gate"), dict) else {}
    inner: dict[str, Any] = {}
    if isinstance(frg, dict):
        inner = frg.get("rescue_final_recovery_readiness_gate") if isinstance(frg.get("rescue_final_recovery_readiness_gate"), dict) else frg
    if isinstance(inner, dict) and str(inner.get("gate_status") or "") == "blocked":
        errors.append("FRG_FINAL_RECOVERY_BLOCKED")

    if not isinstance(loaded.get("filesystem_layout"), dict):
        errors.append("FRG_FILESYSTEM_LAYOUT_MISSING")

    status = "ready"
    if errors:
        status = "blocked"
    elif warnings or (isinstance(inner, dict) and str(inner.get("gate_status") or "") == "review_required"):
        status = "review_required"
        if isinstance(inner, dict) and str(inner.get("gate_status") or "") == "review_required":
            warnings.append("FRG_FINAL_RECOVERY_REVIEW")

    body: dict[str, Any] = {
        "rescue_iso_final_readiness_gate_schema_version": 1,
        "strict_mode": "rescue_iso_readiness_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_status": status,
        "inputs": {k: v[0] for k, v in inputs.items()},
        "publish_forbidden": True,
        "release_forbidden": True,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BASE)
    if werr:
        return _emit_simple("rescue_iso_final_readiness_gate", _FINAL_REL, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit_simple("rescue_iso_final_readiness_gate", _FINAL_REL, status, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_iso_build_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_BUILD_PLAN_REL, "RESCUE_ISO_BPLAN")
    if oerr or out_path is None:
        return _emit_simple("rescue_iso_build_plan", _BUILD_PLAN_REL, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_ISO_BPLAN_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ISO_BPLAN")
    if gerr:
        return _emit_simple("rescue_iso_build_plan", _BUILD_PLAN_REL, "blocked", {}, wrote=False, warnings=[], errors=[gerr])

    body: dict[str, Any] = {
        "rescue_iso_build_plan_schema_version": 1,
        "strict_mode": "rescue_iso_readiness_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "debian_packages_required": ["live-build", "debootstrap", "squashfs-tools", "xorriso", "grub-efi-amd64-bin", "dosfstools"],
        "build_order": ["bootstrap", "chroot_prep", "overlay", "squashfs", "iso9660", "efi_img"],
        "overlay_concept": "tmpfs_upper_squashfs_lower",
        "efi_concept": "fat16_esp_partition_grub_efi",
        "persistence_strategy": "toram_no_persistence_by_default",
        "later_ventoy_compatibility": "review_required",
        "later_raspberry_pi": False,
        "later_secure_boot": "review_required",
        "iso_build_execute_forbidden_in_this_phase": True,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_LARGE)
    if werr:
        return _emit_simple("rescue_iso_build_plan", _BUILD_PLAN_REL, "blocked", body, wrote=False, warnings=[], errors=[werr])
    warnings = ["RESCUE_ISO_BUILD_PLAN_ADVISORY_ONLY"] if body.get("later_secure_boot") == "review_required" else []
    st = "review_required" if warnings else "ok"
    return _emit_simple("rescue_iso_build_plan", _BUILD_PLAN_REL, st, body, wrote=True, warnings=warnings, errors=[])
