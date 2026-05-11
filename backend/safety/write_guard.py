"""
Hard-Stop / Write-Safety nur aus vorhandenen Inspect-Daten (keine neuen Scans, keine Schreibaktion).
"""

from __future__ import annotations

from typing import Any

_LINUX_FS = frozenset({"ext2", "ext3", "ext4", "xfs", "btrfs"})
_EFI_LIKE = frozenset({"vfat", "fat32"})

_WARNING_REASONS = frozenset({"SAFETY_WINDOWS_DETECTED", "SAFETY_DUALBOOT"})


def _walk_disk_nodes(disk: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    def visit(n: dict[str, Any]) -> None:
        if isinstance(n, dict):
            out.append(n)
            for p in n.get("partitions") or []:
                if isinstance(p, dict):
                    visit(p)

    visit(disk)
    return out


def _find_disk_node(classified: list[Any], device: str) -> dict[str, Any] | None:
    for d in classified:
        if isinstance(d, dict) and d.get("device") == device and d.get("type") == "disk":
            return d
    return None


def _find_raw_disk(devices_raw: list[Any], device: str) -> dict[str, Any] | None:
    for d in devices_raw:
        if isinstance(d, dict) and d.get("device") == device:
            return d
    return None


def _leaf_partitions(disk_node: dict[str, Any]) -> list[dict[str, Any]]:
    """Partitionen mit eigenem device-Pfad (type part)."""
    leaves: list[dict[str, Any]] = []
    for n in _walk_disk_nodes(disk_node):
        if not isinstance(n, dict):
            continue
        if n.get("type") == "part" and n.get("device"):
            leaves.append(n)
    return leaves


def _result(
    *,
    allowed: bool,
    reason_code: str,
    risk_level: str,
    requires_confirmation: bool,
    requires_override: bool,
) -> dict[str, Any]:
    return {
        "allowed": allowed,
        "reason_code": reason_code,
        "risk_level": risk_level,
        "requires_confirmation": requires_confirmation,
        "requires_override": requires_override,
    }


def evaluate_write_target(device: str, inspect_result: dict[str, Any]) -> dict[str, Any]:
    """
    Bewertet ein Top-Level-Blockgerät (type=disk) für hypothetische Schreiboperationen.
    Defensiv: im Zweifel blockieren.
    """
    storage = inspect_result.get("storage")
    storage = storage if isinstance(storage, dict) else {}
    classified = storage.get("devices_classified")
    classified_list = classified if isinstance(classified, list) else []

    disk = _find_disk_node(classified_list, device)
    if disk is None:
        return _result(
            allowed=False,
            reason_code="SAFETY_UNKNOWN_DEVICE",
            risk_level="high",
            requires_confirmation=True,
            requires_override=True,
        )

    nodes = _walk_disk_nodes(disk)
    cats = [n.get("category") for n in nodes if isinstance(n, dict)]
    mountability = storage.get("mountability")
    mount_rows = mountability if isinstance(mountability, list) else []

    detected = inspect_result.get("filesystems", {}).get("detected")
    detected = detected if isinstance(detected, dict) else {}

    devices_paths: list[str] = []
    for n in nodes:
        if isinstance(n, dict):
            dev = n.get("device")
            if isinstance(dev, str) and dev.startswith("/dev/"):
                devices_paths.append(dev)

    types_set: set[str] = set()
    for dp in devices_paths:
        meta = detected.get(dp)
        if isinstance(meta, dict):
            t = meta.get("type")
            if isinstance(t, str) and t.strip():
                types_set.add(t.strip().lower())

    for row in mount_rows:
        if not isinstance(row, dict):
            continue
        if row.get("mountpoint") == "/" and row.get("device") in devices_paths:
            return _result(
                allowed=False,
                reason_code="SAFETY_SYSTEM_DISK",
                risk_level="high",
                requires_confirmation=True,
                requires_override=True,
            )

    has_ntfs = "ntfs" in types_set
    has_linux_fs = bool(types_set & _LINUX_FS)

    # --- Hard stop: System- oder Live-Medium ---
    if "system_disk" in cats:
        return _result(
            allowed=False,
            reason_code="SAFETY_SYSTEM_DISK",
            risk_level="high",
            requires_confirmation=True,
            requires_override=True,
        )
    if "live_system" in cats:
        return _result(
            allowed=False,
            reason_code="SAFETY_LIVE_SYSTEM",
            risk_level="high",
            requires_confirmation=True,
            requires_override=True,
        )

    leaves = _leaf_partitions(disk)
    leaf_cats = [p.get("category") for p in leaves if isinstance(p, dict)]

    # Dualboot-Muster auf demselben Gerät (NTFS + Linux-FS)
    if has_ntfs and has_linux_fs:
        return _result(
            allowed=False,
            reason_code="SAFETY_DUALBOOT",
            risk_level="high",
            requires_confirmation=True,
            requires_override=True,
        )

    # Explizite Backup-Kandidaten auf allen Partitionen -> erlaubt
    if leaves and all(c == "backup_candidate" for c in leaf_cats):
        return _result(
            allowed=True,
            reason_code="SAFETY_BACKUP_TARGET_OK",
            risk_level="low",
            requires_confirmation=False,
            requires_override=False,
        )

    # NTFS-only / NTFS+EFI-ähnlich ohne Linux-FS: kein automatisches OK (Datenträger kann Windows sein)
    if has_ntfs and not has_linux_fs:
        rest = types_set - {"ntfs"} - _EFI_LIKE
        if not rest:
            return _result(
                allowed=False,
                reason_code="SAFETY_WINDOWS_DETECTED",
                risk_level="medium",
                requires_confirmation=True,
                requires_override=True,
            )

    # Leere / unpartitionierte Platte (Rohdaten)
    raw_disk = _find_raw_disk(storage.get("devices_raw") or [], device)
    if raw_disk and isinstance(raw_disk.get("partitions"), list) and len(raw_disk["partitions"]) == 0:
        return _result(
            allowed=True,
            reason_code="SAFETY_EMPTY_DISK",
            risk_level="low",
            requires_confirmation=True,
            requires_override=False,
        )

    # Keine blkid-Typen und nur unknown-Kategorien -> leer/unbestimmt behandeln
    if not types_set and leaves and all(c == "unknown" for c in leaf_cats):
        return _result(
            allowed=True,
            reason_code="SAFETY_EMPTY_DISK",
            risk_level="low",
            requires_confirmation=True,
            requires_override=False,
        )

    # Teilweise unklar oder gemischte Kategorien ohne klares Backup-Muster
    if "unknown" in cats or ("backup_candidate" in cats and "unknown" in cats):
        return _result(
            allowed=False,
            reason_code="SAFETY_UNKNOWN_DEVICE",
            risk_level="high",
            requires_confirmation=True,
            requires_override=True,
        )

    return _result(
        allowed=False,
        reason_code="SAFETY_UNKNOWN_DEVICE",
        risk_level="high",
        requires_confirmation=True,
        requires_override=True,
    )


def _target_state(ev: dict[str, Any]) -> str:
    if ev.get("allowed") is True:
        return "allowed"
    rc = str(ev.get("reason_code") or "")
    if rc in _WARNING_REASONS:
        return "warning"
    return "blocked"


def build_write_safety_summary(inspect_result: dict[str, Any]) -> dict[str, Any]:
    """Aggregiert alle Top-Level-Disks; nur lesend."""
    storage = inspect_result.get("storage")
    storage = storage if isinstance(storage, dict) else {}
    classified = storage.get("devices_classified")
    classified_list = classified if isinstance(classified, list) else []

    targets: list[dict[str, Any]] = []
    for node in classified_list:
        if not isinstance(node, dict):
            continue
        if node.get("type") != "disk":
            continue
        dev = node.get("device")
        if not isinstance(dev, str):
            continue
        ev = evaluate_write_target(dev, inspect_result)
        targets.append(
            {
                "device": dev,
                "size": node.get("size"),
                "classification": _target_state(ev),
                "write_allowed": bool(ev.get("allowed")),
                "reason_code": ev.get("reason_code"),
                "risk_level": ev.get("risk_level"),
                "requires_confirmation": ev.get("requires_confirmation"),
                "requires_override": ev.get("requires_override"),
            }
        )

    return {"policy_code": "safety.summary.v1", "targets": targets}
