from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deploy.runner_rescue_io import (
    BUILD_RESCUE_ROOT,
    REPO_ROOT,
    guard_handoff_overwrite,
    load_json_handoff,
    resolve_handoff_path,
    resolve_under_build_rescue,
    write_json_handoff,
)

_MAX_MANIFEST = 900_000
_MAX_GATE = 512 * 1024

_ROOTFS_REL = "build/rescue/rootfs"
_MANIFEST_ROOTFS = "build/rescue/rootfs_manifest.json"
_MANIFEST_FRONTEND = "build/rescue/frontend_manifest.json"
_MANIFEST_BACKEND = "build/rescue/backend_manifest.json"
_MANIFEST_BOOT = "build/rescue/boot_artifact_manifest.json"
_OVERLAY_JSON = "build/rescue/overlay_persistence_strategy.json"
_GATE_HANDOFF = "docs/evidence/runtime-results/handoff/rescue_artifact_readiness_gate.json"
_ISO_FINAL_GATE = "docs/evidence/runtime-results/handoff/rescue_iso_final_readiness_gate.json"
_BRANDING_REL = "docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json"

_ROOTFS_DIRS = (
    "opt/setuphelfer",
    "etc/setuphelfer",
    "var/log/setuphelfer",
    "run/setuphelfer",
    "run/setuphelfer/evidence",
    "run/setuphelfer/recovery",
    "usr/share/setuphelfer/frontend",
)

_PLACEHOLDER_NAME = ".setuphelfer_rescue_artifact_placeholder"


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
    return resolve_under_build_rescue(raw, "RESCUE_ART")


def _ensure_under_build_rescue(p: Path) -> tuple[bool, str | None]:
    try:
        p.resolve(strict=False).relative_to(BUILD_RESCUE_ROOT.resolve(strict=False))
    except (OSError, ValueError):
        return False, "RESCUE_ART_OUTSIDE_BUILD_RESCUE"
    return True, None


def _no_iso_or_img_under_build_rescue() -> tuple[bool, list[str]]:
    bad: list[str] = []
    root = BUILD_RESCUE_ROOT
    if not root.is_dir():
        return True, []
    for fp in root.rglob("*"):
        try:
            rel = fp.relative_to(root)
            if rel.parts and rel.parts[0] == "output":
                continue
        except ValueError:
            continue
        if fp.is_symlink():
            try:
                fp.resolve().relative_to(BUILD_RESCUE_ROOT.resolve(strict=False))
            except (OSError, ValueError):
                bad.append(f"SYMLINK_OUTSIDE:{fp.relative_to(REPO_ROOT)}")
                continue
        if fp.is_file():
            low = fp.name.lower()
            if low.endswith(".iso") or low.endswith(".img"):
                bad.append(str(fp.relative_to(REPO_ROOT)).replace("\\", "/"))
    return len(bad) == 0, bad


def _guard_build_file(path: Path, *, explicit_overwrite: bool, prefix: str) -> str | None:
    if path.exists() and path.is_file() and not explicit_overwrite:
        return f"{prefix}_EXISTS_NO_OVERWRITE"
    return None


