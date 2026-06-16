"""
Core storage facade — read-only inventory for Live and Rescue.

Bundles existing parsers (storage_detection, safe_device adapters). No mounts, no writes.

Phase A.1 (Facade Freeze): ``FACADE_CONTRACT_*`` types and ``get_*`` entry points are the
canonical public surface. Legacy helpers remain for backward compatibility; new modules
must use the contract API only (see docs/architecture/CORE_FACADE_RULES.md).
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Literal

from core.storage_discovery import discover_block_devices, discover_filesystems
from modules.storage_detection import classify_devices

Runner = Callable[..., subprocess.CompletedProcess[str]] | None


def _run_subprocess(
    cmd: list[str],
    *,
    runner: Runner = None,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    """Support both ``subprocess.run``-style and legacy ``runner(cmd, timeout=…)`` callables."""
    run = runner or subprocess.run
    try:
        return run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except TypeError:
        return run(cmd, timeout=timeout)  # type: ignore[misc,call-arg]


_FACADE_VERSION = 1
FACADE_CONTRACT_VERSION = 1
_SOURCE_MODULES = (
    "modules.storage_detection",
    "core.storage_facade",
)


class StorageTargetRole(str, Enum):
    """Canonical target roles for facade consumers (maps to domain vocabulary)."""

    BACKUP_TARGET = "backup_target"
    RESTORE_SOURCE = "restore_source"
    SYSTEM_DISK = "system_disk"
    EXTERNAL_DATA = "external_data"
    RESCUE_STICK = "rescue_stick"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class BlockDeviceInfo:
    """Public contract: block device row (read-only inventory)."""

    name: str
    device_path: str
    fstype: str | None = None
    label: str | None = None
    uuid: str | None = None
    mountpoint: str | None = None
    size: str | None = None
    model: str | None = None
    transport: str | None = None
    device_type: str | None = None


@dataclass(frozen=True)
class MountInfo:
    """Public contract: mount entry (read-only; sourced via mount_facade delegation)."""

    source: str
    target: str
    fstype: str | None = None
    options: str | None = None


@dataclass(frozen=True)
class StorageTargetClassification:
    """Public contract: classification result for a path or device hint."""

    path_or_device: str
    role: StorageTargetRole
    confidence: Literal["high", "medium", "low"] = "low"
    external: bool = False
    write_allowed: bool = False
    evidence: tuple[str, ...] = field(default_factory=tuple)
    facade_version: int = FACADE_CONTRACT_VERSION


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
            devices_tree = discover_block_devices(runner=runner)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"STORAGE_FACADE_DETECT_DEVICES:{type(exc).__name__}")

    flat_rows, lsblk_excerpt, lsblk_warn = _run_lsblk_rescue_rows(runner=runner)
    warnings.extend(lsblk_warn)

    blkid_map: dict[str, dict[str, str]] = {}
    blkid_excerpt = ""
    try:
        blkid_map = discover_filesystems(runner=runner)
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


def _row_to_block_device(row: dict[str, Any]) -> BlockDeviceInfo:
    name = str(row.get("name") or "")
    dev_path = name if name.startswith("/dev/") else f"/dev/{name}" if name else ""
    return BlockDeviceInfo(
        name=name,
        device_path=dev_path,
        fstype=row.get("fstype"),
        label=row.get("label"),
        uuid=row.get("uuid"),
        mountpoint=row.get("mountpoint"),
        size=row.get("size"),
        model=row.get("model"),
        transport=row.get("tran") or row.get("transport"),
        device_type=row.get("type"),
    )


def get_block_devices(*, runner: Runner = None, mode: str = "live") -> list[BlockDeviceInfo]:
    """
    Canonical entry: block devices (read-only). Delegates to ``build_storage_inventory_snapshot``.
    """
    snap = build_storage_inventory_snapshot(runner=runner, mode=mode)
    rows = snap.get("lsblk_rows") or []
    return [_row_to_block_device(r) for r in rows if isinstance(r, dict)]


def get_mounts(*, runner: Runner = None, target: str = "/") -> list[MountInfo]:
    """
    Canonical entry: mount inventory (read-only). Delegates to ``core.mount_facade``.
    """
    from core.mount_facade import build_mount_inventory_snapshot

    snap = build_mount_inventory_snapshot(runner=runner, target=target)
    out: list[MountInfo] = []
    for m in snap.get("current_mounts") or []:
        if not isinstance(m, dict):
            continue
        out.append(
            MountInfo(
                source=str(m.get("source") or ""),
                target=str(m.get("target") or ""),
                fstype=m.get("fstype"),
                options=m.get("options"),
            )
        )
    return out


def get_mount_for_path(path: str, *, runner: Runner = None) -> MountInfo | None:
    """Best-effort longest-prefix match for ``path`` against current mounts."""
    normalized = str(path).rstrip("/") or "/"
    best: MountInfo | None = None
    best_len = -1
    for m in get_mounts(runner=runner):
        tgt = m.target.rstrip("/") or "/"
        if normalized == tgt or normalized.startswith(tgt + "/"):
            if len(tgt) > best_len:
                best_len = len(tgt)
                best = m
    return best


def classify_storage_target(path_or_device: str, *, runner: Runner = None) -> StorageTargetClassification:
    """
    Canonical entry: classify a path or device hint (read-only heuristics).
    Full role mapping migrates to ``storage_role_classification`` in a later phase.
    """
    hint = str(path_or_device).strip()
    snap = build_storage_inventory_snapshot(runner=runner, mode="live")
    rows = snap.get("lsblk_rows") or []
    norm = hint.rstrip("/")

    for r in rows:
        if not isinstance(r, dict):
            continue
        name = str(r.get("name") or "")
        dev = name if name.startswith("/dev/") else f"/dev/{name}"
        mp = str(r.get("mountpoint") or "")
        if hint in (name, dev, mp) or (mp and norm.startswith(mp.rstrip("/"))):
            label = str(r.get("label") or "").lower()
            tran = str(r.get("tran") or r.get("transport") or "").lower()
            mp_l = mp.lower()
            if mp in ("/", "/boot", "/efi"):
                return StorageTargetClassification(
                    path_or_device=hint,
                    role=StorageTargetRole.SYSTEM_DISK,
                    confidence="high",
                    external=False,
                    write_allowed=False,
                    evidence=("live_root_mount_detected",),
                )
            if tran == "usb" or "backup" in label or "/media/" in mp_l or "/run/media/" in mp_l:
                return StorageTargetClassification(
                    path_or_device=hint,
                    role=StorageTargetRole.BACKUP_TARGET,
                    confidence="medium",
                    external=True,
                    write_allowed=False,
                    evidence=("external_usb_or_backup_hint",),
                )
            return StorageTargetClassification(
                path_or_device=hint,
                role=StorageTargetRole.EXTERNAL_DATA,
                confidence="low",
                external=tran == "usb",
                write_allowed=False,
                evidence=("storage_facade_heuristic",),
            )

    return StorageTargetClassification(
        path_or_device=hint,
        role=StorageTargetRole.UNKNOWN,
        confidence="low",
        external=False,
        write_allowed=False,
        evidence=("no_matching_inventory_row",),
    )


def is_external_target(path_or_device: str, *, runner: Runner = None) -> bool:
    """True when classification marks target as external (USB/removable heuristic)."""
    return classify_storage_target(path_or_device, runner=runner).external


def get_parent_block_device(device_path: str, *, runner: Runner = None) -> str | None:
    """
    Canonical entry: resolve whole-disk path for a partition (lsblk PKNAME, read-only).

    Used by Rescue restore hard-stops and gate checks instead of direct lsblk calls.
    """
    dev = str(device_path).strip()
    if not dev:
        return None
    if not dev.startswith("/dev/"):
        dev = f"/dev/{dev}"
    run = runner or subprocess.run
    try:
        proc = _run_subprocess(
            ["lsblk", "-n", "-o", "PKNAME", "-p", dev],
            runner=runner,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return dev if dev.startswith("/dev/") else None
    pk = (proc.stdout or "").strip()
    if proc.returncode == 0 and pk.startswith("/dev/"):
        return pk
    return dev if dev.startswith("/dev/") else None


def get_block_device_size_bytes(device_path: str, *, runner: Runner = None) -> int | None:
    """Canonical entry: block device size in bytes (read-only lsblk SIZE)."""
    dev = str(device_path).strip()
    if not dev.startswith("/dev/"):
        dev = f"/dev/{dev}" if dev else ""
    if not dev:
        return None
    try:
        proc = _run_subprocess(
            ["lsblk", "-n", "-b", "-o", "SIZE", "-p", dev],
            runner=runner,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    line = (proc.stdout or "").strip().splitlines()
    if not line:
        return None
    try:
        return int(line[0].strip())
    except ValueError:
        return None


def list_disk_blockdevice_nodes(*, runner: Runner = None, mode: str = "live") -> list[dict[str, Any]]:
    """Top-level ``disk`` nodes from storage inventory (USB operator selection, diagnostics)."""
    snap = build_storage_inventory_snapshot(runner=runner, mode=mode, include_tree_devices=True)
    tree = snap.get("lsblk_tree") or []
    out: list[dict[str, Any]] = []
    for node in tree:
        if isinstance(node, dict) and node.get("type") == "disk":
            out.append(node)
    if out:
        return out
    for row in snap.get("lsblk_rows") or []:
        if isinstance(row, dict) and row.get("type") == "disk":
            out.append(row)
    return out


def get_lsblk_field(device_path: str, field: str, *, runner: Runner = None) -> str:
    """Single-field lsblk probe (read-only). Prefer inventory helpers when possible."""
    dev = str(device_path).strip()
    if not dev.startswith("/dev/"):
        dev = f"/dev/{dev}" if dev else ""
    if not dev or not str(field).strip():
        return ""
    try:
        proc = _run_subprocess(
            ["lsblk", "-no", str(field).strip(), dev],
            runner=runner,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    text = (proc.stdout or "").strip()
    return text.splitlines()[0].strip() if text else ""


def get_device_label(device_path: str, *, runner: Runner = None) -> str | None:
    """Volume/filesystem label via blkid LABEL (read-only)."""
    for cmd in (
        ["sudo", "blkid", "-p", "-s", "LABEL", "-o", "value", str(device_path)],
        ["blkid", "-p", "-s", "LABEL", "-o", "value", str(device_path)],
        ["blkid", "-o", "value", "-s", "LABEL", str(device_path)],
    ):
        try:
            proc = _run_subprocess(cmd, runner=runner, timeout=15)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if proc.returncode == 0 and (proc.stdout or "").strip():
            return (proc.stdout or "").strip()
    fallback = get_lsblk_field(device_path, "LABEL", runner=runner)
    return fallback or None


def get_root_block_parent(*, runner: Runner = None) -> str | None:
    """Whole-disk parent of the running root filesystem (Rescue gate)."""
    from core.mount_facade import get_mount_source_for_path

    src = get_mount_source_for_path("/", runner=runner)
    if not src or not src.startswith("/dev/"):
        return None
    return get_parent_block_device(src, runner=runner)


def probe_block_device_identity(device_path: str, *, runner: Runner = None) -> dict[str, Any] | None:
    """
    Single-device lsblk JSON node for Rescue identity (read-only).

    Returns the parsed blockdevice dict or None when lsblk fails.
    """
    dev = str(device_path).strip()
    if not dev.startswith("/dev/"):
        return None
    try:
        proc = _run_subprocess(
            [
                "lsblk",
                "-J",
                "-o",
                "PATH,SIZE,TYPE,MODEL,SERIAL,TRAN,UUID,PARTUUID,PKNAME,FSTYPE",
                "-p",
                dev,
            ],
            runner=runner,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0 or not (proc.stdout or "").strip():
        return None
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return None
    bds = data.get("blockdevices")
    if not isinstance(bds, list) or len(bds) != 1:
        return None
    node = bds[0]
    return node if isinstance(node, dict) else None


def get_partition_uuid(partition_path: str, *, runner: Runner = None) -> str | None:
    """Canonical blkid UUID lookup for a partition path (read-only)."""
    return get_device_uuid(partition_path, runner=runner)


def get_device_uuid(device_path: str, *, runner: Runner = None) -> str | None:
    """Canonical blkid UUID lookup (read-only)."""
    run = runner or subprocess.run
    try:
        proc = run(
            ["blkid", "-o", "value", "-s", "UUID", str(device_path)],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode == 0 and (proc.stdout or "").strip():
        return (proc.stdout or "").strip()
    return None


def get_filesystem_type(device_path: str, *, runner: Runner = None) -> str | None:
    """Filesystem type from inventory blkid map or detect_filesystems delegation."""
    dev = str(device_path).strip()
    try:
        fs_map = discover_filesystems(runner=runner)
        meta = fs_map.get(dev) if isinstance(fs_map, dict) else None
        if isinstance(meta, dict):
            fst = meta.get("type") or meta.get("fstype")
            if fst:
                return str(fst)
    except Exception:  # noqa: BLE001
        pass
    snap = build_storage_inventory_snapshot(runner=runner, mode="live", include_tree_devices=False)
    blk = snap.get("blkid_by_device") if isinstance(snap.get("blkid_by_device"), dict) else {}
    meta = blk.get(dev)
    if isinstance(meta, dict):
        fst = meta.get("type") or meta.get("fstype")
        return str(fst) if fst else None
    return None


def list_classified_devices(*, runner: Runner = None) -> list[Any]:
    """Classified block devices for discovery UIs (delegates safe_device)."""
    from core.safe_device import list_classified_devices as _list

    return _list(runner=runner)


def detect_block_devices_for_inspect(*, runner: Runner = None) -> list[dict[str, Any]]:
    """Inspect collector: raw block device tree (delegates storage_detection)."""
    return discover_block_devices(runner=runner)


def detect_filesystems_for_inspect(*, runner: Runner = None) -> dict[str, dict[str, str]]:
    """Inspect collector: blkid map (delegates storage_detection)."""
    return discover_filesystems(runner=runner)


def classify_devices_for_inspect(devices_raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Inspect collector: classified device tree (delegates storage_detection)."""
    return classify_devices(devices_raw)


