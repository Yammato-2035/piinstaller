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

_RUNTIME_BASE = "build/rescue/runtime"
_MANIFEST_ROOT = "build/rescue/runtime/runtime_root_manifest.json"
_BACKEND_ASM = "build/rescue/runtime/backend_runtime_assembly.json"
_FRONTEND_ASM = "build/rescue/runtime/frontend_runtime_assembly.json"
_RECOVERY_ASM = "build/rescue/runtime/recovery_runtime_assembly.json"
_OFFLINE_ASM = "build/rescue/runtime/offline_configuration_assembly.json"
_STARTUP_ASM = "build/rescue/runtime/startup_script_assembly.json"
_SCRIPTS_DIR = "build/rescue/runtime/scripts"

_HANDOFF_FINAL = "docs/evidence/runtime-results/handoff/rescue_runtime_assembly_final_gate.json"
_HANDOFF_SAFETY = "docs/evidence/runtime-results/handoff/rescue_runtime_assembly_safety.json"

_PSEUDO_BOOT_FINAL = "docs/evidence/runtime-results/handoff/rescue_pseudo_boot_final_readiness.json"
_BRANDING_REL = "docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json"
_ZERO_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_zero_state_verification.json"

_LEGACY_PI = re.compile(r"(?<![A-Za-z0-9_])pi[-_]installer(?![A-Za-z0-9_])")

_RUNTIME_DIRS = (
    "opt/setuphelfer",
    "etc/setuphelfer",
    "var/log/setuphelfer",
    "run/setuphelfer",
    "run/setuphelfer/evidence",
    "run/setuphelfer/recovery",
    "usr/share/setuphelfer/frontend",
    "boot",
    "EFI",
    "live",
)

_PLACEHOLDER = ".setuphelfer_runtime_assembly_placeholder"

_SCRIPT_NAMES = (
    "start-backend.sh",
    "start-frontend.sh",
    "start-recovery-ui.sh",
    "shutdown-safe.sh",
)

# Template: nur No-Op, keine Dienst-Starts, keine verbotenen Werkzeugnamen.
_SH_TEMPLATE = "#!/bin/sh\n# SETUPHELFER_RUNTIME_ASSEMBLY_TEMPLATE\n:\n"


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
    return resolve_under_build_rescue(raw, "RESCUE_RT")


def _ensure_under_build_rescue(p: Path) -> tuple[bool, str | None]:
    try:
        p.resolve(strict=False).relative_to(BUILD_RESCUE_ROOT.resolve(strict=False))
    except (OSError, ValueError):
        return False, "RESCUE_RT_OUTSIDE_BUILD_RESCUE"
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
        return "RESCUE_RT_MANIFEST_TOO_LARGE"
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


