"""
Core storage facade — read-only inventory for Live and Rescue.

Bundles existing parsers (storage_detection, safe_device adapters). No mounts, no writes.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any, Callable

from modules.storage_detection import classify_devices, detect_block_devices, detect_filesystems

Runner = Callable[..., subprocess.CompletedProcess[str]] | None

_FACADE_VERSION = 1
_SOURCE_MODULES = (
    "modules.storage_detection",
    "core.storage_facade",
)


def _empty_envelope(*, status: str = "blocked") -> dict[str, Any]:
    return {
        "status": status,
        "devices": [],
        "mounts": [],
        "backup_target_candidates": [],
        "restore_target_candidates": [],
        "warnings": [],
        "errors": [],
        "source_modules": list(_SOURCE_MODULES),
        "facade_version": _FACADE_VERSION,
    }


def _walk_lsblk_flat(node: dict[str, Any], out: list[dict[str, Any]]) -> None:
    if not isinstance(node, dict):
        return
    name = node.get("name") or node.get("NAME")
    if name:
        out.append(
            {
                "name": name,
                "type": node.get("type") or node.get("TYPE"),
                "fstype": node.get("fstype") or node.get("FSTYPE"),
                "label": node.get("label") or node.get("LABEL"),
                "uuid": node.get("uuid") or node.get("UUID"),
                "mountpoint": node.get("mountpoint") or node.get("MOUNTPOINT"),
                "size": node.get("size") or node.get("SIZE"),
                "model": node.get("model") or node.get("MODEL"),
                "tran": node.get("tran") or node.get("TRAN"),
            }
        )
    for ch in node.get("children") or []:
        if isinstance(ch, dict):
            _walk_lsblk_flat(ch, out)


def _run_lsblk_rescue_rows(*, runner: Runner = None) -> tuple[list[dict[str, Any]], str, list[str]]:
    """Single subprocess lsblk site for rescue-style flat rows (legacy handoff compat)."""
    warnings: list[str] = []
    raw = ""
    rows: list[dict[str, Any]] = []
    run = runner or subprocess.run
    try:
        proc = run(
            ["lsblk", "-J", "-o", "NAME,TYPE,FSTYPE,LABEL,UUID,MOUNTPOINT,SIZE,MODEL,TRAN"],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        raw = (proc.stdout or "")[:800_000]
        if proc.returncode == 0 and raw.strip():
            tree = json.loads(raw)
            for dev in tree.get("blockdevices") or []:
                if isinstance(dev, dict):
                    _walk_lsblk_flat(dev, rows)
        else:
            warnings.append("STORAGE_FACADE_LSBLK_NONZERO_OR_EMPTY")
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        warnings.append(f"STORAGE_FACADE_LSBLK_FAILED:{type(exc).__name__}")
    return rows, raw, warnings


def _run_blkid_excerpt(*, runner: Runner = None) -> tuple[str, list[str]]:
    warnings: list[str] = []
    run = runner or subprocess.run
    try:
        proc = run(["blkid"], capture_output=True, text=True, timeout=30, check=False)
        return (proc.stdout or "")[:400_000], warnings
    except (OSError, subprocess.TimeoutExpired):
        warnings.append("STORAGE_FACADE_BLKID_FAILED")
        return "", warnings


def classify_storage_devices(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Rescue-compatible classification flags + uuid conflict detection."""
    flags = {
        "nvme": False,
        "sata": False,
        "usb": False,
        "sd": False,
        "efi_system_partition": False,
        "linux_fs": False,
        "ntfs": False,
        "btrfs": False,
        "xfs": False,
        "crypto_luks": False,
        "backup_candidate": False,
        "system_disk_candidate": False,
    }
    uuids: list[str] = []
    for r in rows:
        name = str(r.get("name") or "").lower()
        tran = str(r.get("tran") or "").lower()
        fst = str(r.get("fstype") or "").lower()
        partlabel = str(r.get("label") or "").lower()
        u = str(r.get("uuid") or "").strip()
        if u:
            uuids.append(u)
        if "nvme" in name:
            flags["nvme"] = True
        if tran == "usb":
            flags["usb"] = True
        if name.startswith("sd") and tran != "usb":
            flags["sata"] = True
        if name.startswith("mmc"):
            flags["sd"] = True
        if fst == "vfat" and ("efi" in partlabel or "esp" in partlabel):
            flags["efi_system_partition"] = True
        if fst in ("ext2", "ext3", "ext4", "xfs", "btrfs"):
            flags["linux_fs"] = True
        if fst == "ntfs":
            flags["ntfs"] = True
        if fst == "btrfs":
            flags["btrfs"] = True
        if fst == "xfs":
            flags["xfs"] = True
        if "crypto" in fst or "luks" in fst:
            flags["crypto_luks"] = True
        if "backup" in partlabel or "setuphelfer" in partlabel:
            flags["backup_candidate"] = True
        if r.get("mountpoint") in ("/", "/boot", "/efi"):
            flags["system_disk_candidate"] = True

    uuid_counts: dict[str, int] = {}
    for u in uuids:
        uuid_counts[u] = uuid_counts.get(u, 0) + 1
    uuid_conflicts = [u for u, c in uuid_counts.items() if c > 1 and u]
    return {"flags": flags, "uuid_conflicts": uuid_conflicts, "row_count": len(rows)}