def list_classified_block_devices_for_inspect(*, runner: Runner = None) -> list[dict[str, Any]]:
    """Classified block device tree for Rescue inspect (facade-only lsblk path)."""
    raw = detect_block_devices_for_inspect(runner=runner)
    return classify_devices_for_inspect(raw)


def list_physical_disk_paths(*, runner: Runner = None, mode: str = "rescue") -> list[str]:
    """Top-level disk device paths (``/dev/...``) for SMART and target assessment."""
    out: list[str] = []
    for node in list_disk_blockdevice_nodes(runner=runner, mode=mode):
        if not isinstance(node, dict):
            continue
        d = node.get("device") or node.get("path")
        if not d:
            name = node.get("name")
            if isinstance(name, str):
                d = name if name.startswith("/dev/") else f"/dev/{name}"
        if isinstance(d, str) and d.startswith("/dev/"):
            out.append(d)
    if out:
        return out
    for node in list_classified_block_devices_for_inspect(runner=runner):
        if not isinstance(node, dict):
            continue
        if (node.get("type") or "").lower() != "disk":
            continue
        d = node.get("device")
        if isinstance(d, str) and d.startswith("/dev/"):
            out.append(d)
    return out


def get_readonly_storage_probe_contract() -> dict[str, Any]:
    """Public-safe metadata for deploy-runner handoffs (no shell execution)."""
    return {
        "facade_contract_version": FACADE_CONTRACT_VERSION,
        "storage_inventory": "core.storage_facade.build_storage_inventory_snapshot",
        "classified_devices": "core.storage_facade.list_classified_block_devices_for_inspect",
        "physical_disks": "core.storage_facade.list_physical_disk_paths",
        "mount_inventory": "core.mount_facade.build_mount_inventory_snapshot",
        "mounts_flat": "core.mount_facade.discover_mounts_flat",
        "implementation_note": "lsblk/blkid/findmnt only inside core facades",
    }


