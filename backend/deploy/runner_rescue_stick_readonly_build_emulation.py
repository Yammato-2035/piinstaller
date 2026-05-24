"""
Setuphelfer Rettungsstick – read-only Build-Emulation (kein lb build, kein ISO, kein apt).

Schreibt nur unter ``build/rescue/emulation/`` und ``docs/evidence/runtime-results/handoff/``.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from deploy.runner_rescue_io import (
    REPO_ROOT,
    atomic_write_text,
    guard_handoff_overwrite,
    resolve_handoff_path,
    resolve_under_build_rescue,
    write_json_handoff,
)

Status = Literal["ok", "review_required", "blocked", "ready"]
EmulStatus = Literal["ok", "review_required", "blocked"]

_EMUL_PREFIX = "build/rescue/emulation"
_MAX_JSON = 900_000
_MAX_HANDOFF = 512 * 1024

_WS = f"{_EMUL_PREFIX}/rescue_stick_build_workspace_snapshot.json"
_TREE = f"{_EMUL_PREFIX}/rescue_stick_expected_debian_live_tree.json"
_PKG = f"{_EMUL_PREFIX}/rescue_stick_package_list_preview.json"
_RT = f"{_EMUL_PREFIX}/rescue_stick_runtime_bundle_preview.json"
_FE = f"{_EMUL_PREFIX}/rescue_stick_frontend_bundle_preview.json"
_SVC = f"{_EMUL_PREFIX}/rescue_stick_systemd_service_preview.json"
_NET = f"{_EMUL_PREFIX}/rescue_stick_network_webui_preview.json"
_MANIFEST = "docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_emulation_manifest.json"
_FINAL = "docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_final_gate.json"

_READONLY_FLAGS = {
    "generated": False,
    "readonly_emulated": True,
    "no_real_build_execution": True,
}

_FORBIDDEN_ARTIFACT_SUFFIXES = (
    ".iso",
    ".img",
    ".qcow2",
    ".qcow",
    ".vdi",
    ".vmdk",
    ".squashfs",
)
_FORBIDDEN_ARTIFACT_NAMES = frozenset(
    {"filesystem.squashfs", "initrd.img", "vmlinuz", "live-image-amd64.hybrid.iso"}
)

_FORBIDDEN_EXEC_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)\blb\s+build\b"), "lb_build"),
    (re.compile(r"(?i)\bdebootstrap\b"), "debootstrap"),
    (re.compile(r"(?i)(?<![./\w])chroot\s+"), "chroot"),
    (re.compile(r"(?i)\bapt\s+install\b"), "apt_install"),
    (re.compile(r"(?i)\bapt\s+upgrade\b"), "apt_upgrade"),
    (re.compile(r"(?i)\bmount\s+"), "mount"),
    (re.compile(r"(?i)\bumount\s+"), "umount"),
    (re.compile(r"(?i)\bxorriso\b"), "xorriso"),
    (re.compile(r"(?i)\bgrub-mkrescue\b"), "grub_mkrescue"),
    (re.compile(r"(?i)\bqemu\b"), "qemu"),
    (re.compile(r"(?i)\bdd\s+if="), "dd_if"),
)

_DOC_FORBIDDEN_HINTS = (
    "kein lb build",
    "no `lb build`",
    "verbieten",
    "forbidden",
    "nicht ausführen",
    "not executed",
    "documented_forbidden",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_short_head() -> str:
    head = REPO_ROOT / ".git" / "HEAD"
    if not head.is_file():
        return "unknown"
    raw = head.read_text(encoding="utf-8").strip()
    if raw.startswith("ref: "):
        ref = REPO_ROOT / ".git" / raw[5:].strip()
        if ref.is_file():
            return ref.read_text(encoding="utf-8").strip()[:12]
    return raw[:12] if raw else "unknown"


def _git_branch() -> str:
    head = REPO_ROOT / ".git" / "HEAD"
    if not head.is_file():
        return "unknown"
    raw = head.read_text(encoding="utf-8").strip()
    if raw.startswith("ref: "):
        return raw[5:].split("/")[-1] or "unknown"
    return "detached"


def _repo_rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return path.name


def _emul_path(rel: str) -> tuple[Path | None, str | None]:
    raw = rel if rel.startswith(_EMUL_PREFIX) else f"{_EMUL_PREFIX}/{rel.lstrip('/')}"
    return resolve_under_build_rescue(raw, "RESCUE_STICK_EMUL")


def _write_emul(path: Path, obj: dict[str, Any], *, explicit_overwrite: bool) -> tuple[bool, list[str]]:
    g = guard_handoff_overwrite(path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_STICK_EMUL")
    if g:
        return False, [g]
    err = write_json_handoff(path, obj, max_bytes=_MAX_JSON)
    if err:
        return False, [err]
    return True, []


def _emit(
    prefix: str,
    rel: str,
    status: str,
    body: dict[str, Any],
    *,
    wrote: bool,
    warnings: list[str],
    errors: list[str],
) -> dict[str, Any]:
    return {
        f"{prefix}_status": status,
        f"{prefix}_file_path": rel,
        prefix: body,
        f"{prefix}_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _doc_exists(rel: str) -> bool:
    p = REPO_ROOT / rel
    return p.is_file()


def _load_emul_json(rel: str) -> dict[str, Any] | None:
    p, err = _emul_path(rel)
    if err or p is None or not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def build_rescue_stick_build_workspace_snapshot(
    *,
    explicit_overwrite: bool = False,
    runtime_gate_exit_0: bool | None = None,
) -> dict[str, Any]:
    rel = _WS
    path, perr = _emul_path(rel)
    if perr or path is None:
        return _emit("rescue_stick_build_workspace_snapshot", rel, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])

    warnings: list[str] = []
    errors: list[str] = []
    partitions_ok = _doc_exists("docs/evidence/partitions/PARTITIONS_FINAL_BROWSER_UI_SMOKE.md")
    if partitions_ok:
        text = (REPO_ROOT / "docs/evidence/partitions/PARTITIONS_FINAL_BROWSER_UI_SMOKE.md").read_text(
            encoding="utf-8", errors="replace"
        )
        if "green" not in text.lower():
            warnings.append("RESCUE_STICK_WS_PARTITIONS_SMOKE_NOT_GREEN")
    else:
        errors.append("RESCUE_STICK_WS_PARTITIONS_SMOKE_MISSING")

    handoff_doc = _doc_exists("docs/evidence/rescue/RESCUE_STICK_PARTITION_HANDOFF_READONLY.md")
    gate_doc = _doc_exists("docs/architecture/RESCUE_STICK_READONLY_BUILD_GATE.md")
    if not handoff_doc:
        warnings.append("RESCUE_STICK_WS_HANDOFF_DOC_MISSING")
    if not gate_doc:
        errors.append("RESCUE_STICK_WS_READONLY_GATE_DOC_MISSING")

    if runtime_gate_exit_0 is False:
        warnings.append("RESCUE_STICK_WS_RUNTIME_GATE_NOT_ZERO")

    body: dict[str, Any] = {
        "schema_version": "1.0",
        "component": "rescue_stick_readonly_build_emulation",
        "snapshot_status": "ok",
        **_READONLY_FLAGS,
        "generated_at": _utc_now(),
        "workspace": {
            "repo_root": ".",
            "head": _git_short_head(),
            "branch": _git_branch(),
            "runtime_gate_required": True,
            "runtime_gate_exit_0_documented": runtime_gate_exit_0,
        },
        "inputs": {
            "partitions_finalized": partitions_ok,
            "rescue_handoff_docs_present": handoff_doc,
            "readonly_build_gate_present": gate_doc,
        },
        "warnings": warnings,
        "errors": errors,
    }
    if errors:
        body["snapshot_status"] = "blocked"
    elif warnings:
        body["snapshot_status"] = "review_required"

    wrote, werr = _write_emul(path, body, explicit_overwrite=explicit_overwrite)
    errors.extend(werr)
    st = str(body["snapshot_status"])
    if werr:
        st = "blocked"
    return _emit("rescue_stick_build_workspace_snapshot", rel, st, body, wrote=wrote, warnings=warnings, errors=errors)


def _tree_entry(path: str, typ: str, purpose: str) -> dict[str, Any]:
    return {
        "path": path,
        "type": typ,
        "expected": True,
        "generated": False,
        "readonly_emulated": True,
        "purpose": purpose,
    }


def build_rescue_stick_expected_debian_live_tree(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    rel = _TREE
    path, perr = _emul_path(rel)
    if perr or path is None:
        return _emit("rescue_stick_expected_debian_live_tree", rel, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])

    entries = [
        _tree_entry("config/", "directory", "live-build configuration root"),
        _tree_entry("config/package-lists/setuphelfer.list.chroot", "file", "chroot package list (preview only)"),
        _tree_entry("config/includes.chroot/opt/setuphelfer/", "directory", "Setuphelfer runtime bundle target"),
        _tree_entry(
            "config/includes.chroot/etc/systemd/system/setuphelfer-backend.service",
            "file",
            "backend unit for live session",
        ),
        _tree_entry(
            "config/includes.chroot/etc/systemd/system/setuphelfer.service",
            "file",
            "frontend/static UI unit for live session",
        ),
        _tree_entry("config/hooks/normal/", "directory", "live-build hooks (no execution in emulation)"),
        _tree_entry("config/bootloaders/", "directory", "bootloader config preview"),
        _tree_entry("binary/", "directory", "expected lb binary stage (not created)"),
        _tree_entry("chroot/", "directory", "expected lb chroot stage (not created)"),
        _tree_entry("cache/", "directory", "lb cache (not created)"),
        _tree_entry("local/", "directory", "lb local overrides (not created)"),
        _tree_entry("build/", "directory", "lb build workspace (not created)"),
    ]
    body = {
        "schema_version": "1.0",
        "component": "rescue_stick_expected_debian_live_tree",
        "tree_status": "ok",
        **_READONLY_FLAGS,
        "generated_at": _utc_now(),
        "entries": entries,
        "forbidden_real_artifacts": list(_FORBIDDEN_ARTIFACT_NAMES),
        "warnings": [],
        "errors": [],
    }
    wrote, errors = _write_emul(path, body, explicit_overwrite=explicit_overwrite)
    st = "blocked" if errors else "ok"
    return _emit("rescue_stick_expected_debian_live_tree", rel, st, body, wrote=wrote, warnings=[], errors=errors)


def _pkg(
    name: str,
    category: str,
    *,
    required: bool,
    status: str,
    reason: str,
    runtime_use: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "category": category,
        "required": required,
        "status": status,
        "reason": reason,
        "runtime_use": runtime_use,
        "dangerous_by_itself": False,
    }


def build_rescue_stick_package_list_preview(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    rel = _PKG
    path, perr = _emul_path(rel)
    if perr or path is None:
        return _emit("rescue_stick_package_list_preview", rel, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])

    packages: list[dict[str, Any]] = [
        _pkg("systemd", "base_system", required=True, status="ok", reason="init and units", runtime_use="service_runtime"),
        _pkg("ca-certificates", "base_system", required=True, status="ok", reason="TLS", runtime_use="read_only"),
        _pkg("curl", "base_system", required=True, status="ok", reason="health checks", runtime_use="read_only"),
        _pkg("jq", "base_system", required=True, status="ok", reason="JSON tooling", runtime_use="read_only"),
        _pkg(
            "systemd-networkd",
            "network",
            required=False,
            status="ok",
            reason="phase_1_default; live_os_validation_pending",
            runtime_use="service_runtime",
        ),
        _pkg(
            "network-manager",
            "network",
            required=False,
            status="optional_later",
            reason="not phase_1_default; live_os_validation_pending",
            runtime_use="optional",
        ),
        _pkg("openssh-client", "network", required=False, status="optional_later", reason="remote help", runtime_use="optional"),
        _pkg("avahi-daemon", "network", required=False, status="optional_later", reason="mDNS", runtime_use="optional"),
        _pkg("util-linux", "storage_readonly", required=True, status="ok", reason="lsblk", runtime_use="read_only"),
        _pkg("smartmontools", "storage_readonly", required=False, status="optional_later", reason="SMART read", runtime_use="read_only"),
        _pkg(
            "parted",
            "storage_readonly",
            required=False,
            status="optional_later",
            reason="CLI only later; no auto partition",
            runtime_use="optional",
        ),
        _pkg("ntfs-3g", "storage_readonly", required=False, status="optional_later", reason="read-only NTFS policy", runtime_use="read_only"),
        _pkg("python3", "python_runtime", required=True, status="ok", reason="backend runtime", runtime_use="service_runtime"),
        _pkg(
            "python3-venv",
            "python_runtime",
            required=False,
            status="ok",
            reason="runtime ships bundled venv under opt/setuphelfer/backend/venv",
            runtime_use="service_runtime",
        ),
        _pkg(
            "nginx",
            "webui_runtime",
            required=False,
            status="optional_later",
            reason="not phase_1; static UI via python http.server",
            runtime_use="optional",
        ),
        _pkg(
            "uvicorn",
            "webui_runtime",
            required=False,
            status="ok",
            reason="bundled in backend venv; not apt package on stick",
            runtime_use="service_runtime",
        ),
    ]
    categories = sorted({p["category"] for p in packages})
    blocking_review = sum(1 for p in packages if p["status"] == "review_required")
    list_status: EmulStatus = "ok" if blocking_review == 0 else "review_required"
    network_decided = any(p["name"] == "systemd-networkd" and p["status"] == "ok" for p in packages)
    pkg_warnings: list[str] = []
    if list_status == "review_required":
        pkg_warnings.append("RESCUE_STICK_PKG_BLOCKING_REVIEW_ITEMS")
    if network_decided:
        pkg_warnings.append("RESCUE_STICK_PKG_NETWORK_STACK_PHASE1_DEFAULT_SYSTEMD_NETWORKD")
    pkg_warnings.append("RESCUE_STICK_PKG_LIVE_OS_NETWORK_TEST_PENDING")
    body = {
        "schema_version": "1.0",
        "component": "rescue_stick_package_list_preview",
        "package_list_status": list_status,
        **_READONLY_FLAGS,
        "generated_at": _utc_now(),
        "categories": categories,
        "packages": packages,
        "selected_network_stack": "systemd-networkd",
        "live_os_network_test_pending": True,
        "real_iso_build_allowed": False,
        "emulation_ready": list_status == "ok",
        "reason": "Package list is emulation-ready; real Live-OS network validation remains separate gate.",
        "network_stack_decision": {
            "phase_1_default": "systemd-networkd",
            "alternative_optional_later": "network-manager",
            "lan_write": "blocked",
            "live_os_validation": "separate_hardware_gate",
        },
        "warnings": pkg_warnings,
        "errors": [],
    }
    wrote, errors = _write_emul(path, body, explicit_overwrite=explicit_overwrite)
    st = "blocked" if errors else list_status
    return _emit(
        "rescue_stick_package_list_preview",
        rel,
        st,
        body,
        wrote=wrote,
        warnings=list(body["warnings"]),
        errors=errors,
    )


def _scan_bundle_path(rel: str, *, forbidden_names: tuple[str, ...]) -> list[str]:
    issues: list[str] = []
    root = REPO_ROOT / rel
    if not root.exists():
        return [f"missing:{rel}"]
    if root.is_file():
        return issues
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if "__pycache__" in p.parts or "node_modules" in p.parts or ".git" in p.parts:
            continue
        name = p.name.lower()
        rel_p = _repo_rel(p)
        if name == ".env" or name.endswith(".env"):
            issues.append(f"secret_env:{rel_p}")
        for fn in forbidden_names:
            if fn in name or fn in rel_p.lower():
                issues.append(f"forbidden_name:{rel_p}")
        if any(rel_p.endswith(s) for s in (".tar.gz", ".tar", ".backup", ".restore")):
            issues.append(f"artifact:{rel_p}")
    return issues


def build_rescue_stick_runtime_bundle_preview(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    rel = _RT
    path, perr = _emul_path(rel)
    if perr or path is None:
        return _emit("rescue_stick_runtime_bundle_preview", rel, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])

    expected_dirs = [
        "backend/",
        "frontend/dist/",
        "scripts/",
        "config/",
        "docs/knowledge-base/",
        "docs/evidence/runtime-results/",
    ]
    issues: list[str] = []
    for d in expected_dirs:
        issues.extend(_scan_bundle_path(d, forbidden_names=("piinstaller", "pi-installer")))

    branding_hits: list[str] = []
    for scan in ("frontend/dist", "config"):
        root = REPO_ROOT / scan
        if not root.is_dir():
            continue
        for p in list(root.rglob("*.html"))[:20] + list(root.rglob("*.js"))[:10]:
            try:
                text = p.read_text(encoding="utf-8", errors="replace").lower()
            except OSError:
                continue
            if "piinstaller" in text and "setuphelfer" not in text:
                branding_hits.append(_repo_rel(p))

    warnings: list[str] = []
    errors: list[str] = []
    if branding_hits:
        warnings.append("RESCUE_STICK_RT_LEGACY_BRANDING_REVIEW")
    missing = [i for i in issues if i.startswith("missing:")]
    if missing:
        warnings.extend(missing)
    blocked_issues = [i for i in issues if i.startswith("secret_env:") or i.startswith("artifact:")]
    if blocked_issues:
        errors.extend(blocked_issues)

    bundle_status: EmulStatus = "blocked" if errors else ("review_required" if warnings else "ok")
    body = {
        "schema_version": "1.0",
        "component": "rescue_stick_runtime_bundle_preview",
        "runtime_bundle_status": bundle_status,
        **_READONLY_FLAGS,
        "generated_at": _utc_now(),
        "expected_root": "opt/setuphelfer/",
        "expected_paths": expected_dirs,
        "excluded_patterns": [".env", "node_modules", "__pycache__", "venv", "*.tar.gz", "backup", "restore"],
        "scan_issues": issues,
        "branding_review_paths": branding_hits[:10],
        "warnings": warnings,
        "errors": errors,
    }
    wrote, werr = _write_emul(path, body, explicit_overwrite=explicit_overwrite)
    errors.extend(werr)
    if werr:
        bundle_status = "blocked"
    return _emit(
        "rescue_stick_runtime_bundle_preview",
        rel,
        bundle_status,
        body,
        wrote=wrote,
        warnings=warnings,
        errors=errors,
    )


def build_rescue_stick_frontend_bundle_preview(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    rel = _FE
    path, perr = _emul_path(rel)
    if perr or path is None:
        return _emit("rescue_stick_frontend_bundle_preview", rel, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])

    dist = REPO_ROOT / "frontend" / "dist"
    index = dist / "index.html"
    warnings: list[str] = []
    errors: list[str] = []
    assets_js: list[str] = []
    assets_css: list[str] = []
    cdn_required = False

    if not index.is_file():
        warnings.append("RESCUE_STICK_FE_DIST_MISSING_BUILD_REQUIRED")
    else:
        html = index.read_text(encoding="utf-8", errors="replace")
        if "fonts.googleapis.com" in html or "cdn.jsdelivr" in html or "unpkg.com" in html:
            cdn_required = True
            warnings.append("RESCUE_STICK_FE_CDN_DEPENDENCY_REVIEW")
        if dist.is_dir():
            for p in dist.rglob("*.js"):
                assets_js.append(_repo_rel(p))
            for p in dist.rglob("*.css"):
                assets_css.append(_repo_rel(p))

    routes_expected = ["partitions", "backup", "restore", "rescue", "dashboard"]
    fe_status: EmulStatus = "blocked" if errors else ("review_required" if cdn_required else "ok")
    if not index.is_file() and not errors:
        fe_status = "review_required"
    body = {
        "schema_version": "1.0",
        "component": "rescue_stick_frontend_bundle_preview",
        "frontend_bundle_status": fe_status,
        **_READONLY_FLAGS,
        "generated_at": _utc_now(),
        "dist_present": index.is_file(),
        "index_html": _repo_rel(index) if index.is_file() else None,
        "assets_js": assets_js[:20],
        "assets_css": assets_css[:10],
        "rescue_relevant_routes": routes_expected,
        "offline_localhost": True,
        "external_cdn_required": cdn_required,
        "blocker_for_real_iso_build": cdn_required,
        "offline_font_policy": "system_fonts_only",
        "analytics_tracking": False,
        "cloud_update_required_for_rescue": False,
        "warnings": warnings,
        "errors": errors,
    }
    wrote, werr = _write_emul(path, body, explicit_overwrite=explicit_overwrite)
    errors.extend(werr)
    if werr:
        fe_status = "blocked"
    return _emit(
        "rescue_stick_frontend_bundle_preview",
        rel,
        fe_status,
        body,
        wrote=wrote,
        warnings=warnings,
        errors=errors,
    )


def build_rescue_stick_systemd_service_preview(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    rel = _SVC
    path, perr = _emul_path(rel)
    if perr or path is None:
        return _emit("rescue_stick_systemd_service_preview", rel, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])

    units = [
        {
            "unit": "setuphelfer-backend.service",
            "exec_start_preview": "/opt/setuphelfer/backend/venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000",
            "working_directory": "/opt/setuphelfer/backend",
            "user": "setuphelfer",
            "group": "setuphelfer",
            "protect_system": "strict",
            "protect_home": True,
            "bind_addresses": "127.0.0.1",
            "read_only_root_compatible": True,
            "writable_paths_preview": ["/var/lib/setuphelfer/evidence", "/run/setuphelfer"],
            "auto_restore_on_start": False,
            "auto_partition_on_start": False,
            "dangerous_actions_on_start": False,
        },
        {
            "unit": "setuphelfer.service",
            "exec_start_preview": "python3 -m http.server 3001 --directory /opt/setuphelfer/frontend/dist",
            "working_directory": "/opt/setuphelfer/frontend/dist",
            "user": "setuphelfer",
            "group": "setuphelfer",
            "protect_system": "strict",
            "protect_home": True,
            "bind_addresses": "127.0.0.1",
            "read_only_root_compatible": True,
            "writable_paths_preview": [],
            "auto_restore_on_start": False,
            "auto_partition_on_start": False,
            "dangerous_actions_on_start": False,
        },
    ]
    body = {
        "schema_version": "1.0",
        "component": "rescue_stick_systemd_service_preview",
        "systemd_preview_status": "ok",
        **_READONLY_FLAGS,
        "generated_at": _utc_now(),
        "units": units,
        "service_bind_decision": {
            "backend_bind": "127.0.0.1:8000",
            "webui_bind": "127.0.0.1:3001",
            "lan_bind": "blocked_until_rescue_lan_gate",
            "auto_restore_on_start": False,
            "auto_partition_on_start": False,
        },
        "warnings": ["RESCUE_STICK_SVC_LAN_GATE_OPTIONAL_LATER"],
        "errors": [],
    }
    wrote, errors = _write_emul(path, body, explicit_overwrite=explicit_overwrite)
    st = "blocked" if errors else "ok"
    return _emit(
        "rescue_stick_systemd_service_preview",
        rel,
        st,
        body,
        wrote=wrote,
        warnings=list(body["warnings"]),
        errors=errors,
    )


def build_rescue_stick_network_webui_preview(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    rel = _NET
    path, perr = _emul_path(rel)
    if perr or path is None:
        return _emit("rescue_stick_network_webui_preview", rel, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])

    body = {
        "schema_version": "1.0",
        "component": "rescue_stick_network_webui_preview",
        "network_webui_status": "ok",
        **_READONLY_FLAGS,
        "generated_at": _utc_now(),
        "access": {
            "localhost_http": "http://127.0.0.1:3001",
            "api_localhost": "http://127.0.0.1:8000",
            "default_access": "local_only",
            "lan_access": "blocked",
            "captive_portal": "optional_later",
            "mdns_setuphelfer_rescue_local": "optional_later",
            "qr_code_display": "optional_later",
        },
        "policies": {
            "cloud_mandatory": False,
            "telemetry": False,
            "lan_write_without_gate": "blocked",
            "write_actions_over_lan": "blocked",
            "rescue_auth_required_for_lan": True,
        },
        "lan_policy": {
            "default": "local_only",
            "lan_access": "blocked",
            "optional_later": True,
        },
        "warnings": ["RESCUE_STICK_NET_LAN_OPTIONAL_LATER"],
        "errors": [],
    }
    wrote, errors = _write_emul(path, body, explicit_overwrite=explicit_overwrite)
    st: EmulStatus = "blocked" if errors else "ok"
    return _emit(
        "rescue_stick_network_webui_preview",
        rel,
        st,
        body,
        wrote=wrote,
        warnings=list(body["warnings"]),
        errors=errors,
    )


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _scan_forbidden_artifacts() -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    root = REPO_ROOT / "build" / "rescue"
    if not root.is_dir():
        return hits
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        name = p.name.lower()
        if name in _FORBIDDEN_ARTIFACT_NAMES or any(name.endswith(s) for s in _FORBIDDEN_ARTIFACT_SUFFIXES):
            hits.append({"path": _repo_rel(p), "reason": "forbidden_artifact"})
    return hits


def _scan_forbidden_tokens_in_paths(paths: list[Path]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            lower = line.lower()
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            for pat, code in _FORBIDDEN_EXEC_PATTERNS:
                if not pat.search(line):
                    continue
                if "_tree_entry(" in line or "preview only" in lower or "not created" in lower:
                    ctx = "documented_forbidden"
                elif "re.compile" in line or "_FORBIDDEN" in line:
                    ctx = "pattern_definition"
                elif any(h in lower for h in _DOC_FORBIDDEN_HINTS):
                    ctx = "documented_forbidden"
                elif path.suffix == ".md" or "docs/" in _repo_rel(path):
                    ctx = "documented_forbidden"
                elif "no_real_build" in lower or "nicht " in lower or "kein " in lower:
                    ctx = "documented_forbidden"
                else:
                    ctx = "forbidden_execution_context"
                findings.append(
                    {
                        "path": _repo_rel(path),
                        "line": line_no,
                        "token": code,
                        "context": ctx,
                    }
                )
    return findings


def build_rescue_stick_evidence_manifest(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_MANIFEST, "RESCUE_STICK_MANIFEST")
    if oerr or out_path is None:
        return _emit("rescue_stick_evidence_manifest", _MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "PATH"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_STICK_MANIFEST")
    if gerr:
        return _emit("rescue_stick_evidence_manifest", _MANIFEST, "blocked", {}, wrote=False, warnings=[], errors=[gerr])

    emul_files = [
        _WS,
        _TREE,
        _PKG,
        _RT,
        _FE,
        _SVC,
        _NET,
    ]
    artifacts: list[dict[str, Any]] = []
    missing: list[str] = []
    for rel in emul_files:
        p, err = _emul_path(rel)
        if err or p is None or not p.is_file():
            missing.append(rel)
            continue
        artifacts.append({"path": rel, "sha256": _sha256_file(p), "size_bytes": p.stat().st_size})

    forbidden_artifacts = _scan_forbidden_artifacts()
    runner_path = REPO_ROOT / "backend" / "deploy" / "runner_rescue_stick_readonly_build_emulation.py"
    token_findings = _scan_forbidden_tokens_in_paths([runner_path])
    exec_hits = [f for f in token_findings if f.get("context") == "forbidden_execution_context"]
    doc_hits = [f for f in token_findings if f.get("context") != "forbidden_execution_context"]

    warnings: list[str] = []
    errors: list[str] = []
    if missing:
        errors.append("RESCUE_STICK_MANIFEST_EMUL_FILES_MISSING")
    if forbidden_artifacts:
        errors.append("RESCUE_STICK_MANIFEST_FORBIDDEN_ARTIFACTS_PRESENT")
    if exec_hits:
        errors.append("RESCUE_STICK_MANIFEST_FORBIDDEN_EXEC_TOKENS_IN_RUNNER")
    if doc_hits:
        warnings.append("RESCUE_STICK_MANIFEST_DOCUMENTED_FORBIDDEN_TERMS")

    manifest_status: EmulStatus = "blocked" if errors else ("review_required" if warnings else "ok")
    body = {
        "schema_version": "1.0",
        "component": "rescue_stick_evidence_manifest",
        "manifest_status": manifest_status,
        **_READONLY_FLAGS,
        "generated_at": _utc_now(),
        "emulation_files": artifacts,
        "missing_emulation_files": missing,
        "forbidden_artifacts_scan": forbidden_artifacts,
        "forbidden_tokens_scan": {
            "execution_context": exec_hits,
            "documented_or_review": doc_hits,
        },
        "warnings": warnings,
        "errors": errors,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    wrote = not werr
    if werr:
        errors.append(werr)
        manifest_status = "blocked"
    return _emit(
        "rescue_stick_evidence_manifest",
        _MANIFEST,
        manifest_status,
        body,
        wrote=wrote,
        warnings=warnings,
        errors=errors,
    )


def build_rescue_stick_readonly_build_final_gate(
    *,
    explicit_overwrite: bool = False,
    runtime_gate_exit_0: bool | None = None,
) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_FINAL, "RESCUE_STICK_FINAL")
    if oerr or out_path is None:
        return _emit("rescue_stick_readonly_build_final_gate", _FINAL, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "PATH"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_STICK_FINAL")
    if gerr:
        return _emit("rescue_stick_readonly_build_final_gate", _FINAL, "blocked", {}, wrote=False, warnings=[], errors=[gerr])

    errors: list[str] = []
    warnings: list[str] = []

    if not _doc_exists("docs/architecture/RESCUE_STICK_READONLY_BUILD_GATE.md"):
        errors.append("RESCUE_STICK_FINAL_GATE_DOC_MISSING")
    if not _doc_exists("docs/architecture/RESCUE_STICK_PARTITION_HANDOFF.md"):
        errors.append("RESCUE_STICK_FINAL_HANDOFF_DOC_MISSING")
    if not _doc_exists("docs/evidence/partitions/PARTITIONS_FINAL_BROWSER_UI_SMOKE.md"):
        errors.append("RESCUE_STICK_FINAL_PARTITIONS_SMOKE_MISSING")
    else:
        txt = (REPO_ROOT / "docs/evidence/partitions/PARTITIONS_FINAL_BROWSER_UI_SMOKE.md").read_text(
            encoding="utf-8", errors="replace"
        )
        if "**green**" not in txt and "Status: green" not in txt and "status\": \"green\"" not in txt:
            warnings.append("RESCUE_STICK_FINAL_PARTITIONS_SMOKE_NOT_GREEN")

    if runtime_gate_exit_0 is False:
        errors.append("RESCUE_STICK_FINAL_RUNTIME_GATE_NOT_ZERO")

    snapshots = {
        "workspace": _load_emul_json(_WS),
        "debian_live_tree": _load_emul_json(_TREE),
        "package_list": _load_emul_json(_PKG),
        "runtime_bundle": _load_emul_json(_RT),
        "frontend_bundle": _load_emul_json(_FE),
        "systemd": _load_emul_json(_SVC),
        "network_webui": _load_emul_json(_NET),
    }
    for key, data in snapshots.items():
        if data is None:
            errors.append(f"RESCUE_STICK_FINAL_MISSING_{key.upper()}")
            continue
        if data.get("no_real_build_execution") is not True:
            errors.append(f"RESCUE_STICK_FINAL_NO_REAL_BUILD_FALSE_{key.upper()}")
        if data.get("readonly_emulated") is not True:
            errors.append(f"RESCUE_STICK_FINAL_NOT_EMULATED_{key.upper()}")
        if data.get("generated") is True:
            errors.append(f"RESCUE_STICK_FINAL_GENERATED_TRUE_{key.upper()}")

    forbidden = _scan_forbidden_artifacts()
    if forbidden:
        errors.append("RESCUE_STICK_FINAL_FORBIDDEN_ARTIFACTS")

    manifest_path, _ = resolve_handoff_path(_MANIFEST, "RESCUE_STICK_FINAL_M")
    manifest_data = None
    if manifest_path and manifest_path.is_file():
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            errors.append("RESCUE_STICK_FINAL_MANIFEST_INVALID")
    else:
        warnings.append("RESCUE_STICK_FINAL_MANIFEST_NOT_WRITTEN_YET")

    if isinstance(manifest_data, dict) and manifest_data.get("manifest_status") == "blocked":
        errors.append("RESCUE_STICK_FINAL_MANIFEST_BLOCKED")

    review_components = []
    for key, data in snapshots.items():
        if not isinstance(data, dict):
            continue
        for field in (
            "snapshot_status",
            "tree_status",
            "package_list_status",
            "runtime_bundle_status",
            "frontend_bundle_status",
            "systemd_preview_status",
            "network_webui_status",
        ):
            if data.get(field) == "review_required":
                review_components.append(key)

    if review_components:
        warnings.append("RESCUE_STICK_FINAL_REVIEW_COMPONENTS:" + ",".join(review_components))

    pkg_snap = snapshots.get("package_list")
    live_os_pending = isinstance(pkg_snap, dict) and pkg_snap.get("live_os_network_test_pending") is True

    if errors:
        gate_status: Status = "blocked"
    elif warnings:
        gate_status = "review_required"
    else:
        gate_status = "ready"

    body = {
        "schema_version": "1.0",
        "component": "rescue_stick_readonly_build_final_gate",
        "gate_status": gate_status,
        **_READONLY_FLAGS,
        "generated_at": _utc_now(),
        "inputs_present": {k: v is not None for k, v in snapshots.items()},
        "runtime_gate_exit_0_documented": runtime_gate_exit_0,
        "write_defaults_blocked": True,
        "partitions_finalized": _doc_exists("docs/evidence/partitions/PARTITIONS_FINAL_BROWSER_UI_SMOKE.md"),
        "live_os_network_test_pending": live_os_pending,
        "real_iso_build_allowed": False,
        "warnings": warnings,
        "errors": errors,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    wrote = not werr
    if werr:
        errors.append(werr)
        gate_status = "blocked"
    return _emit(
        "rescue_stick_readonly_build_final_gate",
        _FINAL,
        gate_status,
        body,
        wrote=wrote,
        warnings=warnings,
        errors=errors,
    )


def run_rescue_stick_readonly_build_emulation_all(
    *,
    explicit_overwrite: bool = False,
    runtime_gate_exit_0: bool | None = True,
) -> dict[str, Any]:
    """Führt alle Emulations-Schritte in Reihenfolge aus (read-only)."""
    steps = [
        build_rescue_stick_build_workspace_snapshot,
        build_rescue_stick_expected_debian_live_tree,
        build_rescue_stick_package_list_preview,
        build_rescue_stick_runtime_bundle_preview,
        build_rescue_stick_frontend_bundle_preview,
        build_rescue_stick_systemd_service_preview,
        build_rescue_stick_network_webui_preview,
        build_rescue_stick_evidence_manifest,
        build_rescue_stick_readonly_build_final_gate,
    ]
    results: dict[str, Any] = {}
    for fn in steps:
        key = fn.__name__
        if fn in (
            build_rescue_stick_build_workspace_snapshot,
            build_rescue_stick_readonly_build_final_gate,
        ):
            results[key] = fn(explicit_overwrite=explicit_overwrite, runtime_gate_exit_0=runtime_gate_exit_0)
        else:
            results[key] = fn(explicit_overwrite=explicit_overwrite)
    final = results.get("build_rescue_stick_readonly_build_final_gate") or {}
    return {
        "rescue_stick_readonly_build_emulation_all_status": final.get("rescue_stick_readonly_build_final_gate_status", "blocked"),
        "steps": results,
        "no_real_build_execution": True,
        "readonly_emulated": True,
    }
