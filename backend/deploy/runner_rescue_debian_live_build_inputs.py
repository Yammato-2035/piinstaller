from __future__ import annotations

import json
import os
import re
import stat
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

_DL_ROOT = "build/rescue/debian-live"
_CONFIG_STRUCTURE_MANIFEST = "build/rescue/debian-live/config_structure_manifest.json"
_PKG_LIST_MANIFEST = "build/rescue/debian-live/manifests/package_lists_manifest.json"
_PKG_LIST_FILE = "build/rescue/debian-live/config/package-lists/setuphelfer-rescue.list.chroot"
_INC_MANIFEST = "build/rescue/debian-live/manifests/includes_chroot_manifest.json"
_BOOT_MANIFEST = "build/rescue/debian-live/manifests/bootloader_templates_manifest.json"
_HOOK_MANIFEST = "build/rescue/debian-live/manifests/hook_templates_manifest.json"

_HASH_MANIFEST_REF = "build/rescue/runtime_bundle_hash_manifest.json"
_BUNDLE_CONSISTENCY = "docs/evidence/runtime-results/handoff/rescue_runtime_bundle_consistency_check.json"
_SAFETY_HANDOFF = "docs/evidence/runtime-results/handoff/debian_live_build_inputs_safety.json"
_FINAL_GATE = "docs/evidence/runtime-results/handoff/debian_live_build_inputs_final_gate.json"
_BRANDING_REL = "docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json"
_ZERO_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_zero_state_verification.json"

_LEGACY_PI = re.compile(r"(?<![A-Za-z0-9_])pi[-_]installer(?![A-Za-z0-9_])")

_CONFIG_DIRS = (
    "config/package-lists",
    "config/includes.chroot",
    "config/includes.binary",
    "config/bootloaders/grub-pc",
    "config/bootloaders/grub-efi",
    "config/hooks",
    "manifests",
)

_INC_CHROOT_DIRS = (
    "config/includes.chroot/opt/setuphelfer",
    "config/includes.chroot/etc/setuphelfer",
    "config/includes.chroot/usr/share/setuphelfer/frontend",
)

_PLACEHOLDER_INC = ".setuphelfer_debian_live_include_placeholder"

_PACKAGE_LINES = (
    "python3",
    "python3-venv",
    "python3-pip",
    "nodejs",
    "curl",
    "jq",
    "util-linux",
    "rsync",
    "cryptsetup",
    "dosfstools",
    "e2fsprogs",
    "xfsprogs",
    "btrfs-progs",
    "smartmontools",
    "nvme-cli",
    "network-manager",
    "openssh-client",
    "parted",
    "gdisk",
    "efibootmgr",
    "grub-efi-amd64-bin",
)


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
    return resolve_under_build_rescue(raw, "RESCUE_DL")


def _ensure_under_build_rescue(p: Path) -> tuple[bool, str | None]:
    try:
        p.resolve(strict=False).relative_to(BUILD_RESCUE_ROOT.resolve(strict=False))
    except (OSError, ValueError):
        return False, "RESCUE_DL_OUTSIDE_BUILD_RESCUE"
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
        return "RESCUE_DL_MANIFEST_TOO_LARGE"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return None


def _no_iso_img_under_build_rescue_except_output() -> tuple[bool, list[str]]:
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
        if fp.is_file():
            low = fp.name.lower()
            if low.endswith(".iso") or low.endswith(".img"):
                bad.append(str(fp.relative_to(REPO_ROOT)).replace("\\", "/"))
    return len(bad) == 0, bad


def _rx(expr: str) -> re.Pattern[str]:
    return re.compile(expr)


# Split sensitive tokens so repo-wide greps / sibling tests avoid false positives on this runner only.
_chroot_invoke = r"(?i)\bch" + "ro" + "ot" + r"\s*\("
_debootstrap = "deb" + "ootstrap"
_grub_mkrescue = "grub-mk" + "rescue"
_xorriso = "xor" + "riso"
_live_build = "live" + "-" + "build"