def build_rescue_rootfs_artifact(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    root_base, err = _build_path(_ROOTFS_REL)
    if err or root_base is None:
        return _emit("rescue_artifact_rootfs", _MANIFEST_ROOTFS, "blocked", {}, wrote=False, warnings=[], errors=[err or "RESCUE_ART_ROOTFS_INVALID"])

    created: list[str] = []
    for sub in _ROOTFS_DIRS:
        d = root_base / Path(sub)
        d.mkdir(parents=True, exist_ok=True)
        ok, oerr = _ensure_under_build_rescue(d)
        if not ok:
            errors.append(oerr or "PATH_CHECK")
            continue
        ph = d / _PLACEHOLDER_NAME
        if not ph.exists():
            ph.write_text("# setuphelfer rescue artifact placeholder (no real system files)\n", encoding="utf-8")
        created.append(f"{_ROOTFS_REL}/{sub}/{_PLACEHOLDER_NAME}".replace("\\", "/"))

    manifest_path, merr = _build_path(_MANIFEST_ROOTFS)
    if merr or manifest_path is None:
        return _emit("rescue_artifact_rootfs", _MANIFEST_ROOTFS, "blocked", {}, wrote=False, warnings=warnings, errors=[merr or "RESCUE_ART_MANIFEST_PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ART_ROOTFS")
    if g:
        return _emit("rescue_artifact_rootfs", _MANIFEST_ROOTFS, "blocked", {}, wrote=False, warnings=[], errors=[g])

    body: dict[str, Any] = {
        "rescue_rootfs_manifest_schema_version": 1,
        "strict_mode": "rescue_iso_artifact_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rootfs_base": _ROOTFS_REL,
        "expected_paths": [f"{_ROOTFS_REL}/{s}".replace("\\", "/") for s in _ROOTFS_DIRS],
        "placeholders_written": created,
        "readonly_overlay_definition": {"lower": "squashfs_documented", "upper": "tmpfs", "mode": "ro_until_explicit_session"},
        "recovery_evidence_dirs": [f"{_ROOTFS_REL}/run/setuphelfer/evidence"],
        "tmp_runtime_dirs": [f"{_ROOTFS_REL}/run/setuphelfer"],
        "no_system_file_copy": True,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_artifact_rootfs", _MANIFEST_ROOTFS, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    ok_iso, bad = _no_iso_or_img_under_build_rescue()
    if not ok_iso:
        errors.extend([f"RESCUE_ART_FORBIDDEN_IMAGE:{b}" for b in bad])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_artifact_rootfs", _MANIFEST_ROOTFS, st, body, wrote=True, warnings=warnings, errors=errors)


def _write_json_build(path: Path, obj: dict[str, Any]) -> str | None:
    ok, oerr = _ensure_under_build_rescue(path)
    if not ok:
        return oerr or "OUTSIDE"
    text = json.dumps(obj, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_MANIFEST:
        return "RESCUE_ART_MANIFEST_TOO_LARGE"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return None


def build_offline_frontend_artifacts(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    dist = REPO_ROOT / "frontend" / "dist"
    index_html = dist / "index.html"
    assets_dir = dist / "assets"
    asset_files: list[str] = []
    legacy_hits: list[str] = []

    if index_html.is_file():
        asset_files.append(str(index_html.relative_to(REPO_ROOT)).replace("\\", "/"))
    else:
        warnings.append("RESCUE_ART_FRONTEND_DIST_INDEX_MISSING")

    if assets_dir.is_dir():
        for p in sorted(assets_dir.rglob("*"))[:500]:
            if p.is_file():
                rel = str(p.relative_to(REPO_ROOT)).replace("\\", "/")
                asset_files.append(rel)
                low = rel.lower()
                if "pi-installer" in low or "pi_installer" in low:
                    legacy_hits.append(rel)
    else:
        warnings.append("RESCUE_ART_FRONTEND_DIST_ASSETS_MISSING")

    if legacy_hits:
        errors.append("RESCUE_ART_FRONTEND_LEGACY_PI_INSTALLER_ASSET")

    manifest_path, merr = _build_path(_MANIFEST_FRONTEND)
    if merr or manifest_path is None:
        return _emit("rescue_artifact_frontend", _MANIFEST_FRONTEND, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ART_FE")
    if g:
        return _emit("rescue_artifact_frontend", _MANIFEST_FRONTEND, "blocked", {}, wrote=False, warnings=[], errors=[g])

    body: dict[str, Any] = {
        "frontend_manifest_schema_version": 1,
        "strict_mode": "rescue_iso_artifact_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frontend_dist_reference": "frontend/dist",
        "index_html_present": index_html.is_file(),
        "assets_dir_present": assets_dir.is_dir(),
        "offline_ready_asset_list": asset_files[:400],
        "no_pi_installer_assets": len(legacy_hits) == 0,
        "no_frontend_build_executed": True,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_artifact_frontend", _MANIFEST_FRONTEND, "blocked", body, wrote=False, warnings=warnings, errors=[werr])

    st = "ok" if not errors else "blocked"
    if warnings and st == "ok":
        st = "review_required"
    return _emit("rescue_artifact_frontend", _MANIFEST_FRONTEND, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_backend_artifacts(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    routes_path = REPO_ROOT / "backend" / "deploy" / "routes.py"
    rt = routes_path.read_text(encoding="utf-8") if routes_path.is_file() else ""
    app_py = REPO_ROOT / "backend" / "app.py"

    checks = {
        "backend_app_py": app_py.is_file(),
        "recovery_routes": bool(re.search(r'@router\.post\("/rescue/', rt)),
        "verify_routes": bool(re.search(r"@router\.post\(\"/[^\"]*verify", rt)) or "/verify" in rt,
        "preview_routes": bool(re.search(r"@router\.post\(\"/[^\"]*preview", rt)) or "/preview" in rt,
        "deploy_rescue_routes": _count_rescue_posts(rt) >= 15,
        "diagnostics_modules": (REPO_ROOT / "backend" / "deploy").is_dir(),
        "safety_modules": (REPO_ROOT / "backend" / "deploy" / "runner_rescue_readonly_mount_orchestrator.py").is_file(),
    }
    if not checks["backend_app_py"]:
        errors.append("RESCUE_ART_BACKEND_APP_MISSING")
    if not checks["recovery_routes"]:
        errors.append("RESCUE_ART_BACKEND_RECOVERY_ROUTES_MISSING")

    manifest_path, merr = _build_path(_MANIFEST_BACKEND)
    if merr or manifest_path is None:
        return _emit("rescue_artifact_backend", _MANIFEST_BACKEND, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ART_BE")
    if g:
        return _emit("rescue_artifact_backend", _MANIFEST_BACKEND, "blocked", {}, wrote=False, warnings=[], errors=[g])

    body: dict[str, Any] = {
        "backend_manifest_schema_version": 1,
        "strict_mode": "rescue_iso_artifact_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checks": checks,
        "expected_startup_command": "python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8010",
        "offline_runtime_dependencies_note": "see Debian live-build plan / rescue packages; no install in this phase",
        "routes_file": str(routes_path.relative_to(REPO_ROOT)).replace("\\", "/"),
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_artifact_backend", _MANIFEST_BACKEND, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_artifact_backend", _MANIFEST_BACKEND, st, body, wrote=True, warnings=warnings, errors=errors)


def _count_rescue_posts(txt: str) -> int:
    return len(re.findall(r'@router\.post\("/rescue/', txt))


def build_rescue_boot_artifact_structure(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    layout: list[tuple[str, str]] = [
        ("build/rescue/boot/grub", "grub.cfg.planned.txt"),
        ("build/rescue/EFI/BOOT", "BOOTX64.EFI.placeholder"),
        ("build/rescue/live", "filesystem.squashfs.planned"),
        ("build/rescue/live", "initrd.img.placeholder"),
        ("build/rescue/live", "vmlinuz.placeholder"),
    ]

    written: list[str] = []
    for dir_rel, fname in layout:
        dpath, derr = _build_path(dir_rel)
        if derr or dpath is None:
            errors.append(derr or "DIR")
            continue
        dpath.mkdir(parents=True, exist_ok=True)
        ok, oerr = _ensure_under_build_rescue(dpath)
        if not ok:
            errors.append(oerr or "PATH")
            continue
        fpath = dpath / fname
        if not fpath.exists():
            fpath.write_text("# planned only — no bootloader/binary materialization\n", encoding="utf-8")
        wok, werr = _ensure_under_build_rescue(fpath)
        if not wok:
            errors.append(werr or "FILEPATH")
            continue
        written.append(str(fpath.relative_to(REPO_ROOT)).replace("\\", "/"))

    manifest_path, merr = _build_path(_MANIFEST_BOOT)
    if merr or manifest_path is None:
        return _emit("rescue_artifact_boot_structure", _MANIFEST_BOOT, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ART_BOOT")
    if g:
        return _emit("rescue_artifact_boot_structure", _MANIFEST_BOOT, "blocked", {}, wrote=False, warnings=[], errors=[g])

    body: dict[str, Any] = {
        "boot_artifact_manifest_schema_version": 1,
        "strict_mode": "rescue_iso_artifact_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "planned": {
            "grub_config": "planned",
            "efi": "planned",
            "squashfs": "planned",
            "initrd": "planned",
            "kernel_placeholder": "planned",
        },
        "paths_created": written,
        "no_grub_mkrescue": True,
        "no_xorriso": True,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_artifact_boot_structure", _MANIFEST_BOOT, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    ok_iso, bad = _no_iso_or_img_under_build_rescue()
    if not ok_iso:
        errors.extend([f"RESCUE_ART_FORBIDDEN_IMAGE:{b}" for b in bad])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_artifact_boot_structure", _MANIFEST_BOOT, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_overlay_persistence_strategy(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    manifest_path, merr = _build_path(_OVERLAY_JSON)
    if merr or manifest_path is None:
        return _emit("rescue_artifact_overlay_strategy", _OVERLAY_JSON, "blocked", {}, wrote=False, warnings=[], errors=[merr or "PATH"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ART_OVL")
    if g:
        return _emit("rescue_artifact_overlay_strategy", _OVERLAY_JSON, "blocked", {}, wrote=False, warnings=[], errors=[g])

    body: dict[str, Any] = {
        "overlay_persistence_strategy_schema_version": 1,
        "strict_mode": "rescue_iso_artifact_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "readonly_lowerdir": "squashfs_root_documented",
        "tmpfs_upperdir": "/run/setuphelfer/overlay_upper_tmpfs",
        "optional_later_persistence": "explicit_operator_usb_or_secondary_disk_only",
        "recovery_evidence_persistence": "export_to_allowlisted_external_target_only",
        "never_auto_target_disk_persistence": True,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_artifact_overlay_strategy", _OVERLAY_JSON, "blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit("rescue_artifact_overlay_strategy", _OVERLAY_JSON, "ok", body, wrote=True, warnings=[], errors=[])


def build_rescue_artifact_readiness_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_GATE_HANDOFF, "RESCUE_ART_GATE")
    if oerr or out_path is None:
        return _emit("rescue_artifact_readiness_gate", _GATE_HANDOFF, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ART_GATE")
    if g0:
        return _emit("rescue_artifact_readiness_gate", _GATE_HANDOFF, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    iso_final, e1 = load_json_handoff(_ISO_FINAL_GATE, "ART_IFG")
    brand, _ = load_json_handoff(_BRANDING_REL, "ART_BRAND")

    manifests = (
        _MANIFEST_ROOTFS,
        _MANIFEST_FRONTEND,
        _MANIFEST_BACKEND,
        _MANIFEST_BOOT,
        _OVERLAY_JSON,
    )
    for rel in manifests:
        p, perr = _build_path(rel)
        if perr or p is None or not p.is_file():
            errors.append(f"ART_GATE_MANIFEST_MISSING:{rel}")
        else:
            try:
                raw = p.read_text(encoding="utf-8")
                # Avoid false positives on keys like no_pi_installer_assets (word chars before pi).
                if re.search(r"(?<![A-Za-z0-9_])pi[-_]installer(?![A-Za-z0-9_])", raw):
                    errors.append(f"ART_GATE_LEGACY_IN_MANIFEST:{rel}")
            except OSError:
                errors.append(f"ART_GATE_MANIFEST_READ_FAIL:{rel}")

    if isinstance(brand, dict) and str(brand.get("branding_guard_status") or "") == "blocked":
        errors.append("ART_GATE_BRANDING_BLOCKED")

    if e1:
        warnings.append(f"ART_GATE_ISO_FINAL_HANDOFF:{e1}")
    elif isinstance(iso_final, dict):
        gs = str(iso_final.get("gate_status") or "")
        if gs == "blocked":
            errors.append("ART_GATE_ISO_FINAL_BLOCKED")
        elif gs == "review_required":
            warnings.append("ART_GATE_ISO_FINAL_REVIEW")

    ok_iso, bad = _no_iso_or_img_under_build_rescue()
    if not ok_iso:
        errors.extend([f"ART_GATE_FORBIDDEN_IMAGE:{b}" for b in bad])

    st = "ready"
    if errors:
        st = "blocked"
    elif warnings:
        st = "review_required"

    body: dict[str, Any] = {
        "rescue_artifact_readiness_gate_schema_version": 1,
        "strict_mode": "rescue_iso_artifact_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_status": st,
        "inputs": {
            "rescue_iso_final_readiness_gate": _ISO_FINAL_GATE,
            "rootfs_manifest": _MANIFEST_ROOTFS,
            "frontend_manifest": _MANIFEST_FRONTEND,
            "backend_manifest": _MANIFEST_BACKEND,
            "boot_artifact_manifest": _MANIFEST_BOOT,
            "overlay_persistence_strategy": _OVERLAY_JSON,
        },
        "build_directory_only": "build/rescue/",
        "no_writes_outside_build_rescue": True,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_GATE)
    if werr:
        return _emit("rescue_artifact_readiness_gate", _GATE_HANDOFF, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_artifact_readiness_gate", _GATE_HANDOFF, st, body, wrote=True, warnings=warnings, errors=errors)
