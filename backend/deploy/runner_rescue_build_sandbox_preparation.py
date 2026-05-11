from __future__ import annotations

import hashlib
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
_MAX_HANDOFF = 512 * 1024
_MAX_PLAN_ENTRIES = 220
_MAX_HASH_BYTES = 256 * 1024

_SB_ROOT = "build/rescue/sandbox"
_MANIFEST = "build/rescue/sandbox_root_manifest.json"
_CFG_PLAN = "build/rescue/sandbox_config_copy_plan.json"
_RT_PLAN = "build/rescue/sandbox_runtime_copy_plan.json"
_OVL_PLAN = "build/rescue/overlay_workspace_plan.json"
_CLEAN_PLAN = "build/rescue/build_cleanup_plan.json"
_SAFE = "docs/evidence/runtime-results/handoff/rescue_build_sandbox_safety.json"
_FIN = "docs/evidence/runtime-results/handoff/rescue_build_sandbox_final_gate.json"

_DL = "build/rescue/debian-live"
_RT = "build/rescue/runtime"
_MANIFESTS_EXTRA = (
    "build/rescue/runtime_bundle_hash_manifest.json",
    "build/rescue/runtime_bundle_inventory.json",
    "build/rescue/runtime_bundle.seal.json",
)

_CC = "docs/evidence/runtime-results/handoff/rescue_runtime_bundle_consistency_check.json"
_DRY_FIN = "docs/evidence/runtime-results/handoff/rescue_dry_build_final_gate.json"
_DRY_SAFE = "docs/evidence/runtime-results/handoff/rescue_dry_build_safety_validation.json"
_BRAND = "docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json"
_ZERO = "docs/evidence/runtime-results/handoff/runtime_identifier_zero_state_verification.json"

_SB_SUBDIRS = (
    "sandbox/workspace",
    "sandbox/config-copy",
    "sandbox/runtime-copy",
    "sandbox/manifests",
    "sandbox/logs",
    "sandbox/tmp",
    "sandbox/overlay",
    "sandbox/rollback",
    "sandbox/readonly-markers",
)

_TEXT_SUFFIXES = (
    ".json",
    ".md",
    ".txt",
    ".cfg",
    ".template",
    ".list",
    ".chroot",
    ".yaml",
    ".yml",
)

_BLOCKED_NAME_PARTS = frozenset(
    {
        "node_modules",
        ".git",
    }
)

_BLOCKED_SUFFIXES = (".iso", ".img", ".qcow2", ".qcow", ".vdi", ".vmdk")

_LEGACY_PI = re.compile(r"(?<![A-Za-z0-9_])pi[-_]installer(?![A-Za-z0-9_])")


def _routes_text() -> str:
    p = REPO_ROOT / "backend" / "deploy" / "routes.py"
    return p.read_text(encoding="utf-8") if p.is_file() else ""


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
    return resolve_under_build_rescue(raw, "RESCUE_SB")


def _ensure_under_build_rescue(p: Path) -> tuple[bool, str | None]:
    try:
        p.resolve(strict=False).relative_to(BUILD_RESCUE_ROOT.resolve(strict=False))
    except (OSError, ValueError):
        return False, "RESCUE_SB_OUTSIDE_BUILD_RESCUE"
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
        return "RESCUE_SB_MANIFEST_TOO_LARGE"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return None


def _handoff_exists(rel: str) -> bool:
    p, err = resolve_handoff_path(rel, "RESCUE_SB")
    return bool(p and p.is_file() and not err)


def _artifact_exists(rel: str) -> bool:
    r = rel.replace("\\", "/").strip()
    if r.startswith("docs/evidence/"):
        return _handoff_exists(r)
    p, err = _build_path(r)
    return bool(p and p.is_file() and not err)


def _read_build_json(rel: str) -> tuple[dict[str, Any] | None, str | None]:
    p, err = _build_path(rel)
    if err or p is None or not p.is_file():
        return None, err or "RESCUE_SB_JSON_MISSING"
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "RESCUE_SB_JSON_INVALID"
    return (o if isinstance(o, dict) else None), None


