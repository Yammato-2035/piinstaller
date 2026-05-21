"""
Rescue boot context — read-only environment classification (no mounts, no writes).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from core.install_paths import get_opt_install_dir
from deploy.runner_rescue_io import REPO_ROOT

_SOURCE_MODULES = (
    "rescue.boot_context",
    "core.mount_facade",
    "core.storage_facade",
)

_LIVE_FSTYPES = frozenset({"squashfs", "overlay", "iso9660", "aufs"})
_FORBIDDEN_WRITE_ROOTS = ("/", "/boot", "/efi", "/boot/efi")
_ALLOWED_WRITE_ROOTS = ("/media", "/run/media", "build/rescue/runtime-mounts/")


def _tri_bool(value: bool | None) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "unknown"


def _hints_from_mount_snapshot(mount_snapshot: dict[str, Any] | None) -> tuple[bool | None, bool | None, list[str]]:
    warnings: list[str] = []
    live: bool | None = None
    rescue: bool | None = None
    if not isinstance(mount_snapshot, dict):
        return live, rescue, warnings
    mounts = mount_snapshot.get("current_mounts")
    if not isinstance(mounts, list):
        return live, rescue, warnings
    for m in mounts:
        if not isinstance(m, dict):
            continue
        fst = str(m.get("fstype") or "").lower()
        tgt = str(m.get("target") or "")
        if fst in _LIVE_FSTYPES:
            live = True
        if tgt == "/" and fst in ("ext4", "xfs", "btrfs"):
            rescue = rescue is False if rescue is not None else False
    if live is True and rescue is None:
        rescue = False
    return live, rescue, warnings


def _hints_from_env() -> tuple[bool | None, bool | None, list[str]]:
    warnings: list[str] = []
    rescue: bool | None = None
    live: bool | None = None
    rm = (os.environ.get("SETUPHELFER_RESCUE_MODE") or "").strip().lower()
    if rm in ("1", "true", "yes", "on"):
        rescue = True
    elif rm in ("0", "false", "no", "off"):
        rescue = False
    live_env = (os.environ.get("SETUPHELFER_LIVE_SYSTEM") or "").strip().lower()
    if live_env in ("1", "true", "yes"):
        live = True
    elif live_env in ("0", "false", "no"):
        live = False
    if rescue is True and live is None:
        live = False
    return live, rescue, warnings


def _read_os_release_live_hint() -> bool | None:
    try:
        text = Path("/etc/os-release").read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return None
    if "debian-live" in text or "live-boot" in text or "live system" in text:
        return True
    return None


def build_rescue_boot_context(
    *,
    source_root: str | None = None,
    storage_snapshot_ref: str | None = None,
    mount_snapshot_ref: str | None = None,
    storage_snapshot: dict[str, Any] | None = None,
    mount_snapshot: dict[str, Any] | None = None,
    rescue_mode_hint: bool | None = None,
    live_system_hint: bool | None = None,
    network_available_hint: bool | None = None,
    ui_mode_hint: str | None = None,
) -> dict[str, Any]:
    """
    Classify runtime context for rescue orchestration. Does not mount or mutate devices.
    """
    warnings: list[str] = []
    errors: list[str] = []

    live_hint = live_system_hint
    rescue_hint = rescue_mode_hint
    env_live, env_rescue, env_warn = _hints_from_env()
    warnings.extend(env_warn)
    if live_hint is None:
        live_hint = env_live
    if rescue_hint is None:
        rescue_hint = env_rescue

    m_live, m_rescue, m_warn = _hints_from_mount_snapshot(mount_snapshot)
    warnings.extend(m_warn)
    if live_hint is None:
        live_hint = m_live
    if rescue_hint is None:
        rescue_hint = m_rescue

    if live_hint is None:
        os_live = _read_os_release_live_hint()
        if os_live is True:
            live_hint = True
            warnings.append("BOOT_CONTEXT_OS_RELEASE_LIVE_HINT")

    if rescue_hint is None and live_hint is True:
        rescue_hint = False
    if rescue_hint is None and live_hint is False:
        rescue_hint = True

    src = (source_root or os.environ.get("SETUPHELFER_RESCUE_SOURCE_ROOT") or "").strip()
    if not src:
        src = "/mnt/setuphelfer-source"
        warnings.append("BOOT_CONTEXT_SOURCE_ROOT_DEFAULT_PLANNED")

    try:
        runtime_root = str(get_opt_install_dir())
    except OSError:
        runtime_root = "/opt/setuphelfer"

    evidence_root = str((REPO_ROOT / "docs" / "evidence" / "runtime-results").resolve())

    ui_mode = (ui_mode_hint or "").strip().lower() or "unknown"
    if ui_mode == "unknown":
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            ui_mode = "web"
        else:
            ui_mode = "headless"

    net = network_available_hint
    if net is None:
        try:
            net = any(p.is_dir() for p in Path("/sys/class/net").iterdir() if p.name != "lo")
        except OSError:
            net = None

    boot_context = {
        "live_system": _tri_bool(live_hint),
        "rescue_mode": _tri_bool(rescue_hint),
        "source_root": src,
        "runtime_root": runtime_root,
        "evidence_root": evidence_root,
        "ui_mode": ui_mode,
        "network_available": _tri_bool(net),
        "allowed_write_roots": list(_ALLOWED_WRITE_ROOTS),
        "forbidden_write_roots": list(_FORBIDDEN_WRITE_ROOTS),
        "storage_snapshot_ref": storage_snapshot_ref,
        "mount_snapshot_ref": mount_snapshot_ref,
    }

    status = "ok"
    if live_hint is True and rescue_hint is True:
        status = "review_required"
        warnings.append("BOOT_CONTEXT_LIVE_AND_RESCUE_CONFLICT")
    if rescue_hint is False and live_hint is False:
        status = "review_required"
        warnings.append("BOOT_CONTEXT_MODE_UNCLEAR")

    return {
        "status": status,
        "boot_context": boot_context,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": errors,
        "source_modules": list(_SOURCE_MODULES),
    }