def collect_inspect_storage_bundle(*, runner: Runner = None) -> dict[str, Any]:
    """
    Read-only storage bundle for inspect/collector (no mountability/uuid conflicts).
    """
    source_modules: list[str] = []
    devices_raw: list[dict[str, Any]] = []
    devices_classified: list[dict[str, Any]] = []
    filesystems_map: dict[str, dict[str, str]] = {}

    try:
        devices_raw = detect_block_devices_for_inspect(runner=runner)
        source_modules.append("core.storage_facade.detect_block_devices_for_inspect")
    except Exception as exc:  # noqa: BLE001
        return {
            "devices_raw": [],
            "devices_classified": [],
            "filesystems_map": {},
            "source_modules": source_modules,
            "error": {"code": "inspect.storage.detect_block_devices_failed", "detail": type(exc).__name__},
        }

    try:
        devices_classified = classify_devices_for_inspect(devices_raw)
        source_modules.append("core.storage_facade.classify_devices_for_inspect")
    except Exception as exc:  # noqa: BLE001
        return {
            "devices_raw": devices_raw,
            "devices_classified": [],
            "filesystems_map": {},
            "source_modules": source_modules,
            "error": {"code": "inspect.storage.classify_devices_failed", "detail": type(exc).__name__},
        }

    try:
        filesystems_map = detect_filesystems_for_inspect(runner=runner)
        source_modules.append("core.storage_facade.detect_filesystems_for_inspect")
    except Exception as exc:  # noqa: BLE001
        return {
            "devices_raw": devices_raw,
            "devices_classified": devices_classified,
            "filesystems_map": {},
            "source_modules": source_modules,
            "error": {"code": "inspect.storage.detect_filesystems_failed", "detail": type(exc).__name__},
        }

    return {
        "devices_raw": devices_raw,
        "devices_classified": devices_classified,
        "filesystems_map": filesystems_map,
        "source_modules": source_modules,
        "error": None,
    }


