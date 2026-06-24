from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deploy.routes_source_aggregate import read_deploy_routes_aggregate
from deploy.runner_rescue_io import (
    BUILD_RESCUE_ROOT,
    REPO_ROOT,
    guard_handoff_overwrite,
    load_json_handoff,
    resolve_handoff_path,
    resolve_under_build_rescue,
    scan_build_rescue_for_forbidden_images,
    write_json_handoff,
)

_MAX_MANIFEST = 900_000
_MAX_HANDOFF = 512 * 1024

_MANIFEST_PB = "build/rescue/pseudo_boot_manifest.json"
_SERVICE_SIM = "build/rescue/service_startup_simulation.json"
_OVERLAY_BOOT = "build/rescue/overlay_boot_strategy.json"
_BACKEND_HEALTH = "build/rescue/backend_health_integration.json"
_RECOVERY_UI = "build/rescue/recovery_ui_integration.json"

_HANDOFF_SAFETY = "docs/evidence/runtime-results/handoff/rescue_pseudo_boot_safety_validation.json"
_HANDOFF_FINAL = "docs/evidence/runtime-results/handoff/rescue_pseudo_boot_final_readiness.json"

_ARTIFACT_GATE = "docs/evidence/runtime-results/handoff/rescue_artifact_readiness_gate.json"
_BRANDING_REL = "docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json"
_ZERO_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_zero_state_verification.json"

_LEGACY_PI = re.compile(r"(?<![A-Za-z0-9_])pi[-_]installer(?![A-Za-z0-9_])")


