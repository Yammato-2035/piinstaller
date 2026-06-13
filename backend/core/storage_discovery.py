"""
Storage Discovery Canonical — single read-only owner for lsblk/findmnt/blkid discovery.

Phase P.1: delegates to ``modules.storage_detection`` and ``core.mount_facade``;
no new probe rules, no writes, no mounts.
"""

from __future__ import annotations

from typing import Any, Callable

import subprocess

from core.mount_facade import build_mount_inventory_snapshot
from modules.storage_detection import (
    classify_devices,
    detect_block_devices as _detect_block_devices,
    detect_filesystems as _detect_filesystems,
)

Runner = Callable[..., subprocess.CompletedProcess[str]] | None

STORAGE_DISCOVERY_VERSION = 1

_SOURCE_MODULES = (
    "modules.storage_detection",
    "core.mount_facade",
    "core.storage_discovery",
)


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
            "discover_filesystems",
            "discover_partitions",
            "discover_storage_roles",
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
