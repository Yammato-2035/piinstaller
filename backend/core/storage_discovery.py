"""
Storage Discovery Canonical — single read-only owner for lsblk/findmnt/blkid discovery.

Phase P.1: delegates to ``modules.storage_detection`` and ``core.mount_facade``;
no new probe rules, no writes, no mounts.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from typing import Any, Callable

from core.mount_facade import build_mount_inventory_snapshot
from modules.storage_detection import (
    classify_devices,
    detect_block_devices as _detect_block_devices,
    detect_filesystems as _detect_filesystems,
)

Runner = Callable[..., subprocess.CompletedProcess[str]] | None

STORAGE_DISCOVERY_VERSION = 1

_LSBLK_JSON_COLUMNS = "NAME,TYPE,PKNAME,LABEL,SIZE,FSTYPE,MOUNTPOINTS,RM,RO,MODEL,TRAN"
_LSBLK_JSON_COLUMNS_FALLBACK = "NAME,TYPE,PKNAME,LABEL,SIZE,FSTYPE,MOUNTPOINT,RM,RO,MODEL,TRAN"

_SOURCE_MODULES = (
    "modules.storage_detection",
    "core.mount_facade",
    "core.storage_discovery",
)


def _run_shell_capture(cmd: str, *, runner: Runner = None, timeout: int = 30) -> tuple[int, str]:
    if runner is not None:
        proc = runner(cmd.split(), capture_output=True, text=True, timeout=timeout, check=False)
        return proc.returncode, proc.stdout or ""
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, check=False)
    return proc.returncode, proc.stdout or ""


def discover_lsblk_json_tree(*, runner: Runner = None) -> dict[str, Any]:
    """Raw ``lsblk -J`` tree (legacy ``app._lsblk_tree`` shape)."""
    rc, raw = _run_shell_capture(
        f"lsblk -J -o {_LSBLK_JSON_COLUMNS} 2>/dev/null",
        runner=runner,
    )
    if rc != 0 or not raw.strip():
        rc2, raw2 = _run_shell_capture(
            f"lsblk -J -o {_LSBLK_JSON_COLUMNS_FALLBACK} 2>/dev/null",
            runner=runner,
        )
        raw = raw2 if rc2 == 0 else raw
    try:
        data = json.loads(raw or "{}")
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _flatten_findmnt_filesystems(nodes: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(nodes, list):
        return out
    for node in nodes:
        if not isinstance(node, dict):
            continue
        out.append(node)
        children = node.get("children")
        if isinstance(children, list):
            out.extend(_flatten_findmnt_filesystems(children))
    return out


def discover_findmnt_mounts_flat(*, runner: Runner = None) -> list[dict[str, Any]]:
    """Flat findmnt JSON list (legacy ``app._findmnt_mounts`` shape)."""
    rc, raw = _run_shell_capture("findmnt -J -o SOURCE,TARGET,FSTYPE,OPTIONS 2>/dev/null", runner=runner)
    if rc != 0:
        return []
    try:
        data = json.loads(raw or "{}")
        return _flatten_findmnt_filesystems(data.get("filesystems", []) or [])
    except json.JSONDecodeError:
        return []


def discover_device_fstype(
    device_path: str,
    *,
    runner: Runner = None,
    sudo_runner: Callable[[str], tuple[int, str]] | None = None,
) -> str:
    """Read-only blkid TYPE for a block device path (optional sudo_runner for elevated probe)."""
    dev = (device_path or "").strip()
    if not dev.startswith("/dev/"):
        return ""
    quoted = shlex.quote(dev)
    rc, out = _run_shell_capture(f"blkid -o value -s TYPE {quoted} 2>/dev/null", runner=runner, timeout=2)
    if rc == 0 and out.strip():
        return out.strip().lower()
    if sudo_runner is not None:
        src, sout = sudo_runner(f"blkid -o value -s TYPE {quoted} 2>/dev/null")
        if src == 0 and sout.strip():
            return sout.strip().lower()
    return ""


def _walk_lsblk_nodes(items: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]) -> dict[str, Any] | None:
    for node in items:
        if not isinstance(node, dict):
            continue
        if predicate(node):
            return node
        children = node.get("children")
        if isinstance(children, list):
            found = _walk_lsblk_nodes(children, predicate)
            if found is not None:
                return found
    return None


def discover_lsblk_node_by_mountpoint(mountpoint: str, *, runner: Runner = None) -> dict[str, Any] | None:
    """Find lsblk JSON node by mountpoint (legacy ``app._find_lsblk_by_mountpoint``)."""
    mp = (mountpoint or "").strip()
    if not mp:
        return None
    data = discover_lsblk_json_tree(runner=runner)
    devices = data.get("blockdevices", []) or []
    if not isinstance(devices, list):
        return None

    def _matches(node: dict[str, Any]) -> bool:
        node_mp = node.get("mountpoint")
        mps = node.get("mountpoints")
        if node_mp and node_mp == mp:
            return True
        return isinstance(mps, list) and mp in mps

    return _walk_lsblk_nodes(devices, _matches)


def discover_lsblk_node_by_name(dev_name: str, *, runner: Runner = None) -> dict[str, Any] | None:
    """Find lsblk JSON node by NAME (legacy ``app._find_lsblk_by_name``)."""
    name = (dev_name or "").strip()
    if name.startswith("/dev/"):
        name = name[5:]
    if not name:
        return None
    data = discover_lsblk_json_tree(runner=runner)
    devices = data.get("blockdevices", []) or []
    if not isinstance(devices, list):
        return None
    return _walk_lsblk_nodes(devices, lambda node: node.get("name") == name)


def discover_disk_by_name(name: str, *, runner: Runner = None) -> dict[str, Any] | None:
    """Top-level disk node by NAME (legacy ``app._find_disk_by_name``)."""
    disk_name = (name or "").strip()
    if not disk_name:
        return None
    data = discover_lsblk_json_tree(runner=runner)
    devices = data.get("blockdevices", []) or []
    if not isinstance(devices, list):
        return None
    for node in devices:
        if isinstance(node, dict) and node.get("name") == disk_name and node.get("type") == "disk":
            return node
    return None


def discover_mountpoints_for_disk(disk_dev: str, *, runner: Runner = None) -> list[str]:
    """All mountpoints for a disk device path including partitions (legacy ``app._mountpoints_for_disk``)."""
    disk = (disk_dev or "").strip()
    if not disk:
        return []
    mps: list[str] = []
    for fs in discover_findmnt_mounts_flat(runner=runner):
        src = (fs.get("source") or "").strip()
        tgt = (fs.get("target") or "").strip()
        if src and tgt and src.startswith(disk):
            mps.append(tgt)
    return sorted(set(mps), key=len, reverse=True)


def disk_has_system_mount(disk: dict[str, Any]) -> bool:
    """True when disk or children mount /, /boot, or /boot/firmware (legacy ``app._disk_is_system``)."""
    bad = {"/", "/boot", "/boot/firmware"}

    def _has_bad(node: dict[str, Any]) -> bool:
        mp = node.get("mountpoint")
        mps = node.get("mountpoints")
        if mp in bad:
            return True
        if isinstance(mps, list) and any(x in bad for x in mps):
            return True
        for child in node.get("children", []) or []:
            if isinstance(child, dict) and _has_bad(child):
                return True
        return False

    return _has_bad(disk) if isinstance(disk, dict) else False


def discover_block_devices(*, runner: Runner = None) -> list[dict[str, Any]]:
    """Canonical lsblk-backed block device tree."""
    return _detect_block_devices(runner=runner)


def discover_filesystems(*, runner: Runner = None) -> dict[str, dict[str, str]]:
    """Canonical blkid-backed filesystem map (device -> uuid/type)."""
    return _detect_filesystems(runner=runner)


def discover_mounts(*, runner: Runner = None, target: str = "/") -> list[dict[str, Any]]:
    """Canonical findmnt-backed mount list (flattened JSON nodes)."""
    snap = build_mount_inventory_snapshot(runner=runner, target=target)
    mounts = snap.get("current_mounts")
    return mounts if isinstance(mounts, list) else []


def discover_partitions(*, runner: Runner = None) -> list[dict[str, Any]]:
    """Partition nodes from canonical block device tree."""
    parts: list[dict[str, Any]] = []

    def _walk(node: dict[str, Any]) -> None:
        children = node.get("partitions")
        if isinstance(children, list):
            for ch in children:
                if isinstance(ch, dict):
                    parts.append(ch)
                    _walk(ch)

    for dev in discover_block_devices(runner=runner):
        if isinstance(dev, dict):
            _walk(dev)
    return parts


def discover_storage_roles(*, runner: Runner = None) -> list[dict[str, Any]]:
    """Classified device roles via storage_detection.classify_devices."""
    devices = discover_block_devices(runner=runner)
    classified = classify_devices(devices)
    return classified if isinstance(classified, list) else []


def build_storage_discovery_diagnostics() -> dict[str, Any]:
    return {
        "discovery_version": STORAGE_DISCOVERY_VERSION,
        "discovery_module": "core.storage_discovery",
        "source_modules": list(_SOURCE_MODULES),
        "public_functions": [
            "discover_block_devices",
            "discover_mounts",
            "discover_findmnt_mounts_flat",
            "discover_lsblk_json_tree",
            "discover_lsblk_node_by_mountpoint",
            "discover_lsblk_node_by_name",
            "discover_disk_by_name",
            "discover_mountpoints_for_disk",
            "discover_device_fstype",
            "discover_filesystems",
            "discover_partitions",
            "discover_storage_roles",
            "disk_has_system_mount",
            "build_storage_discovery_diagnostics",
        ],
        "canonical_commands": {
            "block_devices": "lsblk -J",
            "filesystems": "blkid",
            "mounts": "findmnt -J",
        },
        "read_only": True,
        "writes_allowed": False,
    }