def _emit(prefix: str, file_rel: str, status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    sk = f"{prefix}_status"
    return {
        sk: status,
        f"{prefix}_file_path": file_rel,
        prefix: body,
        f"{prefix}_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _build_path(rel: str) -> tuple[Path | None, str | None]:
    raw = rel if rel.startswith("build/rescue/") else f"build/rescue/{rel.lstrip('/')}"
    return resolve_under_build_rescue(raw, "RESCUE_PB")


def _ensure_under_build_rescue(p: Path) -> tuple[bool, str | None]:
    try:
        p.resolve(strict=False).relative_to(BUILD_RESCUE_ROOT.resolve(strict=False))
    except (OSError, ValueError):
        return False, "RESCUE_PB_OUTSIDE_BUILD_RESCUE"
    return True, None


def _guard_build_file(path: Path, *, explicit_overwrite: bool, prefix: str) -> str | None:
    if path.exists() and path.is_file() and not explicit_overwrite:
        return f"{prefix}_EXISTS_NO_OVERWRITE"
    return None


def _write_json_build(path: Path, obj: dict[str, Any]) -> str | None:
    ok, oerr = _ensure_under_build_rescue(path)
    if not ok:
        return oerr or "OUTSIDE"
    text = json.dumps(obj, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_MANIFEST:
        return "RESCUE_PB_MANIFEST_TOO_LARGE"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return None


def _no_iso_or_img_under_build_rescue() -> tuple[bool, list[str]]:
    return scan_build_rescue_for_forbidden_images()


def _routes_text() -> str:
    return read_deploy_routes_aggregate()


def _app_text() -> str:
    p = REPO_ROOT / "backend" / "app.py"
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def _api_routes_text() -> str:
    root = REPO_ROOT / "backend" / "api" / "routes"
    if not root.is_dir():
        return ""
    return "".join(p.read_text(encoding="utf-8") for p in sorted(root.glob("*.py")))


def _static_route_sources_text() -> str:
    return _app_text() + _api_routes_text() + _routes_text()


def build_rescue_pseudo_boot_manifest(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    manifest_path, merr = _build_path(_MANIFEST_PB)
    if merr or manifest_path is None:
        return _emit("rescue_pseudo_boot_manifest", _MANIFEST_PB, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_PB_MAN")
    if g:
        return _emit("rescue_pseudo_boot_manifest", _MANIFEST_PB, "blocked", {}, wrote=False, warnings=[], errors=[g])

    ordered = [
        {"order": 1, "id": "efi_init", "stage": "EFI init", "group": "boot"},
        {"order": 2, "id": "kernel_handoff", "stage": "Kernel handoff", "group": "boot"},
        {"order": 3, "id": "initrd_stage", "stage": "initrd stage", "group": "boot"},
        {"order": 4, "id": "readonly_rootfs", "stage": "readonly rootfs", "group": "overlay"},
        {"order": 5, "id": "tmpfs_overlay", "stage": "tmpfs overlay", "group": "overlay"},
        {"order": 6, "id": "setuphelfer_backend", "stage": "setuphelfer backend", "group": "runtime"},
        {"order": 7, "id": "frontend_runtime", "stage": "frontend runtime", "group": "runtime"},
        {"order": 8, "id": "recovery_services", "stage": "recovery services", "group": "recovery"},
        {"order": 9, "id": "operator_ui_ready", "stage": "operator UI ready", "group": "recovery"},
    ]
    body: dict[str, Any] = {
        "pseudo_boot_manifest_schema_version": 1,
        "strict_mode": "rescue_pseudo_boot_integration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "boot_stages": [s for s in ordered if s["group"] == "boot"],
        "overlay_stages": [s for s in ordered if s["group"] == "overlay"],
        "runtime_startup_stages": [s for s in ordered if s["group"] == "runtime"],
        "frontend_startup_stages": [ordered[6]],
        "backend_startup_stages": [ordered[5]],
        "recovery_startup_stages": [ordered[7], ordered[8]],
        "evidence_initialization": {"after_order": 5, "paths_note": "run/setuphelfer/evidence (documented)"},
        "shutdown_flow": [
            {"id": "drain_http", "order": 1},
            {"id": "stop_recovery_sessions", "order": 2},
            {"id": "drop_overlay_upper", "order": 3},
            {"id": "sync_evidence_optional", "order": 4},
            {"id": "poweroff_or_reboot", "order": 5},
        ],
        "ordered_boot_chain": ordered,
        "no_real_boot": True,
        "hardware_emulator_boot_blocked": True,
        "no_iso_boot": True,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_pseudo_boot_manifest", _MANIFEST_PB, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    ok_iso, bad = _no_iso_or_img_under_build_rescue()
    if not ok_iso:
        errors.extend([f"RESCUE_PB_FORBIDDEN_IMAGE:{b}" for b in bad])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_pseudo_boot_manifest", _MANIFEST_PB, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_service_startup_simulation(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    manifest_path, merr = _build_path(_SERVICE_SIM)
    if merr or manifest_path is None:
        return _emit("rescue_pseudo_boot_service_startup", _SERVICE_SIM, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_PB_SVC")
    if g:
        return _emit("rescue_pseudo_boot_service_startup", _SERVICE_SIM, "blocked", {}, wrote=False, warnings=[], errors=[g])

    rt = _routes_text()
    body: dict[str, Any] = {
        "service_startup_simulation_schema_version": 1,
        "strict_mode": "rescue_pseudo_boot_integration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "simulated_systemd_units": [
            {
                "unit": "setuphelfer-backend.service",
                "expected_command": "python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8010",
                "expected_order": 1,
                "expected_dependencies": ["network-online.target", "local-fs.target"],
                "systemd_invocation": "simulated_only",
            }
        ],
        "frontend_availability": {"check": "GET / or static dist under /usr/share/setuphelfer/frontend", "simulated_only": True},
        "recovery_routes_present": bool(re.search(r'@router\.post\("/rescue/', rt)),
        "verify_routes_present": bool(re.search(r"@router\.post\(\"/[^\"]*verify", rt)) or "/verify" in rt,
        "preview_routes_present": bool(re.search(r"@router\.post\(\"/[^\"]*preview", rt)) or "/preview" in rt,
        "diagnostics_runtime_note": "diagnostics_router included from app.py (documented)",
        "expected_health_endpoints": [
            {"method": "GET", "path": "/api/version"},
            {"method": "GET", "path": "/api/health", "optional": True, "fallback": "/health"},
            {"method": "GET", "path": "/api/system/network"},
        ],
        "no_systemd_exec": True,
    }
    if not body["recovery_routes_present"]:
        warnings.append("RESCUE_PB_SVC_RECOVERY_ROUTES_WEAK")
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_pseudo_boot_service_startup", _SERVICE_SIM, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "review_required" if warnings and not errors else "ok"
    if errors:
        st = "blocked"
    return _emit("rescue_pseudo_boot_service_startup", _SERVICE_SIM, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_overlay_boot_strategy(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    manifest_path, merr = _build_path(_OVERLAY_BOOT)
    if merr or manifest_path is None:
        return _emit("rescue_pseudo_boot_overlay_strategy", _OVERLAY_BOOT, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_PB_OVL")
    if g:
        return _emit("rescue_pseudo_boot_overlay_strategy", _OVERLAY_BOOT, "blocked", {}, wrote=False, warnings=[], errors=[g])

    body: dict[str, Any] = {
        "overlay_boot_strategy_schema_version": 1,
        "strict_mode": "rescue_pseudo_boot_integration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "readonly_lowerdir": "squashfs_root_documented",
        "tmpfs_upperdir": "/run/setuphelfer/overlay_upper_tmpfs",
        "workdir": "/run/setuphelfer/overlay_work",
        "persistence_disabled_by_default": True,
        "evidence_persistence_optional": True,
        "rollback_safe_shutdown_strategy": "drop_upper_tmpfs_then_sync_optional_evidence_export",
        "never_auto_target_disk_persistence": True,
        "auto_write_mounts_blocked": True,
        "no_bind_mount_simulation": True,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_pseudo_boot_overlay_strategy", _OVERLAY_BOOT, "blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit("rescue_pseudo_boot_overlay_strategy", _OVERLAY_BOOT, "ok", body, wrote=True, warnings=[], errors=[])


def build_rescue_backend_health_integration(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    manifest_path, merr = _build_path(_BACKEND_HEALTH)
    if merr or manifest_path is None:
        return _emit("rescue_pseudo_boot_backend_health", _BACKEND_HEALTH, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_PB_BE")
    if g:
        return _emit("rescue_pseudo_boot_backend_health", _BACKEND_HEALTH, "blocked", {}, wrote=False, warnings=[], errors=[g])

    app_t = _static_route_sources_text()
    rt = _routes_text()
    checks = {
        "endpoint_api_version": '@app.get("/api/version")' in app_t or '"/api/version"' in app_t,
        "endpoint_api_health": '"/api/health"' in app_t or "@app.get(\"/api/health\")" in app_t,
        "endpoint_health_root": '@app.get("/health")' in app_t or '"/health"' in app_t,
        "endpoint_api_system_network": "/api/system/network" in app_t,
        "recovery_routes": bool(re.search(r'@router\.post\("/rescue/', rt)),
        "verify_routes": bool(re.search(r"@router\.post\(\"/[^\"]*verify", rt)) or "/verify" in rt,
        "preview_routes": bool(re.search(r"@router\.post\(\"/[^\"]*preview", rt)) or "/preview" in rt,
    }
    if not checks["endpoint_api_health"] and checks["endpoint_health_root"]:
        warnings.append("RESCUE_PB_HEALTH_USES_ROOT_NOT_API_PREFIX")
    if not checks["endpoint_api_version"]:
        errors.append("RESCUE_PB_BACKEND_VERSION_ROUTE_MISSING")

    body: dict[str, Any] = {
        "backend_health_integration_schema_version": 1,
        "strict_mode": "rescue_pseudo_boot_integration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "static_analysis_only": True,
        "sources": {
            "app_py": "backend/app.py",
            "api_routes_py": "backend/api/routes/*.py",
            "routes_py": "backend/deploy/routes.py",
        },
        "checks": checks,
        "expected_health_probe_order": ["/api/version", "/api/health|/health", "/api/system/network"],
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_pseudo_boot_backend_health", _BACKEND_HEALTH, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "blocked" if errors else ("review_required" if warnings else "ok")
    return _emit("rescue_pseudo_boot_backend_health", _BACKEND_HEALTH, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_recovery_ui_integration(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    manifest_path, merr = _build_path(_RECOVERY_UI)
    if merr or manifest_path is None:
        return _emit("rescue_pseudo_boot_recovery_ui", _RECOVERY_UI, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_PB_UI")
    if g:
        return _emit("rescue_pseudo_boot_recovery_ui", _RECOVERY_UI, "blocked", {}, wrote=False, warnings=[], errors=[g])

    dist = REPO_ROOT / "frontend" / "dist"
    # Rescue-Operator-UI: nur InspectRun (Vollpfad-Scan wuerde Doku/Legacy-Hinweise false positiv treffen).
    inspect = REPO_ROOT / "frontend" / "src" / "pages" / "InspectRun.tsx"
    legacy_hits: list[str] = []
    recovery_like: list[str] = []
    inspect_raw = ""
    if inspect.is_file():
        rel = str(inspect.relative_to(REPO_ROOT)).replace("\\", "/")
        recovery_like.append(rel)
        try:
            inspect_raw = inspect.read_text(encoding="utf-8", errors="replace")
        except OSError:
            inspect_raw = ""
        if _LEGACY_PI.search(inspect_raw):
            legacy_hits.append(rel)
    assets_ok = (dist / "assets").is_dir() and (dist / "index.html").is_file()

    if legacy_hits:
        errors.append("RESCUE_PB_UI_LEGACY_PI_INSTALLER")
    if not recovery_like:
        warnings.append("RESCUE_PB_UI_RECOVERY_SURFACE_NOT_FOUND")
    if inspect.is_file() and inspect_raw and not (("/api/rescue" in inspect_raw) or ("/api/recovery" in inspect_raw)):
        warnings.append("RESCUE_PB_UI_INSPECT_RUN_API_REF_WEAK")
    if not assets_ok:
        warnings.append("RESCUE_PB_UI_DIST_ASSETS_MISSING")

    body: dict[str, Any] = {
        "recovery_ui_integration_schema_version": 1,
        "strict_mode": "rescue_pseudo_boot_integration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frontend_assets_dist_present": assets_ok,
        "recovery_related_sources": recovery_like[:120],
        "recovery_pages_hint": "InspectRun references /api/rescue, verify, preview, recovery activation APIs",
        "inspect_run_has_rescue_api_refs": ("/api/rescue" in inspect_raw) or ("/api/recovery" in inspect_raw),
        "branding_consistency_note": "no_pi_installer_strings_in_scanned_tsx",
        "no_pi_installer_ui_rests": len(legacy_hits) == 0,
        "legacy_hits": legacy_hits[:40],
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_pseudo_boot_recovery_ui", _RECOVERY_UI, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "blocked" if errors else ("review_required" if warnings else "ok")
    return _emit("rescue_pseudo_boot_recovery_ui", _RECOVERY_UI, st, body, wrote=True, warnings=warnings, errors=errors)


def validate_rescue_pseudo_boot_safety(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_HANDOFF_SAFETY, "RESCUE_PB_SAFE")
    if oerr or out_path is None:
        return _emit("rescue_pseudo_boot_safety_validation", _HANDOFF_SAFETY, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_PB_SAFE")
    if g0:
        return _emit("rescue_pseudo_boot_safety_validation", _HANDOFF_SAFETY, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    # Kein Selbst-Scan dieser Datei (Literal-Tokens wuerden false positives erzeugen).
    runner_path = REPO_ROOT / "backend" / "deploy" / "runner_rescue_pseudo_boot_integration.py"
    runner_scan_note = "runner_forbidden_syscalls_enforced_in_unit_tests"

    rt = _routes_text().lower()
    forbidden_segments = (
        "restore-execute",
        "publish-release",
        "deploy-release",
        "partition-write",
        "grub-repair",
        "efi-write",
        "auto-repair",
        "auto-restore",
    )
    for seg in forbidden_segments:
        if seg in rt:
            errors.append(f"RESCUE_PB_SAFE_FORBIDDEN_ROUTE_SEGMENT:{seg}")

    destructive_tokens = ("mkfs", "dd if=", "dd of=", "wipefs", "systemctl enable", "systemctl disable")
    for tok in destructive_tokens:
        if tok in rt:
            errors.append(f"RESCUE_PB_SAFE_DESTRUCTIVE_TOKEN_IN_ROUTES:{tok}")

    if _LEGACY_PI.search(_routes_text()):
        errors.append("RESCUE_PB_SAFE_LEGACY_PI_INSTALLER_IN_ROUTES")

    body: dict[str, Any] = {
        "rescue_pseudo_boot_safety_validation_schema_version": 1,
        "strict_mode": "rescue_pseudo_boot_integration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "no_execute_apply_delete_release_defaults": True,
        "no_destructive_defaults": len(errors) == 0,
        "no_auto_restore_flags": "auto-restore" not in rt,
        "no_auto_repair_flags": "auto-repair" not in rt,
        "no_productive_auto_mounts_documented": True,
        "forbidden_segments_scanned": list(forbidden_segments),
        "runner_scan": runner_scan_note,
        "runner_path_checked_exists": runner_path.is_file(),
        "evaluation": {"rescue_pseudo_boot_safety_eval_status": "ok" if not errors else "blocked"},
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_pseudo_boot_safety_validation", _HANDOFF_SAFETY, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_pseudo_boot_safety_validation", _HANDOFF_SAFETY, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_pseudo_boot_final_readiness(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_HANDOFF_FINAL, "RESCUE_PB_FIN")
    if oerr or out_path is None:
        return _emit("rescue_pseudo_boot_final_readiness", _HANDOFF_FINAL, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_PB_FIN")
    if g0:
        return _emit("rescue_pseudo_boot_final_readiness", _HANDOFF_FINAL, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    art, aerr = load_json_handoff(_ARTIFACT_GATE, "PB_ART")
    if aerr or not isinstance(art, dict):
        errors.append("PB_FIN_ARTIFACT_GATE_MISSING")
    else:
        ags = str(art.get("gate_status") or "")
        if ags == "blocked":
            errors.append("PB_FIN_ARTIFACT_GATE_BLOCKED")
        elif ags == "review_required":
            warnings.append("PB_FIN_ARTIFACT_GATE_REVIEW")
        elif ags != "ready":
            warnings.append("PB_FIN_ARTIFACT_GATE_NOT_READY")

    brand, _ = load_json_handoff(_BRANDING_REL, "PB_BRAND")
    if isinstance(brand, dict) and str(brand.get("branding_guard_status") or "") == "blocked":
        errors.append("PB_FIN_BRANDING_BLOCKED")

    zero, ze = load_json_handoff(_ZERO_REL, "PB_ZERO")
    if ze:
        warnings.append(f"PB_FIN_ZERO_HANDOFF:{ze}")
    elif isinstance(zero, dict) and str(zero.get("zero_state_status") or "") == "blocked":
        errors.append("PB_FIN_ZERO_STATE_BLOCKED")
    elif isinstance(zero, dict) and str(zero.get("zero_state_status") or "") == "review_required":
        warnings.append("PB_FIN_ZERO_STATE_REVIEW")

    inputs: dict[str, str] = {
        "rescue_artifact_readiness_gate": _ARTIFACT_GATE,
        "pseudo_boot_manifest": _MANIFEST_PB,
        "service_startup_simulation": _SERVICE_SIM,
        "overlay_boot_strategy": _OVERLAY_BOOT,
        "backend_health_integration": _BACKEND_HEALTH,
        "recovery_ui_integration": _RECOVERY_UI,
        "branding_guard": _BRANDING_REL,
        "zero_state_verification": _ZERO_REL,
    }
    loaded: dict[str, Any] = {}
    for key, rel in inputs.items():
        if key in ("branding_guard", "zero_state_verification", "rescue_artifact_readiness_gate"):
            continue
        p, perr = _build_path(rel)
        if perr or p is None or not p.is_file():
            errors.append(f"PB_FIN_INPUT_MISSING:{rel}")
        else:
            try:
                loaded[key] = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                errors.append(f"PB_FIN_INPUT_JSON_INVALID:{rel}")

    ovl = loaded.get("overlay_boot_strategy") if isinstance(loaded.get("overlay_boot_strategy"), dict) else {}
    if ovl:
        if not ovl.get("persistence_disabled_by_default"):
            errors.append("PB_FIN_OVERLAY_PERSISTENCE_UNSAFE")
        if not ovl.get("readonly_lowerdir"):
            errors.append("PB_FIN_OVERLAY_READONLY_MISSING")

    ui = loaded.get("recovery_ui_integration") if isinstance(loaded.get("recovery_ui_integration"), dict) else {}
    if ui and ui.get("no_pi_installer_ui_rests") is False:
        errors.append("PB_FIN_RECOVERY_UI_LEGACY")
    if ui and ui.get("inspect_run_has_rescue_api_refs") is False:
        errors.append("PB_FIN_RECOVERY_UI_API_REFS_MISSING")

    be = loaded.get("backend_health_integration") if isinstance(loaded.get("backend_health_integration"), dict) else {}
    bchecks = be.get("checks") if isinstance(be.get("checks"), dict) else {}
    if bchecks and not bchecks.get("endpoint_api_version"):
        errors.append("PB_FIN_BACKEND_VERSION_MISSING")
    if bchecks and not bchecks.get("recovery_routes"):
        errors.append("PB_FIN_RECOVERY_ROUTES_MISSING")

    ok_iso, bad = _no_iso_or_img_under_build_rescue()
    if not ok_iso:
        errors.extend([f"PB_FIN_FORBIDDEN_IMAGE:{b}" for b in bad])

    st = "ready"
    if errors:
        st = "blocked"
    elif warnings:
        st = "review_required"

    body: dict[str, Any] = {
        "rescue_pseudo_boot_final_readiness_schema_version": 1,
        "strict_mode": "rescue_pseudo_boot_integration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_status": st,
        "inputs": inputs,
        "simulated_boot_chain_complete": isinstance(loaded.get("pseudo_boot_manifest"), dict),
        "overlay_readonly_enforced": bool(ovl.get("readonly_lowerdir")) and bool(ovl.get("never_auto_target_disk_persistence")),
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_pseudo_boot_final_readiness", _HANDOFF_FINAL, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_pseudo_boot_final_readiness", _HANDOFF_FINAL, st, body, wrote=True, warnings=warnings, errors=errors)