def classify_device_from_existing_result(
    inspect_result: dict[str, Any],
    device: str,
) -> StorageTargetClassification:
    """Classify a device using an existing inspect payload (no new scan)."""
    storage = inspect_result.get("storage") if isinstance(inspect_result, dict) else {}
    storage = storage if isinstance(storage, dict) else {}
    classified = storage.get("devices_classified")
    rows = classified if isinstance(classified, list) else []
    hint = str(device).strip()

    def walk(nodes: list[Any]) -> StorageTargetClassification | None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            dev = str(node.get("device") or "")
            if dev == hint:
                cat = str(node.get("category") or "unknown")
                role = StorageTargetRole.UNKNOWN
                external = False
                if cat == "system_disk":
                    role = StorageTargetRole.SYSTEM_DISK
                elif cat == "backup_candidate":
                    role = StorageTargetRole.BACKUP_TARGET
                    external = True
                return StorageTargetClassification(
                    path_or_device=hint,
                    role=role,
                    confidence="medium",
                    external=external,
                    write_allowed=False,
                    evidence=(f"inspect_category:{cat}",),
                )
            parts = node.get("partitions")
            if isinstance(parts, list):
                hit = walk(parts)
                if hit is not None:
                    return hit
        return None

    hit = walk(rows)
    if hit is not None:
        return hit
    return classify_storage_target(hint, runner=None)


def normalize_legacy_storage_result(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy storage_detection/inspect dict keys for facade consumers."""
    if not isinstance(raw, dict):
        return {"facade_version": FACADE_CONTRACT_VERSION, "devices_raw": [], "devices_classified": []}
    storage = raw.get("storage") if isinstance(raw.get("storage"), dict) else raw
    filesystems = raw.get("filesystems") if isinstance(raw.get("filesystems"), dict) else {}
    return {
        "facade_version": FACADE_CONTRACT_VERSION,
        "devices_raw": storage.get("devices_raw") or raw.get("devices_raw") or [],
        "devices_classified": storage.get("devices_classified") or raw.get("devices_classified") or [],
        "filesystems_detected": filesystems.get("detected") or raw.get("blkid_by_device") or {},
        "lsblk_rows": raw.get("lsblk_rows") or [],
    }