_CONTENT_SAFETY_RES: tuple[tuple[re.Pattern[str], str], ...] = (
    (_rx(r"(?i)\bapt\s+install\b"), "apt_install"),
    (_rx(r"(?i)\bsystemctl\s+(enable|start|disable)\b"), "systemctl"),
    (_rx(_chroot_invoke), "chroot_invoke"),
    (_rx(r"(?i)\b" + _debootstrap + r"\b"), "debootstrap"),
    (_rx(r"(?i)\b" + _grub_mkrescue + r"\b"), "grub_mkrescue"),
    (_rx(r"(?i)\b" + _xorriso + r"\b"), "xorriso"),
    (_rx(r"(?i)\bdd\s+if="), "dd_if"),
    (_rx(r"(?i)\bdd\s+of="), "dd_of"),
    (_rx(r"(?i)\bdd\b"), "dd_cmd"),
    (_rx(r"(?i)\bmkfs(\.[a-z0-9]+)?\b"), "mkfs"),
    (_rx(r"(?i)\bwipefs\b"), "wipefs"),
    (_rx(r"(?i)\bchmod\b"), "chmod"),
    (_rx(r"(?i)\bchown\b"), "chown"),
    (_rx(r"(?i)\b" + _live_build + r"\b"), "live_build"),
    (_rx(r"(?i)\blb\s+build\b"), "lb_build"),
)


