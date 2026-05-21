"""
Core mount facade — read-only mount inventory and plans. No mount/umount execution.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Any, Callable

Runner = Callable[..., subprocess.CompletedProcess[str]] | None

_FACADE_VERSION = 1
_SOURCE_MODULES = ("core.mount_facade", "core.safe_device (resolve_mount_source_for_path)")

_FORBIDDEN_HOST_MOUNTS = frozenset({"/", "/boot", "/efi"})
_ALLOWED_PLAN_FSTYPES = frozenset({"vfat", "ext4", "ntfs", "btrfs", "xfs"})


def _empty_envelope(*, status: str = "blocked") -> dict[str, Any]:
    return {
        "status": status,
        "current_mounts": [],
        "readonly_mount_plan": {},
        "blocked_reasons": [],
        "warnings": [],
        "errors": [],
        "source_modules": list(_SOURCE_MODULES),
        "facade_version": _FACADE_VERSION,
    }


def _flatten_findmnt_nodes(nodes: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(nodes, list):
        return out
    for n in nodes:
        if not isinstance(n, dict):
            continue
        out.append(n)
        ch = n.get("children")
        if isinstance(ch, list):
            out.extend(_flatten_findmnt_nodes(ch))
    return out


def _run_findmnt_json(*, target: str, recursive: bool, runner: Runner) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    run = runner or subprocess.run
    args = ["findmnt", "-J"]
    if recursive:
        args.extend(["-R", target])
    else:
        args.extend(["-T", target])
    try:
        proc = run(args, capture_output=True, text=True, timeout=30, check=False)
        if proc.returncode != 0:
            warnings.append(f"MOUNT_FACADE_FINDMNT_RC_{proc.returncode}")
            return [], warnings
        data = json.loads(proc.stdout or "{}")
        fss = data.get("filesystems")
        return _flatten_findmnt_nodes(fss), warnings
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        warnings.append(f"MOUNT_FACADE_FINDMNT_FAILED:{type(exc).__name__}")
        return [], warnings


def build_mount_inventory_snapshot(*, runner: Runner = None, target: str = "/") -> dict[str, Any]:
    """Read-only findmnt inventory (recursive from target)."""
    out = _empty_envelope(status="ok")
    mounts, warnings = _run_findmnt_json(target=target, recursive=True, runner=runner)
    out["current_mounts"] = mounts
    out["warnings"] = list(dict.fromkeys(warnings))
    if not mounts:
        out["status"] = "review_required"
        out["warnings"].append("MOUNT_FACADE_NO_MOUNTS")
    safety = classify_mount_safety(mounts)
    out["mount_safety"] = safety
    if safety.get("blocked"):
        out["status"] = "blocked"
        out["blocked_reasons"] = list(safety.get("blocked_reasons") or [])
    return out


def classify_mount_safety(mounts: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify mount entries; no side effects."""
    blocked_reasons: list[str] = []
    warnings: list[str] = []
    for m in mounts:
        if not isinstance(m, dict):
            continue
        tgt = str(m.get("target") or "").rstrip("/") or "/"
        opts = str(m.get("options") or "").lower()
        fst = str(m.get("fstype") or "").lower()
        if tgt in _FORBIDDEN_HOST_MOUNTS:
            blocked_reasons.append(f"MOUNT_FACADE_HOST_ROOT:{tgt}")
        if "rw" in opts.split(",") and "ro" not in opts.split(","):
            if tgt in _FORBIDDEN_HOST_MOUNTS:
                blocked_reasons.append(f"MOUNT_FACADE_RW_ON_SYSTEM:{tgt}")
        if fst == "squashfs":
            warnings.append("MOUNT_FACADE_LIVE_SQUASHFS")
    return {
        "blocked": bool(blocked_reasons),
        "blocked_reasons": blocked_reasons,
        "warnings": warnings,
    }


def plan_readonly_source_mount(
    storage_snapshot: dict[str, Any],
    *,
    mount_root_prefix: str = "build/rescue/runtime-mounts/",
    max_operations: int = 12,
) -> dict[str, Any]:
    """
    Plan-only readonly mount operations for rescue workspace paths.
    Does not execute mount/umount.
    """
    tentative: list[dict[str, Any]] = []
    rows = storage_snapshot.get("lsblk_rows") if isinstance(storage_snapshot.get("lsblk_rows"), list) else []
    for r in rows[:40]:
        if not isinstance(r, dict):
            continue
        fst = str(r.get("fstype") or "").lower()
        if fst in _ALLOWED_PLAN_FSTYPES and r.get("name"):
            safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(r.get("name")))
            mp = f"{mount_root_prefix.rstrip('/')}/{safe}"
            tentative.append(
                {
                    "device_hint": str(r.get("name")),
                    "filesystem": fst,
                    "mountpoint": mp,
                    "read_only": True,
                    "purpose": "inspect_readonly",
                    "execution": "plan_only",
                }
            )
    return {
        "schema_version": 1,
        "strict_mode": "rescue_readonly_mount_plan_only",
        "mount_root_prefix": mount_root_prefix,
        "planned_operations": tentative[:max_operations],
        "forbidden": ["rw", "remount,rw", "mount", "/", "/boot", "/efi"],
        "cleanup_policy": "unmount_and_rmdir_after_validation_session",
    }


def validate_no_untracked_mount_change(
    baseline_mounts: list[dict[str, Any]],
    current_mounts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Detect new mount targets vs baseline (analysis only)."""

    def _keys(mounts: list[dict[str, Any]]) -> set[str]:
        keys: set[str] = set()
        for m in mounts:
            if isinstance(m, dict):
                tgt = str(m.get("target") or "").strip()
                src = str(m.get("source") or "").strip()
                if tgt:
                    keys.add(f"{src}|{tgt}")
        return keys

    base = _keys(baseline_mounts)
    cur = _keys(current_mounts)
    added = sorted(cur - base)
    removed = sorted(base - cur)
    untracked = bool(added)
    return {
        "untracked_mount_change": untracked,
        "added_mount_keys": added,
        "removed_mount_keys": removed,
        "status": "blocked" if untracked else "ok",
    }