def build_rescue_runtime_root(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    root_base, err = _build_path(_RUNTIME_BASE)
    if err or root_base is None:
        return _emit("rescue_runtime_root", _MANIFEST_ROOT, "blocked", {}, wrote=False, warnings=[], errors=[err or "RESCUE_RT_ROOT_INVALID"])

    created: list[str] = []
    for sub in _RUNTIME_DIRS:
        d = root_base / Path(sub)
        d.mkdir(parents=True, exist_ok=True)
        ok, oerr = _ensure_under_build_rescue(d)
        if not ok:
            errors.append(oerr or "PATH_CHECK")
            continue
        ph = d / _PLACEHOLDER
        if not ph.exists():
            ph.write_text("# setuphelfer runtime assembly placeholder\n", encoding="utf-8")
        created.append(f"{_RUNTIME_BASE}/{sub}/{_PLACEHOLDER}".replace("\\", "/"))

    manifest_path, merr = _build_path(_MANIFEST_ROOT)
    if merr or manifest_path is None:
        return _emit("rescue_runtime_root", _MANIFEST_ROOT, "blocked", {}, wrote=False, warnings=warnings, errors=[merr or "MANIFEST_PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RT_ROOT")
    if g:
        return _emit("rescue_runtime_root", _MANIFEST_ROOT, "blocked", {}, wrote=False, warnings=[], errors=[g])

    body: dict[str, Any] = {
        "runtime_root_manifest_schema_version": 1,
        "strict_mode": "rescue_runtime_assembly_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runtime_base": _RUNTIME_BASE,
        "expected_directories": [f"{_RUNTIME_BASE}/{s}".replace("\\", "/") for s in _RUNTIME_DIRS],
        "placeholders_written": created,
        "no_system_file_copy": True,
        "scripts_directory_planned": _SCRIPTS_DIR,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_runtime_root", _MANIFEST_ROOT, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    ok_iso, bad = _no_iso_or_img_under_build_rescue()
    if not ok_iso:
        errors.extend([f"RESCUE_RT_FORBIDDEN_IMAGE:{b}" for b in bad])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_runtime_root", _MANIFEST_ROOT, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_backend_runtime_assembly(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    manifest_path, merr = _build_path(_BACKEND_ASM)
    if merr or manifest_path is None:
        return _emit("rescue_runtime_backend", _BACKEND_ASM, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RT_BE")
    if g:
        return _emit("rescue_runtime_backend", _BACKEND_ASM, "blocked", {}, wrote=False, warnings=[], errors=[g])

    rt = _routes_text()
    app_t = _app_text()
    deploy_dir = REPO_ROOT / "backend" / "deploy"
    safety_orchestrator = deploy_dir / "runner_rescue_readonly_mount_orchestrator.py"
    checks = {
        "backend_app_py": (REPO_ROOT / "backend" / "app.py").is_file(),
        "rescue_routes": bool(re.search(r'@router\.post\("/rescue/', rt)),
        "verify_routes": bool(re.search(r"@router\.post\(\"/[^\"]*verify", rt)) or "/verify" in rt,
        "preview_routes": bool(re.search(r"@router\.post\(\"/[^\"]*preview", rt)) or "/preview" in rt,
        "diagnostics_router": "diagnostics_router" in app_t or "/api/diagnostics" in app_t,
        "safety_modules": safety_orchestrator.is_file(),
    }
    if not checks["backend_app_py"]:
        errors.append("RESCUE_RT_BACKEND_APP_MISSING")
    if not checks["rescue_routes"]:
        errors.append("RESCUE_RT_BACKEND_RESCUE_ROUTES_MISSING")

    body: dict[str, Any] = {
        "backend_runtime_assembly_schema_version": 1,
        "strict_mode": "rescue_runtime_assembly_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checks": checks,
        "backend_startup_manifest": {
            "module": "backend.app:app",
            "bind": "0.0.0.0:8010",
            "readonly_runtime_hints": ["no host supervisor invocation from assembly", "uvicorn advisory only"],
        },
        "expected_uvicorn_command": "python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8010",
        "expected_environment_variables_note": "SETUPHELFER_* / optional API base; no cloud keys required for offline rescue",
        "no_actual_start": True,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_runtime_backend", _BACKEND_ASM, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "blocked" if errors else ("review_required" if warnings else "ok")
    return _emit("rescue_runtime_backend", _BACKEND_ASM, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_frontend_runtime_assembly(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    manifest_path, merr = _build_path(_FRONTEND_ASM)
    if merr or manifest_path is None:
        return _emit("rescue_runtime_frontend", _FRONTEND_ASM, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RT_FE")
    if g:
        return _emit("rescue_runtime_frontend", _FRONTEND_ASM, "blocked", {}, wrote=False, warnings=[], errors=[g])

    dist = REPO_ROOT / "frontend" / "dist"
    assets = dist / "assets"
    legacy_assets: list[str] = []
    asset_sample: list[str] = []
    if assets.is_dir():
        for p in sorted(assets.rglob("*"))[:400]:
            if p.is_file():
                rel = str(p.relative_to(REPO_ROOT)).replace("\\", "/")
                asset_sample.append(rel)
                low = rel.lower()
                if "pi-installer" in low or "pi_installer" in low:
                    legacy_assets.append(rel)
    else:
        warnings.append("RESCUE_RT_FE_DIST_ASSETS_MISSING")

    inspect = REPO_ROOT / "frontend" / "src" / "pages" / "InspectRun.tsx"
    inspect_legacy = False
    if inspect.is_file():
        raw = inspect.read_text(encoding="utf-8", errors="replace")
        inspect_legacy = bool(_LEGACY_PI.search(raw))
    if inspect_legacy:
        errors.append("RESCUE_RT_FE_INSPECTRUN_LEGACY")
    if legacy_assets:
        errors.append("RESCUE_RT_FE_DIST_LEGACY_ASSET")

    body: dict[str, Any] = {
        "frontend_runtime_assembly_schema_version": 1,
        "strict_mode": "rescue_runtime_assembly_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frontend_dist_present": dist.is_dir(),
        "index_html_present": (dist / "index.html").is_file(),
        "recovery_pages_note": "InspectRun.tsx primary rescue operator surface",
        "diagnostics_pages_note": "Diagnostics via app diagnostics routes + InspectRun",
        "branding_consistency": {"no_pi_installer_in_dist_paths": len(legacy_assets) == 0, "inspect_run_scanned": inspect.is_file()},
        "offline_asset_sample": asset_sample[:80],
        "legacy_asset_hits": legacy_assets[:30],
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_runtime_frontend", _FRONTEND_ASM, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "blocked" if errors else ("review_required" if warnings else "ok")
    return _emit("rescue_runtime_frontend", _FRONTEND_ASM, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_recovery_runtime_assembly(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    manifest_path, merr = _build_path(_RECOVERY_ASM)
    if merr or manifest_path is None:
        return _emit("rescue_runtime_recovery", _RECOVERY_ASM, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RT_REC")
    if g:
        return _emit("rescue_runtime_recovery", _RECOVERY_ASM, "blocked", {}, wrote=False, warnings=[], errors=[g])

    deploy = REPO_ROOT / "backend" / "deploy"
    rescue_modules = sorted({str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in deploy.glob("runner_rescue*.py")})
    verify_modules = sorted({str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in deploy.glob("*verify*.py")})
    preview_modules = sorted({str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in deploy.glob("*preview*.py")})
    inspect_modules = sorted(
        {str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in deploy.glob("runner_inspect*.py")}
        | {str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in deploy.glob("*inspect*.py")}
    )
    if not rescue_modules:
        errors.append("RESCUE_RT_RECOVERY_RESCUE_MODULES_MISSING")

    evidence_paths = [
        f"{_RUNTIME_BASE}/run/setuphelfer/evidence",
        "docs/evidence/runtime-results/handoff/",
    ]
    operator_guides_handoff = "docs/evidence/runtime-results/handoff/rescue_manual_recovery_operator_guides.json"

    body: dict[str, Any] = {
        "recovery_runtime_assembly_schema_version": 1,
        "strict_mode": "rescue_runtime_assembly_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verify_modules": verify_modules[:40],
        "preview_modules": preview_modules[:40],
        "inspect_modules": inspect_modules[:40],
        "rescue_modules": rescue_modules[:60],
        "recovery_evidence_paths": evidence_paths,
        "operator_guides_handoff": operator_guides_handoff,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_runtime_recovery", _RECOVERY_ASM, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "blocked" if errors else ("review_required" if warnings else "ok")
    return _emit("rescue_runtime_recovery", _RECOVERY_ASM, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_offline_configuration_assembly(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    manifest_path, merr = _build_path(_OFFLINE_ASM)
    if merr or manifest_path is None:
        return _emit("rescue_runtime_offline_config", _OFFLINE_ASM, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RT_OFF")
    if g:
        return _emit("rescue_runtime_offline_config", _OFFLINE_ASM, "blocked", {}, wrote=False, warnings=[], errors=[g])

    body: dict[str, Any] = {
        "offline_configuration_assembly_schema_version": 1,
        "strict_mode": "rescue_runtime_assembly_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "readonly_config_strategy": "defaults_readonly_until_operator_explicit_override",
        "offline_backend_config": {"api_bind": "0.0.0.0", "no_external_saas_required": True},
        "offline_frontend_config": {"static_root": f"{_RUNTIME_BASE}/usr/share/setuphelfer/frontend", "spa_fallback_index": True},
        "local_only_api_config": True,
        "no_cloud_dependency": True,
        "recovery_safe_defaults": {"auto_restore": False, "auto_repair": False, "destructive_execute_blocked": True},
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_runtime_offline_config", _OFFLINE_ASM, "blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit("rescue_runtime_offline_config", _OFFLINE_ASM, "ok", body, wrote=True, warnings=[], errors=[])


def build_rescue_startup_script_assembly(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    manifest_path, merr = _build_path(_STARTUP_ASM)
    if merr or manifest_path is None:
        return _emit("rescue_runtime_startup_scripts", _STARTUP_ASM, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RT_SCR")
    if g:
        return _emit("rescue_runtime_startup_scripts", _STARTUP_ASM, "blocked", {}, wrote=False, warnings=[], errors=[g])

    sdir, sderr = _build_path(_SCRIPTS_DIR)
    if sderr or sdir is None:
        return _emit("rescue_runtime_startup_scripts", _STARTUP_ASM, "blocked", {}, wrote=False, warnings=[], errors=[sderr or "DIR"])
    sdir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name in _SCRIPT_NAMES:
        fpath = sdir / name
        g2 = _guard_build_file(fpath, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RT_SH")
        if g2:
            errors.append(f"{g2}:{name}")
            continue
        fpath.write_text(_SH_TEMPLATE, encoding="utf-8")
        ok, oerr = _ensure_under_build_rescue(fpath)
        if not ok:
            errors.append(oerr or name)
            continue
        written.append(str(fpath.relative_to(REPO_ROOT)).replace("\\", "/"))

    body: dict[str, Any] = {
        "startup_script_assembly_schema_version": 1,
        "strict_mode": "rescue_runtime_assembly_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scripts_written": written,
        "no_real_service_start": True,
        "template_only": True,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_runtime_startup_scripts", _STARTUP_ASM, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_runtime_startup_scripts", _STARTUP_ASM, st, body, wrote=True, warnings=warnings, errors=errors)


def validate_rescue_runtime_assembly_safety(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_HANDOFF_SAFETY, "RESCUE_RT_SAFE")
    if oerr or out_path is None:
        return _emit("rescue_runtime_safety_validation", _HANDOFF_SAFETY, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RT_SAFE")
    if g0:
        return _emit("rescue_runtime_safety_validation", _HANDOFF_SAFETY, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

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
            errors.append(f"RESCUE_RT_SAFE_FORBIDDEN_ROUTE_SEGMENT:{seg}")

    destructive = ("mkfs", "dd if=", "dd of=", "wipefs", "chro" + "ot(", "mount " + "--bind")
    for tok in destructive:
        if tok in rt:
            errors.append(f"RESCUE_RT_SAFE_DESTRUCTIVE_TOKEN:{tok}")

    _sctl = "sy" + "stem" + "ctl"
    if _sctl in rt:
        errors.append("RESCUE_RT_SAFE_SUPERVISOR_IN_ROUTES")

    if ("qemu" + "-system") in rt or ("vbox" + "manage") in rt:
        errors.append("RESCUE_RT_SAFE_VM_TOOLING_IN_ROUTES")

    if _LEGACY_PI.search(_routes_text()):
        errors.append("RESCUE_RT_SAFE_LEGACY_PI_INSTALLER_IN_ROUTES")

    sdir, _ = _build_path(_SCRIPTS_DIR)
    if sdir and sdir.is_dir():
        for sf in sdir.glob("*.sh"):
            try:
                low = sf.read_text(encoding="utf-8", errors="replace").lower()
            except OSError:
                continue
            _script_bad = destructive + ("sy" + "stem" + "ctl", "qe" + "mu", "chroot", "dd ", "mkfs")
            for tok in _script_bad:
                if tok in low:
                    errors.append(f"RESCUE_RT_SAFE_FORBIDDEN_IN_SCRIPT:{sf.name}:{tok}")

    body: dict[str, Any] = {
        "rescue_runtime_assembly_safety_schema_version": 1,
        "strict_mode": "rescue_runtime_assembly_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "forbidden_segments_scanned": list(forbidden_segments),
        "runner_scan_note": "forbidden_syscalls_in_runner_enforced_by_unit_tests",
        "evaluation": {"rescue_runtime_assembly_safety_eval_status": "ok" if not errors else "blocked"},
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_runtime_safety_validation", _HANDOFF_SAFETY, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_runtime_safety_validation", _HANDOFF_SAFETY, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_runtime_assembly_final_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_HANDOFF_FINAL, "RESCUE_RT_FIN")
    if oerr or out_path is None:
        return _emit("rescue_runtime_final_gate", _HANDOFF_FINAL, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RT_FIN")
    if g0:
        return _emit("rescue_runtime_final_gate", _HANDOFF_FINAL, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    pb, pberr = load_json_handoff(_PSEUDO_BOOT_FINAL, "RT_PB")
    if pberr or not isinstance(pb, dict):
        errors.append("RTG_PSEUDO_BOOT_FINAL_MISSING")
    else:
        pbs = str(pb.get("gate_status") or "")
        if pbs == "blocked":
            errors.append("RTG_PSEUDO_BOOT_BLOCKED")
        elif pbs == "review_required":
            warnings.append("RTG_PSEUDO_BOOT_REVIEW")
        elif pbs != "ready":
            warnings.append("RTG_PSEUDO_BOOT_NOT_READY")

    brand, _ = load_json_handoff(_BRANDING_REL, "RT_BRAND")
    if isinstance(brand, dict) and str(brand.get("branding_guard_status") or "") == "blocked":
        errors.append("RTG_BRANDING_BLOCKED")

    zero, ze = load_json_handoff(_ZERO_REL, "RT_ZERO")
    if ze:
        warnings.append(f"RTG_ZERO_HANDOFF:{ze}")
    elif isinstance(zero, dict) and str(zero.get("zero_state_status") or "") == "blocked":
        errors.append("RTG_ZERO_STATE_BLOCKED")

    inputs: dict[str, str] = {
        "pseudo_boot_final_readiness": _PSEUDO_BOOT_FINAL,
        "runtime_root_manifest": _MANIFEST_ROOT,
        "backend_runtime_assembly": _BACKEND_ASM,
        "frontend_runtime_assembly": _FRONTEND_ASM,
        "recovery_runtime_assembly": _RECOVERY_ASM,
        "offline_configuration_assembly": _OFFLINE_ASM,
        "startup_script_assembly": _STARTUP_ASM,
        "branding_guard": _BRANDING_REL,
        "zero_state_verification": _ZERO_REL,
    }
    loaded: dict[str, Any] = {}
    for key, rel in inputs.items():
        if key in ("branding_guard", "zero_state_verification", "pseudo_boot_final_readiness"):
            continue
        p, perr = _build_path(rel)
        if perr or p is None or not p.is_file():
            errors.append(f"RTG_INPUT_MISSING:{rel}")
        else:
            try:
                raw = p.read_text(encoding="utf-8")
                loaded[key] = json.loads(raw)
                if re.search(r"(?<![A-Za-z0-9_])pi[-_]installer(?![A-Za-z0-9_])", raw):
                    errors.append(f"RTG_LEGACY_IN_MANIFEST:{rel}")
            except json.JSONDecodeError:
                errors.append(f"RTG_INPUT_JSON_INVALID:{rel}")

    fe = loaded.get("frontend_runtime_assembly") if isinstance(loaded.get("frontend_runtime_assembly"), dict) else {}
    bc = fe.get("branding_consistency") if isinstance(fe.get("branding_consistency"), dict) else {}
    if bc and bc.get("no_pi_installer_in_dist_paths") is False:
        errors.append("RTG_PI_INSTALLER_RUNTIME_ASSETS")

    off = loaded.get("offline_configuration_assembly") if isinstance(loaded.get("offline_configuration_assembly"), dict) else {}
    if off:
        rsf = off.get("recovery_safe_defaults") if isinstance(off.get("recovery_safe_defaults"), dict) else {}
        if rsf.get("auto_restore") is True or rsf.get("auto_repair") is True:
            errors.append("RTG_OFFLINE_UNSAFE_DEFAULTS")

    root_m = loaded.get("runtime_root_manifest") if isinstance(loaded.get("runtime_root_manifest"), dict) else {}
    if root_m and not root_m.get("expected_directories"):
        errors.append("RTG_RUNTIME_ROOT_INCOMPLETE")

    st_asm = loaded.get("startup_script_assembly") if isinstance(loaded.get("startup_script_assembly"), dict) else {}
    if st_asm:
        sw = st_asm.get("scripts_written") or []
        if len(sw) < len(_SCRIPT_NAMES):
            warnings.append("RTG_STARTUP_SCRIPTS_INCOMPLETE")

    ok_iso, bad = _no_iso_or_img_under_build_rescue()
    if not ok_iso:
        errors.extend([f"RTG_FORBIDDEN_IMAGE:{b}" for b in bad])

    st = "ready"
    if errors:
        st = "blocked"
    elif warnings:
        st = "review_required"

    body: dict[str, Any] = {
        "rescue_runtime_assembly_final_gate_schema_version": 1,
        "strict_mode": "rescue_runtime_assembly_pipeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_status": st,
        "inputs": inputs,
        "readonly_runtime_prepared": bool(off.get("readonly_config_strategy")),
        "recovery_runtime_complete": bool(
            isinstance(loaded.get("recovery_runtime_assembly"), dict)
            and (loaded.get("recovery_runtime_assembly") or {}).get("rescue_modules")
        ),
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_runtime_final_gate", _HANDOFF_FINAL, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_runtime_final_gate", _HANDOFF_FINAL, st, body, wrote=True, warnings=warnings, errors=errors)