def _path_blocked_for_runtime(rel_posix: str) -> bool | str:
    low = rel_posix.lower()
    parts = Path(rel_posix).parts
    for p in parts:
        if p in _BLOCKED_NAME_PARTS:
            return True
        if p.lower() == "node_modules":
            return True
    for suf in _BLOCKED_SUFFIXES:
        if low.endswith(suf):
            return suf
    return False


def _is_textish_file(fp: Path) -> bool:
    low = fp.name.lower()
    return any(low.endswith(s) for s in _TEXT_SUFFIXES)


def _sha256_file_short(fp: Path) -> str | None:
    try:
        sz = fp.stat().st_size
    except OSError:
        return None
    if sz > _MAX_HASH_BYTES:
        return None
    try:
        h = hashlib.sha256()
        h.update(fp.read_bytes())
        return h.hexdigest()
    except OSError:
        return None


def build_rescue_build_sandbox_root(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    mp, mperr = _build_path(_MANIFEST)
    if mperr or mp is None:
        return _emit("rescue_build_sandbox_root", _MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[mperr or "PATH"])
    g = _guard_build_file(mp, explicit_overwrite=explicit_overwrite, prefix="RESCUE_SB_RM")
    if g:
        return _emit("rescue_build_sandbox_root", _MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[g])

    base, berr = _build_path(_SB_ROOT)
    if berr or base is None:
        return _emit("rescue_build_sandbox_root", _MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[berr or "ROOT"])

    created: list[str] = []
    br = BUILD_RESCUE_ROOT.resolve(strict=False)
    for sub in _SB_SUBDIRS:
        d = br / Path(sub)
        d.mkdir(parents=True, exist_ok=True)
        ok, oerr = _ensure_under_build_rescue(d)
        if not ok:
            errors.append(oerr or sub)
            continue
        created.append(f"build/rescue/{sub}".replace("\\", "/"))

    allowed = [f"build/rescue/{s}".replace("\\", "/") for s in _SB_SUBDIRS]
    readonly_roots = [
        "build/rescue/runtime",
        "build/rescue/debian-live",
    ]
    st = "ok" if not errors else "blocked"
    body: dict[str, Any] = {
        "sandbox_root_manifest_schema_version": 1,
        "strict_mode": "rescue_build_sandbox_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sandbox_root": "build/rescue/sandbox",
        "allowed_write_roots": sorted(allowed),
        "cleanup_required": True,
        "directories_created": sorted(created),
        "execute_build_allowed": False,
        "readonly_roots": readonly_roots,
        "rescue_build_sandbox_root_status": st,
    }
    werr = _write_json_build(mp, body)
    if werr:
        return _emit("rescue_build_sandbox_root", _MANIFEST, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_sandbox_root", _MANIFEST, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_sandbox_config_copy_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    path, perr = _build_path(_CFG_PLAN)
    if perr or path is None:
        return _emit("rescue_build_sandbox_config_copy_plan", _CFG_PLAN, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])
    g = _guard_build_file(path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_SB_CP")
    if g:
        return _emit("rescue_build_sandbox_config_copy_plan", _CFG_PLAN, "blocked", {}, wrote=False, warnings=[], errors=[g])

    entries: list[dict[str, Any]] = []
    root_dl, e1 = _build_path(_DL)
    if root_dl and root_dl.is_dir():
        for fp in sorted(root_dl.rglob("*"))[: _MAX_PLAN_ENTRIES * 2]:
            if not fp.is_file() or not _is_textish_file(fp):
                continue
            try:
                rel = fp.relative_to(BUILD_RESCUE_ROOT.resolve(strict=False)).as_posix()
            except ValueError:
                continue
            tgt = f"build/rescue/sandbox/config-copy/{rel[len('build/rescue/debian-live/'):] if rel.startswith('build/rescue/debian-live/') else rel}"
            hx = _sha256_file_short(fp)
            entries.append(
                {
                    "copy_mode": "readonly_copy",
                    "expected_hash": hx,
                    "overwrite_allowed": False,
                    "source_path": rel,
                    "target_path": tgt,
                }
            )
            if len(entries) >= _MAX_PLAN_ENTRIES:
                warnings.append("RESCUE_SB_CP_TRUNCATED")
                break
    else:
        warnings.append("RESCUE_SB_CP_DEBIAN_LIVE_MISSING")

    for extra in _MANIFESTS_EXTRA:
        ep, _ = _build_path(extra)
        if ep and ep.is_file() and _is_textish_file(ep):
            rel = extra
            entries.append(
                {
                    "copy_mode": "readonly_copy",
                    "expected_hash": _sha256_file_short(ep),
                    "overwrite_allowed": False,
                    "source_path": rel,
                    "target_path": f"build/rescue/sandbox/config-copy/manifests/{Path(extra).name}",
                }
            )

    st = "review_required" if warnings else "ok"
    body: dict[str, Any] = {
        "sandbox_config_copy_plan_schema_version": 1,
        "strict_mode": "rescue_build_sandbox_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plan_entries": entries,
        "no_binary_bulk_copy": True,
        "rescue_build_sandbox_config_copy_plan_status": st,
        "text_and_manifest_only": True,
    }
    werr = _write_json_build(path, body)
    if werr:
        return _emit("rescue_build_sandbox_config_copy_plan", _CFG_PLAN, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_sandbox_config_copy_plan", _CFG_PLAN, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_sandbox_runtime_copy_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    path, perr = _build_path(_RT_PLAN)
    if perr or path is None:
        return _emit("rescue_build_sandbox_runtime_copy_plan", _RT_PLAN, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])
    g = _guard_build_file(path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_SB_RP")
    if g:
        return _emit("rescue_build_sandbox_runtime_copy_plan", _RT_PLAN, "blocked", {}, wrote=False, warnings=[], errors=[g])

    entries: list[dict[str, Any]] = []
    root_rt, e1 = _build_path(_RT)
    if root_rt and root_rt.is_dir():
        for fp in sorted(root_rt.rglob("*"))[: _MAX_PLAN_ENTRIES * 3]:
            if not fp.is_file():
                continue
            try:
                rel = fp.relative_to(BUILD_RESCUE_ROOT.resolve(strict=False)).as_posix()
            except ValueError:
                continue
            blk = _path_blocked_for_runtime(rel)
            if blk:
                errors.append(f"RESCUE_SB_RP_BLOCKED_PATH:{rel}")
                continue
            if not _is_textish_file(fp):
                continue
            rest = rel[len("build/rescue/runtime/") :] if rel.startswith("build/rescue/runtime/") else rel
            tgt = f"build/rescue/sandbox/runtime-copy/{rest}"
            entries.append(
                {
                    "copy_mode": "readonly_copy",
                    "expected_hash": _sha256_file_short(fp),
                    "overwrite_allowed": False,
                    "source_path": rel,
                    "target_path": tgt,
                }
            )
            if len(entries) >= _MAX_PLAN_ENTRIES:
                warnings.append("RESCUE_SB_RP_TRUNCATED")
                break
    else:
        warnings.append("RESCUE_SB_RT_MISSING")

    st = "blocked" if errors else ("review_required" if warnings else "ok")
    body: dict[str, Any] = {
        "sandbox_runtime_copy_plan_schema_version": 1,
        "strict_mode": "rescue_build_sandbox_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plan_entries": entries,
        "no_vm_artifacts": True,
        "rescue_build_sandbox_runtime_copy_plan_status": st,
    }
    werr = _write_json_build(path, body)
    if werr:
        return _emit("rescue_build_sandbox_runtime_copy_plan", _RT_PLAN, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_sandbox_runtime_copy_plan", _RT_PLAN, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_overlay_workspace_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    path, perr = _build_path(_OVL_PLAN)
    if perr or path is None:
        return _emit("rescue_build_sandbox_overlay_workspace_plan", _OVL_PLAN, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])
    g = _guard_build_file(path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_SB_OV")
    if g:
        return _emit("rescue_build_sandbox_overlay_workspace_plan", _OVL_PLAN, "blocked", {}, wrote=False, warnings=[], errors=[g])

    st = "ok"
    body: dict[str, Any] = {
        "overlay_workspace_plan_schema_version": 1,
        "strict_mode": "rescue_build_sandbox_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lowerdir": "build/rescue/runtime",
        "upperdir": "build/rescue/sandbox/overlay/upper",
        "workdir": "build/rescue/sandbox/overlay/work",
        "persistence_disabled": True,
        "readonly_runtime": True,
        "rescue_build_sandbox_overlay_workspace_plan_status": st,
        "rollback_strategy": "discard_upper_workdirs_no_mount",
        "no_mount_execution": True,
    }
    werr = _write_json_build(path, body)
    if werr:
        return _emit("rescue_build_sandbox_overlay_workspace_plan", _OVL_PLAN, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_sandbox_overlay_workspace_plan", _OVL_PLAN, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_build_cleanup_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    path, perr = _build_path(_CLEAN_PLAN)
    if perr or path is None:
        return _emit("rescue_build_cleanup_plan", _CLEAN_PLAN, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])
    g = _guard_build_file(path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_SB_CL")
    if g:
        return _emit("rescue_build_cleanup_plan", _CLEAN_PLAN, "blocked", {}, wrote=False, warnings=[], errors=[g])

    tmp_paths = [
        "build/rescue/sandbox/tmp",
        "build/rescue/sandbox/logs",
    ]
    rollback_paths = ["build/rescue/sandbox/rollback"]
    manifests = sorted([_MANIFEST, _CFG_PLAN, _RT_PLAN, _OVL_PLAN, _CLEAN_PLAN])
    cleanup_targets = sorted(
        [
            "build/rescue/sandbox/tmp",
            "build/rescue/sandbox/overlay/upper",
            "build/rescue/sandbox/overlay/work",
        ]
    )
    st = "ok"
    body: dict[str, Any] = {
        "build_cleanup_plan_schema_version": 1,
        "strict_mode": "rescue_build_sandbox_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cleanup_order": ["overlay_work_upper", "overlay_work_workdir", "sandbox_tmp", "sandbox_logs"],
        "cleanup_targets": cleanup_targets,
        "destructive_cleanup": False,
        "generated_manifests": manifests,
        "rescue_build_cleanup_plan_status": st,
        "rollback_paths": rollback_paths,
        "temporary_paths": tmp_paths,
        "no_rm_rf_in_runner": True,
    }
    werr = _write_json_build(path, body)
    if werr:
        return _emit("rescue_build_cleanup_plan", _CLEAN_PLAN, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_cleanup_plan", _CLEAN_PLAN, st, body, wrote=True, warnings=warnings, errors=errors)


def _rx(expr: str) -> re.Pattern[str]:
    return re.compile(expr)


_lb = "lb" + r"\s+build"
_grub = "grub-mk" + "rescue"
_xor = "xor" + "riso"
_debo = "deb" + "ootstrap"
_ch = "ch" + "ro" + "ot" + r"\s*\("
_mnt = "mount" + r"\s*\("
_loset = "lose" + "tup"
_mod = "mod" + "probe"
_dk = "dock" + "er"
_pod = "pod" + "man"

_SB_SAFETY: tuple[tuple[re.Pattern[str], str], ...] = (
    (_rx(r"(?i)" + _lb), "lb_build"),
    (_rx(r"(?i)\b" + _debo + r"\b"), "deboost"),
    (_rx(r"(?i)\bapt\s+install\b"), "apt_install"),
    (_rx(r"(?i)" + _ch), "chroot_invoke"),
    (_rx(r"(?i)\b" + _grub + r"\b"), "boot_mkrescue"),
    (_rx(r"(?i)\b" + _xor + r"\b"), "iso_xor"),
    (_rx(r"(?i)\bqe" + "mu"), "virt_qemu_family"),
    (_rx(r"(?i)\bvbox" + r"manage\b"), "virt_vboxm"),
    (_rx(r"(?i)\bdd\b"), "dd_cmd"),
    (_rx(r"(?i)\bmkfs(\.[a-z0-9]+)?\b"), "mkfs_pat"),
    (_rx(r"(?i)\bwipefs\b"), "wipefs_pat"),
    (_rx(r"(?i)" + _mnt), "mount_invoke"),
    (_rx(r"(?i)\b" + _loset + r"\b"), "loop_attach"),
    (_rx(r"(?i)\b" + _mod + r"\b"), "kmod_load"),
    (_rx(r"(?i)\b" + _dk + r"\b"), "ctr_dk"),
    (_rx(r"(?i)\b" + _pod + r"\b"), "ctr_pm"),
    (_rx(r"(?i)\bsquash" + "fs\b"), "sqfs_tool"),
)


def validate_rescue_build_sandbox_safety(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_SAFE, "RESCUE_SB_SAFE")
    if oerr or out_path is None:
        return _emit("rescue_build_sandbox_safety_validation", _SAFE, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_SB_SAFE")
    if g0:
        return _emit("rescue_build_sandbox_safety_validation", _SAFE, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    rt = _routes_text().lower()
    route_scan = tuple(x for x in _SB_SAFETY if x[1] not in ("dd_cmd",))
    for rx, lid in route_scan:
        if rx.search(rt):
            errors.append(f"RESCUE_SB_SAFE_ROUTES:{lid}")

    for rel in (_MANIFEST, _CFG_PLAN, _RT_PLAN, _OVL_PLAN, _CLEAN_PLAN):
        p, _ = _build_path(rel)
        if p and p.is_file():
            try:
                raw = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if _LEGACY_PI.search(raw):
                errors.append(f"RESCUE_SB_SAFE_LEGACY:{rel}")
            for rx, lid in _SB_SAFETY:
                if rx.search(raw):
                    errors.append(f"RESCUE_SB_SAFE_ARTIFACT:{rel}:{lid}")

    body: dict[str, Any] = {
        "rescue_build_sandbox_safety_schema_version": 1,
        "strict_mode": "rescue_build_sandbox_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evaluation": {"rescue_build_sandbox_safety_eval_status": "ok" if not errors else "blocked"},
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_build_sandbox_safety_validation", _SAFE, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_build_sandbox_safety_validation", _SAFE, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_build_sandbox_final_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_FIN, "RESCUE_SB_FIN")
    if oerr or out_path is None:
        return _emit("rescue_build_sandbox_final_gate", _FIN, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_SB_FIN")
    if g0:
        return _emit("rescue_build_sandbox_final_gate", _FIN, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    inputs: dict[str, str] = {
        "sandbox_root_manifest": _MANIFEST,
        "sandbox_config_copy_plan": _CFG_PLAN,
        "sandbox_runtime_copy_plan": _RT_PLAN,
        "overlay_workspace_plan": _OVL_PLAN,
        "build_cleanup_plan": _CLEAN_PLAN,
        "rescue_dry_build_final_gate": _DRY_FIN,
        "rescue_dry_build_safety_validation": _DRY_SAFE,
        "runtime_bundle_consistency": _CC,
        "branding_guard": _BRAND,
        "zero_state_verification": _ZERO,
    }

    for key, rel in inputs.items():
        if key in ("runtime_bundle_consistency", "branding_guard", "zero_state_verification"):
            continue
        if not _artifact_exists(rel):
            errors.append(f"RESCUE_SB_FIN_INPUT_MISSING:{rel}")

    cc, ce = load_json_handoff(_CC, "RESCUE_SB_CC")
    if ce or not isinstance(cc, dict):
        errors.append("RESCUE_SB_FIN_CC_MISSING")
    elif str(cc.get("consistency_status") or "") == "blocked":
        errors.append("RESCUE_SB_FIN_CC_BLOCKED")

    df, de = load_json_handoff(_DRY_FIN, "RESCUE_SB_DF")
    if de or not isinstance(df, dict):
        errors.append("RESCUE_SB_FIN_DRY_FIN_MISSING")
    else:
        gs = str(df.get("gate_status") or "")
        if gs == "blocked":
            errors.append("RESCUE_SB_FIN_DRY_FIN_BLOCKED")
        elif gs not in ("ready", "review_required"):
            warnings.append("RESCUE_SB_FIN_DRY_FIN_NOT_GREEN")

    ds, dse = load_json_handoff(_DRY_SAFE, "RESCUE_SB_DS")
    if dse or not isinstance(ds, dict):
        warnings.append("RESCUE_SB_FIN_DRY_SAFE_MISSING")
    else:
        ev = ds.get("evaluation") if isinstance(ds.get("evaluation"), dict) else {}
        if str(ev.get("rescue_dry_build_safety_eval_status") or "") == "blocked":
            errors.append("RESCUE_SB_FIN_DRY_SAFE_BLOCKED")

    brand, _ = load_json_handoff(_BRAND, "RESCUE_SB_BR")
    if isinstance(brand, dict) and str(brand.get("branding_guard_status") or "") == "blocked":
        errors.append("RESCUE_SB_FIN_BRAND_BLOCKED")

    zero, ze = load_json_handoff(_ZERO, "RESCUE_SB_ZE")
    if ze:
        warnings.append(f"RESCUE_SB_FIN_ZERO:{ze}")
    elif isinstance(zero, dict) and str(zero.get("zero_state_status") or "") == "blocked":
        errors.append("RESCUE_SB_FIN_ZERO_BLOCKED")

    sb_safe, sse = load_json_handoff(_SAFE, "RESCUE_SB_S2")
    if sse or not isinstance(sb_safe, dict):
        warnings.append("RESCUE_SB_FIN_SB_SAFE_MISSING")
    else:
        ev2 = sb_safe.get("evaluation") if isinstance(sb_safe.get("evaluation"), dict) else {}
        if str(ev2.get("rescue_build_sandbox_safety_eval_status") or "") == "blocked":
            errors.append("RESCUE_SB_FIN_SB_SAFE_BLOCKED")

    rtp, rte = _read_build_json(_RT_PLAN)
    if rte or not isinstance(rtp, dict):
        warnings.append("RESCUE_SB_FIN_RT_PLAN_MISSING")
    elif str(rtp.get("rescue_build_sandbox_runtime_copy_plan_status") or "") == "blocked":
        errors.append("RESCUE_SB_FIN_RUNTIME_PLAN_BLOCKED")

    for plan_rel, pkey, ecode in (
        (_CFG_PLAN, "rescue_build_sandbox_config_copy_plan_status", "RESCUE_SB_FIN_CFG_PLAN_BLOCKED"),
        (_OVL_PLAN, "rescue_build_sandbox_overlay_workspace_plan_status", "RESCUE_SB_FIN_OVERLAY_PLAN_BLOCKED"),
        (_CLEAN_PLAN, "rescue_build_cleanup_plan_status", "RESCUE_SB_FIN_CLEANUP_PLAN_BLOCKED"),
    ):
        po, poe = _read_build_json(plan_rel)
        if not poe and isinstance(po, dict) and str(po.get(pkey) or "") == "blocked":
            errors.append(ecode)

    for rel in (_MANIFEST, _CFG_PLAN, _RT_PLAN, _OVL_PLAN, _CLEAN_PLAN):
        p, _ = _build_path(rel)
        if p and p.is_file():
            try:
                raw = p.read_text(encoding="utf-8")
                if _LEGACY_PI.search(raw):
                    errors.append(f"RESCUE_SB_FIN_LEGACY:{rel}")
            except OSError:
                errors.append(f"RESCUE_SB_FIN_READ:{rel}")

    gst = "ready"
    if errors:
        gst = "blocked"
    elif warnings:
        gst = "review_required"

    body: dict[str, Any] = {
        "rescue_build_sandbox_final_gate_schema_version": 1,
        "strict_mode": "rescue_build_sandbox_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_status": gst,
        "inputs": inputs,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_build_sandbox_final_gate", _FIN, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_sandbox_final_gate", _FIN, gst, body, wrote=True, warnings=warnings, errors=errors)