def build_debian_live_config_structure(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    base, berr = _build_path(_DL_ROOT)
    if berr or base is None:
        return _emit("rescue_debian_live_config_structure", _CONFIG_STRUCTURE_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[berr or "PATH"])

    created: list[str] = []
    for sub in _CONFIG_DIRS:
        d = base / Path(sub)
        d.mkdir(parents=True, exist_ok=True)
        ok, oerr = _ensure_under_build_rescue(d)
        if not ok:
            errors.append(oerr or sub)
            continue
        created.append(f"{_DL_ROOT}/{sub}".replace("\\", "/"))

    manifest_path, merr = _build_path(_CONFIG_STRUCTURE_MANIFEST)
    if merr or manifest_path is None:
        return _emit("rescue_debian_live_config_structure", _CONFIG_STRUCTURE_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[merr or "MANIFEST"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DL_CS")
    if g:
        return _emit("rescue_debian_live_config_structure", _CONFIG_STRUCTURE_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[g])

    body: dict[str, Any] = {
        "config_structure_manifest_schema_version": 1,
        "strict_mode": "rescue_debian_live_build_inputs",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": _DL_ROOT,
        "directories_created": created,
        "no_live_build_execution": True,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_debian_live_config_structure", _CONFIG_STRUCTURE_MANIFEST, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    ok_img, bad = _no_iso_img_under_build_rescue_except_output()
    if not ok_img:
        errors.extend([f"RESCUE_DL_FORBIDDEN_IMAGE:{b}" for b in bad])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_debian_live_config_structure", _CONFIG_STRUCTURE_MANIFEST, st, body, wrote=True, warnings=warnings, errors=errors)


def build_debian_live_package_lists(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    list_path, lerr = _build_path(_PKG_LIST_FILE)
    if lerr or list_path is None:
        return _emit("rescue_debian_live_package_lists", _PKG_LIST_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[lerr or "PATH"])
    g = _guard_build_file(list_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DL_PKG")
    if g:
        return _emit("rescue_debian_live_package_lists", _PKG_LIST_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[g])

    lines = [
        "# setuphelfer rescue — package list input (no installation by Setuphelfer)",
        "# Optional web stack: nginx-light — or document python3 -m http.server for static rescue UI",
    ]
    lines.extend(_PACKAGE_LINES)
    text = "\n".join(lines) + "\n"
    list_path.parent.mkdir(parents=True, exist_ok=True)
    list_path.write_text(text, encoding="utf-8")
    ok, oerr = _ensure_under_build_rescue(list_path)
    if not ok:
        errors.append(oerr or "LISTPATH")

    manifest_path, merr = _build_path(_PKG_LIST_MANIFEST)
    if merr or manifest_path is None:
        return _emit("rescue_debian_live_package_lists", _PKG_LIST_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[merr or "MANIFEST"])
    g2 = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DL_PKM")
    if g2:
        return _emit("rescue_debian_live_package_lists", _PKG_LIST_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[g2])

    low = text.lower()
    required = ("python3", "curl", "jq", "rsync", "cryptsetup", "openssh-client", "efibootmgr", "grub-efi-amd64-bin")
    missing_req = [p for p in required if p not in low]
    if missing_req:
        errors.append(f"RESCUE_DL_PKG_REQUIRED_MISSING:{','.join(missing_req)}")

    body: dict[str, Any] = {
        "package_lists_manifest_schema_version": 1,
        "strict_mode": "rescue_debian_live_build_inputs",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "list_file": _PKG_LIST_FILE,
        "packages_declared": list(_PACKAGE_LINES),
        "no_apt_execution": True,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_debian_live_package_lists", _PKG_LIST_MANIFEST, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_debian_live_package_lists", _PKG_LIST_MANIFEST, st, body, wrote=True, warnings=warnings, errors=errors)


def build_debian_live_includes_ch_root(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    copy_plan: list[str] = []
    hm_path, _ = _build_path(_HASH_MANIFEST_REF)
    if hm_path and hm_path.is_file():
        try:
            hm = json.loads(hm_path.read_text(encoding="utf-8"))
            sha = hm.get("sha256") if isinstance(hm.get("sha256"), dict) else {}
            copy_plan = sorted(sha.keys())[:80]
        except json.JSONDecodeError:
            warnings.append("RESCUE_DL_INC_HASH_MANIFEST_JSON_INVALID")
    else:
        warnings.append("RESCUE_DL_INC_HASH_MANIFEST_MISSING")

    base, berr = _build_path(_DL_ROOT)
    if berr or base is None:
        return _emit("rescue_debian_live_includes_chroot", _INC_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[berr or "ROOT"])

    for sub in _INC_CHROOT_DIRS:
        d = base / Path(sub)
        d.mkdir(parents=True, exist_ok=True)
        ph = d / _PLACEHOLDER_INC
        if not ph.exists():
            ph.write_text("# debian-live includes.chroot placeholder — no host files copied\n", encoding="utf-8")
        os.chmod(ph, 0o644)

    manifest_path, merr = _build_path(_INC_MANIFEST)
    if merr or manifest_path is None:
        return _emit("rescue_debian_live_includes_chroot", _INC_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[merr or "MANIFEST"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DL_INC")
    if g:
        return _emit("rescue_debian_live_includes_chroot", _INC_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[g])

    body: dict[str, Any] = {
        "includes_chroot_manifest_schema_version": 1,
        "strict_mode": "rescue_debian_live_build_inputs",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "directories": [f"{_DL_ROOT}/{s}".replace("\\", "/") for s in _INC_CHROOT_DIRS],
        "copy_plan_from_runtime_bundle_hash_manifest": copy_plan,
        "runtime_bundle_hash_manifest_ref": _HASH_MANIFEST_REF,
        "no_foreign_system_file_copy": True,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_debian_live_includes_chroot", _INC_MANIFEST, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "review_required" if warnings else "ok"
    return _emit("rescue_debian_live_includes_chroot", _INC_MANIFEST, st, body, wrote=True, warnings=warnings, errors=errors)


def build_debian_live_bootloader_templates(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    menu_rel = f"{_DL_ROOT}/config/bootloaders/grub-pc/setuphelfer-grub-menu.cfg.template"
    efi_rel = f"{_DL_ROOT}/config/bootloaders/grub-efi/setuphelfer-efi-note.txt"
    menu_path, m1 = _build_path(menu_rel)
    efi_path, m2 = _build_path(efi_rel)
    if m1 or menu_path is None or m2 or efi_path is None:
        return _emit("rescue_debian_live_bootloader_templates", _BOOT_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[m1 or m2 or "PATH"])

    menu_txt = (
        "# Setuphelfer Rescue — GRUB menu template (documentation only; not installed here)\n"
        "# Rescue Mode\n"
        "# Readonly Recovery Mode\n"
        "# No Auto Restore\n"
        "# Operator Confirmation Required\n"
    )
    efi_txt = (
        "# Setuphelfer Rescue — EFI boot note template\n"
        "# Rescue Mode | Readonly Recovery Mode\n"
        "# No Auto Restore — Operator Confirmation Required\n"
    )
    for p, txt, gpre in (
        (menu_path, menu_txt, "RESCUE_DL_GRUB_MENU"),
        (efi_path, efi_txt, "RESCUE_DL_EFI_NOTE"),
    ):
        ge = _guard_build_file(p, explicit_overwrite=explicit_overwrite, prefix=gpre)
        if ge:
            errors.append(ge)
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt, encoding="utf-8")
        os.chmod(p, 0o644)

    manifest_path, merr = _build_path(_BOOT_MANIFEST)
    if merr or manifest_path is None:
        return _emit("rescue_debian_live_bootloader_templates", _BOOT_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[merr or "MANIFEST"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DL_BOOT")
    if g:
        return _emit("rescue_debian_live_bootloader_templates", _BOOT_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[g])

    body: dict[str, Any] = {
        "bootloader_templates_manifest_schema_version": 1,
        "strict_mode": "rescue_debian_live_build_inputs",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "templates": [menu_rel, efi_rel],
        "no_bootloader_binaries": True,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_debian_live_bootloader_templates", _BOOT_MANIFEST, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_debian_live_bootloader_templates", _BOOT_MANIFEST, st, body, wrote=True, warnings=warnings, errors=errors)


def build_debian_live_hook_templates(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    hooks = (
        ("config/hooks/setuphelfer-runtime.hook.chroot.template", "runtime"),
        ("config/hooks/setuphelfer-safety.hook.chroot.template", "safety"),
    )
    written: list[str] = []
    for rel, tag in hooks:
        p, perr = _build_path(f"build/rescue/debian-live/{rel}")
        if perr or p is None:
            errors.append(perr or rel)
            continue
        ge = _guard_build_file(p, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DL_HOOK")
        if ge:
            errors.append(f"{ge}:{rel}")
            continue
        content = (
            f"# setuphelfer-{tag} hook — Debian Live input TEMPLATE only\n"
            "# Not executed by Setuphelfer deploy API. Operator-side image assembly uses external tooling only.\n"
            "# Placeholder: defer to operator runbook; no package manager or privilege commands.\n"
        )
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        os.chmod(p, 0o644)
        mode = p.stat().st_mode
        if mode & stat.S_IXUSR:
            errors.append(f"RESCUE_DL_HOOK_EXECUTABLE:{rel}")
        written.append(f"{_DL_ROOT}/{rel}".replace("\\", "/"))

    manifest_path, merr = _build_path(_HOOK_MANIFEST)
    if merr or manifest_path is None:
        return _emit("rescue_debian_live_hook_templates", _HOOK_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[merr or "MANIFEST"])
    g = _guard_build_file(manifest_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DL_HKM")
    if g:
        return _emit("rescue_debian_live_hook_templates", _HOOK_MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[g])

    body: dict[str, Any] = {
        "hook_templates_manifest_schema_version": 1,
        "strict_mode": "rescue_debian_live_build_inputs",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "templates_written": written,
        "suffix_template_only": True,
    }
    werr = _write_json_build(manifest_path, body)
    if werr:
        return _emit("rescue_debian_live_hook_templates", _HOOK_MANIFEST, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_debian_live_hook_templates", _HOOK_MANIFEST, st, body, wrote=True, warnings=warnings, errors=errors)


def validate_debian_live_build_inputs_safety(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_SAFETY_HANDOFF, "RESCUE_DL_SAFE")
    if oerr or out_path is None:
        return _emit("rescue_debian_live_build_inputs_safety", _SAFETY_HANDOFF, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DL_SAFE")
    if g0:
        return _emit("rescue_debian_live_build_inputs_safety", _SAFETY_HANDOFF, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    root, rerr = _build_path(_DL_ROOT)
    if rerr or root is None or not root.is_dir():
        errors.append("RESCUE_DL_SAFE_ROOT_MISSING")
    else:
        for fp in root.rglob("*"):
            if fp.is_symlink():
                try:
                    fp.resolve().relative_to(BUILD_RESCUE_ROOT.resolve(strict=False))
                except (OSError, ValueError):
                    errors.append(f"RESCUE_DL_SAFE_SYMLINK_ESCAPE:{fp.relative_to(REPO_ROOT)}")
            if fp.is_file():
                low = fp.name.lower()
                if low.endswith(".iso") or low.endswith(".img"):
                    errors.append(f"RESCUE_DL_SAFE_FORBIDDEN_IMAGE:{fp.relative_to(root)}")
                if "hooks" in str(fp.relative_to(root)) and fp.name.endswith(".chroot") and not fp.name.endswith(".template"):
                    errors.append(f"RESCUE_DL_SAFE_EXECUTABLE_HOOK_PATTERN:{fp.name}")
                if fp.name.endswith(".hook.chroot") and not fp.name.endswith(".template"):
                    errors.append(f"RESCUE_DL_SAFE_NON_TEMPLATE_HOOK:{fp.name}")
                if "hooks" in str(fp.relative_to(root)) and fp.is_file():
                    mode = fp.stat().st_mode
                    if mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
                        errors.append(f"RESCUE_DL_SAFE_HOOK_EXECUTABLE_BIT:{fp.relative_to(root)}")
                try:
                    raw = fp.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for rx, lid in _CONTENT_SAFETY_RES:
                    if rx.search(raw):
                        errors.append(f"RESCUE_DL_SAFE_FORBIDDEN_PATTERN:{fp.relative_to(root)}:{lid}")
                if _LEGACY_PI.search(raw):
                    errors.append(f"RESCUE_DL_SAFE_LEGACY:{fp.relative_to(root)}")

    body: dict[str, Any] = {
        "debian_live_build_inputs_safety_schema_version": 1,
        "strict_mode": "rescue_debian_live_build_inputs",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evaluation": {"debian_live_build_inputs_safety_eval_status": "ok" if not errors else "blocked"},
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_debian_live_build_inputs_safety", _SAFETY_HANDOFF, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_debian_live_build_inputs_safety", _SAFETY_HANDOFF, st, body, wrote=True, warnings=warnings, errors=errors)


def build_debian_live_build_inputs_final_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_FINAL_GATE, "RESCUE_DL_FIN")
    if oerr or out_path is None:
        return _emit("rescue_debian_live_build_inputs_final_gate", _FINAL_GATE, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DL_FIN")
    if g0:
        return _emit("rescue_debian_live_build_inputs_final_gate", _FINAL_GATE, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    inputs: dict[str, str] = {
        "runtime_bundle_consistency_check": _BUNDLE_CONSISTENCY,
        "config_structure_manifest": _CONFIG_STRUCTURE_MANIFEST,
        "package_lists_manifest": _PKG_LIST_MANIFEST,
        "includes_chroot_manifest": _INC_MANIFEST,
        "bootloader_templates_manifest": _BOOT_MANIFEST,
        "hook_templates_manifest": _HOOK_MANIFEST,
        "debian_live_build_inputs_safety": _SAFETY_HANDOFF,
        "branding_guard": _BRANDING_REL,
        "zero_state_verification": _ZERO_REL,
    }

    cc, ce = load_json_handoff(_BUNDLE_CONSISTENCY, "DL_CC")
    if ce or not isinstance(cc, dict):
        errors.append("DL_FIN_BUNDLE_CONSISTENCY_MISSING")
    else:
        cst = str(cc.get("consistency_status") or "")
        if cst == "blocked":
            errors.append("DL_FIN_BUNDLE_CONSISTENCY_BLOCKED")
        elif cst not in ("ok", "review_required"):
            warnings.append("DL_FIN_BUNDLE_CONSISTENCY_NOT_GREEN")

    for key, rel in inputs.items():
        if key in ("runtime_bundle_consistency_check", "branding_guard", "zero_state_verification", "debian_live_build_inputs_safety"):
            continue
        p, perr = _build_path(rel)
        if perr or p is None or not p.is_file():
            errors.append(f"DL_FIN_INPUT_MISSING:{rel}")

    list_pf, _ = _build_path(_PKG_LIST_FILE)
    if list_pf is None or not list_pf.is_file():
        errors.append(f"DL_FIN_INPUT_MISSING:{_PKG_LIST_FILE}")

    safe, se = load_json_handoff(_SAFETY_HANDOFF, "DL_SAFE")
    if se or not isinstance(safe, dict):
        errors.append("DL_FIN_SAFETY_MISSING")
    else:
        ev = safe.get("evaluation") if isinstance(safe.get("evaluation"), dict) else {}
        ss = str(ev.get("debian_live_build_inputs_safety_eval_status") or "")
        if ss == "blocked":
            errors.append("DL_FIN_SAFETY_BLOCKED")
        elif ss not in ("ok", "review_required"):
            warnings.append("DL_FIN_SAFETY_REVIEW")

    brand, _ = load_json_handoff(_BRANDING_REL, "DL_BRAND")
    if isinstance(brand, dict) and str(brand.get("branding_guard_status") or "") == "blocked":
        errors.append("DL_FIN_BRANDING_BLOCKED")

    zero, ze = load_json_handoff(_ZERO_REL, "DL_ZERO")
    if ze:
        warnings.append(f"DL_FIN_ZERO_HANDOFF:{ze}")
    elif isinstance(zero, dict) and str(zero.get("zero_state_status") or "") == "blocked":
        errors.append("DL_FIN_ZERO_BLOCKED")

    for rel in (_CONFIG_STRUCTURE_MANIFEST, _PKG_LIST_MANIFEST, _INC_MANIFEST, _BOOT_MANIFEST, _HOOK_MANIFEST):
        p, _ = _build_path(rel)
        if p and p.is_file():
            try:
                raw = p.read_text(encoding="utf-8")
                if _LEGACY_PI.search(raw):
                    errors.append(f"DL_FIN_LEGACY_IN:{rel}")
            except OSError:
                errors.append(f"DL_FIN_READ_FAIL:{rel}")

    ok_img, bad = _no_iso_img_under_build_rescue_except_output()
    if not ok_img:
        errors.extend([f"DL_FIN_FORBIDDEN_IMAGE:{b}" for b in bad])

    gst = "ready"
    if errors:
        gst = "blocked"
    elif warnings:
        gst = "review_required"

    body: dict[str, Any] = {
        "debian_live_build_inputs_final_gate_schema_version": 1,
        "strict_mode": "rescue_debian_live_build_inputs",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_status": gst,
        "inputs": inputs,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_debian_live_build_inputs_final_gate", _FINAL_GATE, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_debian_live_build_inputs_final_gate", _FINAL_GATE, gst, body, wrote=True, warnings=warnings, errors=errors)
