"""
Core mount facade — read-only mount inventory and plans. No mount/umount execution.

Phase A.1 (Facade Freeze): ``build_readonly_mount_plan`` and ``validate_*`` are the
canonical public surface for mount planning and safety checks (plan-only).
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable

Runner = Callable[..., subprocess.CompletedProcess[str]] | None


def _run_subprocess(
    cmd: list[str],
    *,
    runner: Runner = None,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    run = runner or subprocess.run
    try:
        return run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except TypeError:
        return run(cmd, timeout=timeout)  # type: ignore[misc,call-arg]


_FACADE_VERSION = 1
FACADE_CONTRACT_VERSION = 1
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


@dataclass(frozen=True)
class ReadonlyMountPlan:
    """Public contract: plan-only readonly mount operations (no execution)."""

    mount_root_prefix: str
    planned_operations: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    schema_version: int = 1
    strict_mode: str = "rescue_readonly_mount_plan_only"
    facade_version: int = FACADE_CONTRACT_VERSION


def build_readonly_mount_plan(
    storage_snapshot: dict[str, Any],
    *,
    mount_root_prefix: str = "build/rescue/runtime-mounts/",
    max_operations: int = 12,
) -> ReadonlyMountPlan:
    """
    Canonical entry: readonly mount plan (plan-only). Wraps ``plan_readonly_source_mount``.
    """
    raw = plan_readonly_source_mount(
        storage_snapshot,
        mount_root_prefix=mount_root_prefix,
        max_operations=max_operations,
    )
    ops = tuple(raw.get("planned_operations") or [])
    return ReadonlyMountPlan(
        mount_root_prefix=str(raw.get("mount_root_prefix") or mount_root_prefix),
        planned_operations=ops,
        schema_version=int(raw.get("schema_version") or 1),
        strict_mode=str(raw.get("strict_mode") or "rescue_readonly_mount_plan_only"),
    )


def validate_mount_readonly(mount_entry: dict[str, Any]) -> dict[str, Any]:
    """
    Validate a single mount entry is readonly-safe (analysis only, no remount).
    """
    if not isinstance(mount_entry, dict):
        return {
            "valid": False,
            "reason_code": "MOUNT_FACADE_INVALID_ENTRY",
            "facade_version": FACADE_CONTRACT_VERSION,
        }
    opts = str(mount_entry.get("options") or "").lower().split(",")
    tgt = str(mount_entry.get("target") or mount_entry.get("mountpoint") or "").rstrip("/") or "/"
    read_only = mount_entry.get("read_only") is True or "ro" in opts
    blocked = tgt in _FORBIDDEN_HOST_MOUNTS and not read_only
    return {
        "valid": read_only and not blocked,
        "read_only": read_only,
        "target": tgt,
        "reason_code": "MOUNT_FACADE_HOST_RW" if blocked else ("MOUNT_FACADE_OK" if read_only else "MOUNT_FACADE_NOT_READONLY"),
        "facade_version": FACADE_CONTRACT_VERSION,
    }


def validate_source_not_target(*, source: str, target: str) -> dict[str, Any]:
    """Ensure backup/restore source and target paths/devices do not alias."""
    s = str(source).strip().rstrip("/")
    t = str(target).strip().rstrip("/")
    same = bool(s and t and (s == t or s.startswith(t + "/") or t.startswith(s + "/")))
    return {
        "valid": not same,
        "source": s,
        "target": t,
        "reason_code": "MOUNT_FACADE_SOURCE_IS_TARGET" if same else "MOUNT_FACADE_SOURCE_TARGET_OK",
        "facade_version": FACADE_CONTRACT_VERSION,
    }


def validate_not_live_root(mountpoint: str) -> dict[str, Any]:
    """Block plans that would mount or write on live system root paths."""
    mp = str(mountpoint).rstrip("/") or "/"
    blocked = mp in _FORBIDDEN_HOST_MOUNTS
    return {
        "valid": not blocked,
        "mountpoint": mp,
        "reason_code": "MOUNT_FACADE_LIVE_ROOT" if blocked else "MOUNT_FACADE_NOT_LIVE_ROOT",
        "facade_version": FACADE_CONTRACT_VERSION,
    }


def get_mount_source_for_path(path: str, *, runner: Runner = None) -> str | None:
    """
    Canonical entry: findmnt SOURCE for ``path`` (read-only).

    Rescue restore modules use this instead of direct findmnt subprocess calls.
    """
    run = runner or subprocess.run
    target = str(path).strip() or "/"
    try:
        try:
            proc = run(
                ["findmnt", "-n", "-o", "SOURCE", "-T", target],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except TypeError:
            proc = run(["findmnt", "-n", "-o", "SOURCE", "-T", target], timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    lines = (proc.stdout or "").strip().splitlines()
    return lines[0].strip() if lines else None


def is_block_device_mounted(device: str, *, runner: Runner = None) -> bool:
    """True when ``findmnt -S device`` reports an active mount (read-only)."""
    dev = str(device).strip()
    if not dev.startswith("/dev/"):
        return False
    try:
        proc = _run_subprocess(["findmnt", "-n", "-S", dev], runner=runner, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0 and bool((proc.stdout or "").strip())


def get_findmnt_json_by_source(device: str, *, runner: Runner = None) -> dict[str, Any] | None:
    """Parse ``findmnt -J -S device`` or None when unmounted / invalid."""
    dev = str(device).strip()
    if not dev.startswith("/dev/"):
        return None
    try:
        proc = _run_subprocess(["findmnt", "-J", "-S", dev], runner=runner, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0 or not (proc.stdout or "").strip():
        return None
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