def build_storage_inventory_snapshot(
    *,
    runner: Runner = None,
    mode: str = "rescue",
    include_tree_devices: bool = True,
) -> dict[str, Any]:
    """
    Read-only storage inventory. ``mode`` is metadata only (live|rescue); same parsers.
    """
    out = _empty_envelope(status="ok")
    errors: list[str] = []
    warnings: list[str] = []

    devices_tree: list[dict[str, Any]] = []
    if include_tree_devices:
        try:
            devices_tree = detect_block_devices(runner=runner)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"STORAGE_FACADE_DETECT_DEVICES:{type(exc).__name__}")

    flat_rows, lsblk_excerpt, lsblk_warn = _run_lsblk_rescue_rows(runner=runner)
    warnings.extend(lsblk_warn)

    blkid_map: dict[str, dict[str, str]] = {}
    blkid_excerpt = ""
    try:
        blkid_map = detect_filesystems(runner=runner)
        blkid_excerpt, blk_warn = _run_blkid_excerpt(runner=runner)
        warnings.extend(blk_warn)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"STORAGE_FACADE_BLKID:{type(exc).__name__}")

    classified_tree = classify_devices(devices_tree) if devices_tree else []
    classification = classify_storage_devices(flat_rows)

    out["devices"] = classified_tree
    out["lsblk_rows"] = flat_rows[:500]
    out["blkid_by_device"] = blkid_map
    out["classification"] = classification
    out["lsblk_excerpt"] = lsblk_excerpt[:20_000]
    out["blkid_excerpt"] = blkid_excerpt[:20_000]
    out["mode"] = mode
    out["warnings"] = list(dict.fromkeys(warnings))
    out["errors"] = errors

    if classification.get("uuid_conflicts"):
        out["status"] = "review_required"
    elif not flat_rows and not devices_tree:
        out["status"] = "review_required"
        out["warnings"].append("STORAGE_FACADE_NO_DEVICES")
    elif errors:
        out["status"] = "blocked"

    out["backup_target_candidates"] = find_candidate_backup_targets(out)
    out["restore_target_candidates"] = find_candidate_restore_targets(out)
    return out


def find_candidate_backup_targets(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """External/removable backup targets from flat rows + tree categories."""
    candidates: list[dict[str, Any]] = []
    cls = snapshot.get("classification") if isinstance(snapshot.get("classification"), dict) else {}
    flags = cls.get("flags") if isinstance(cls.get("flags"), dict) else {}

    for r in snapshot.get("lsblk_rows") or []:
        if not isinstance(r, dict):
            continue
        fst = str(r.get("fstype") or "").lower()
        tran = str(r.get("tran") or "").lower()
        label = str(r.get("label") or "").lower()
        if fst not in ("ext4", "xfs", "ntfs", "btrfs") and "backup" not in label:
            continue
        if tran == "usb" or flags.get("backup_candidate") or "setuphelfer" in label or "backup" in label:
            candidates.append(
                {
                    "device_hint": str(r.get("name") or ""),
                    "fstype": fst,
                    "transport": tran,
                    "label": r.get("label"),
                    "role": "backup_target",
                    "readonly_analysis": True,
                }
            )
    return candidates[:40]


def find_candidate_restore_targets(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Internal/source candidates for restore preview (read-only classification)."""
    candidates: list[dict[str, Any]] = []
    for r in snapshot.get("lsblk_rows") or []:
        if not isinstance(r, dict):
            continue
        mp = r.get("mountpoint")
        fst = str(r.get("fstype") or "").lower()
        if mp in ("/", "/boot", "/efi") or (fst.startswith("ext") and mp):
            candidates.append(
                {
                    "device_hint": str(r.get("name") or ""),
                    "mountpoint": mp,
                    "fstype": fst,
                    "role": "restore_source_candidate",
                    "readonly_analysis": True,
                }
            )
    return candidates[:40]
