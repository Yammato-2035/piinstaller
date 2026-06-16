"""
Read-only Speicher-Inspektion für Rescue-/Diagnosemodus.

Nutzt bestehende Hilfen aus ``storage_detection`` (lsblk/blkid), ohne
Zielsystem-Laufwerke schreibend zu mounten. Automatisches Mounten entfällt
bewusst (Phase 1); nur bereits gemountete Geräte werden über findmnt
bezüglich RO/RW klassifiziert.
"""

from __future__ import annotations

import os
import re
import subprocess
from collections import defaultdict
from typing import Any, Callable, Mapping, Sequence

Runner = Callable[..., subprocess.CompletedProcess[str]]


def _run_capture(
    argv: list[str],
    *,
    runner: Runner | None = None,
    timeout: int = 90,
) -> subprocess.CompletedProcess[str]:
    run = runner or subprocess.run
    try:
        return run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError as e:
        # CI-Runner kann Tools wie smartctl fehlen lassen.
        # Einheitlicher Fallback: nicht über Exception abbrechen, sondern als "command not available"
        # weiter verarbeiten (smart_classify_disk prüft Text/returncode).
        return subprocess.CompletedProcess(argv, 127, stdout="", stderr=str(e))


def _flatten_block_nodes(nodes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        parts = n.get("partitions") or []
        if isinstance(parts, list) and parts:
            out.extend(_flatten_block_nodes([p for p in parts if isinstance(p, dict)]))
        dev = n.get("device")
        if isinstance(dev, str) and dev.startswith("/dev/"):
            row = {k: v for k, v in n.items() if k != "partitions"}
            out.append(row)
    return out


def _parent_disk(devpath: str, *, runner: Runner | None = None) -> str:
    """Liefert die Basis-Blockdevice-URL für Partitionstabellen (delegiert storage_facade)."""
    from core.storage_facade import get_parent_block_device

    parent = get_parent_block_device(devpath, runner=runner)
    return parent or devpath


def list_block_devices(*, runner: Runner | None = None) -> list[dict[str, Any]]:
    """Klassifizierte Blockbaum-Struktur (delegiert storage_facade)."""
    from core.storage_facade import list_classified_block_devices_for_inspect

    return list_classified_block_devices_for_inspect(runner=runner)


def detect_filesystems(*, runner: Runner | None = None) -> dict[str, dict[str, str]]:
    """blkid-basiert, nur lesen (delegiert storage_facade)."""
    from core.storage_facade import detect_filesystems_for_inspect

    return detect_filesystems_for_inspect(runner=runner)


def check_mountability(*, read_only: bool = True, runner: Runner | None = None) -> list[dict[str, Any]]:
    """
    Pro Blockgerät: Mount-Status und effektive Optionen (nur lesend).

    Unbekannte/unmounted Geräte: kein automatisches Mounten — ``mountable`` ist
    dann ``unknown`` (Policy Phase 1).
    """
    _ = read_only  # reserviert für spätere explizite RO-Test-Mounts
    from core.storage_facade import list_classified_block_devices_for_inspect

    devices = list_classified_block_devices_for_inspect(runner=runner)
    flat = _flatten_block_nodes(devices)
    rows: list[dict[str, Any]] = []
    for node in flat:
        dev = node.get("device")
        if not isinstance(dev, str) or not dev.startswith("/dev/"):
            continue
        from core.mount_facade import get_findmnt_json_by_source, is_block_device_mounted

        mounted = is_block_device_mounted(dev, runner=runner)
        entry: dict[str, Any] = {
            "device": dev,
            "mounted": mounted,
            "mountpoint": None,
            "fstype": node.get("fstype"),
            "options": None,
            "readonly_effective": None,
            "mountable": "unknown",
            "policy_code": "rescue.storage.unmounted_no_auto_mount",
        }
        if not mounted:
            rows.append(entry)
            continue
        data = get_findmnt_json_by_source(dev, runner=runner)
        if data is None:
            entry["mountable"] = "unknown"
            entry["policy_code"] = "rescue.storage.findmnt_json_invalid"
            rows.append(entry)
            continue
        fss = data.get("filesystems")
        if not isinstance(fss, list) or not fss:
            rows.append(entry)
            continue
        fs0 = fss[0]
        if isinstance(fs0, dict):
            entry["mountpoint"] = fs0.get("target")
            entry["fstype"] = entry["fstype"] or fs0.get("fstype")
            opts = fs0.get("options")
            if isinstance(opts, str):
                entry["options"] = opts
                parts = {p.strip() for p in opts.split(",") if p.strip()}
                ro = "ro" in parts and "rw" not in parts
                entry["readonly_effective"] = bool(ro)
                entry["mountable"] = "ok"
                entry["policy_code"] = "rescue.storage.mounted_inspected"
        rows.append(entry)
    return rows


def read_partition_table(device: str, *, runner: Runner | None = None) -> dict[str, Any]:
    """
    Partitionstabelle des zugehörigen Datenträgers (nur lesende Werkzeuge).

    Bevorzugt ``sfdisk --dump``; fallback ``fdisk -l``.
    """
    disk = _parent_disk(device, runner=runner)
    out: dict[str, Any] = {"disk": disk, "source": None, "text": "", "ok": False, "code": None}
    r = _run_capture(["sfdisk", "--dump", disk], runner=runner, timeout=60)
    if r.returncode == 0 and (r.stdout or "").strip():
        out["source"] = "sfdisk"
        out["text"] = r.stdout or ""
        out["ok"] = True
        out["code"] = "rescue.storage.partition_table_ok"
        return out
    r2 = _run_capture(["fdisk", "-l", disk], runner=runner, timeout=60)
    if r2.returncode == 0 and (r2.stdout or "").strip():
        out["source"] = "fdisk"
        out["text"] = r2.stdout or ""
        out["ok"] = True
        out["code"] = "rescue.storage.partition_table_ok_fdisk"
        return out
    out["code"] = "rescue.storage.partition_table_unreadable"
    out["text"] = (r.stderr or r.stdout or "").strip()
    return out


def detect_uuid_conflicts(*, runner: Runner | None = None) -> dict[str, Any]:
    """Erkennt doppelte UUIDs laut blkid (Lesen)."""
    fsmap = detect_filesystems(runner=runner)
    uuid_index: dict[str, list[str]] = defaultdict(list)
    for dev, meta in fsmap.items():
        u = meta.get("uuid")
        if u:
            uuid_index[u].append(dev)
    conflicts = {u: devs for u, devs in uuid_index.items() if len(devs) > 1}
    return {
        "conflicts": conflicts,
        "has_conflicts": bool(conflicts),
    }


def smart_classify_disk(disk_dev: str, *, runner: Runner | None = None) -> dict[str, Any]:
    """
    SMART-Gesundheit per ``smartctl -H`` (nur lesen). Ohne smartctl: code not_available.
    """
    row: dict[str, Any] = {
        "device": disk_dev,
        "state": "UNKNOWN",
        "risk_code": "rescue.smart.not_available",
        "raw": None,
    }
    if not disk_dev.startswith("/dev/"):
        row["risk_code"] = "rescue.smart.invalid_device"
        return row
    r = _run_capture(["smartctl", "-H", disk_dev], runner=runner, timeout=45)
    text = (r.stdout or "") + "\n" + (r.stderr or "")
    row["raw"] = text.strip()[:4000] if text.strip() else None
    if r.returncode != 0 and ("smartctl: command not found" in text or "No such file" in text):
        row["risk_code"] = "rescue.smart.not_available"
        return row
    if r.returncode != 0:
        row["risk_code"] = "rescue.smart.command_failed"
        return row
    upper = text.upper()
    if "PASSED" in upper or "OK" in upper:
        row["state"] = "OK"
        row["risk_code"] = "rescue.smart.ok"
        return row
    if "FAILED" in upper:
        row["state"] = "FAILED"
        row["risk_code"] = "rescue.smart.critical"
        return row
    if any(x in upper for x in ("WARNING", "CAUTION", "UNKNOWN")):
        row["state"] = "WARNING"
        row["risk_code"] = "rescue.smart.warning"
        return row
    row["state"] = "UNKNOWN"
    row["risk_code"] = "rescue.smart.warning"
    return row


def list_physical_disks(*, runner: Runner | None = None) -> list[str]:
    """Nur Top-Level-Disk-Geräte (TYPE=disk) für SMART."""
    from core.storage_facade import list_physical_disk_paths

    return list_physical_disk_paths(runner=runner, mode="rescue")


def readonly_fs_check(device: str, fstype: str | None, *, runner: Runner | None = None) -> dict[str, Any]:
    """
    ext4: ``fsck -n`` ; xfs: ``xfs_repair -n`` — nur wenn Gerät nicht gemountet.

    Gemountete Ziele werden übersprungen (Code skipped_mounted).
    """
    fst = (fstype or "").lower()
    res: dict[str, Any] = {"device": device, "fstype": fst or None, "skipped": False, "code": None, "detail": None}
    from core.mount_facade import is_block_device_mounted

    if is_block_device_mounted(device, runner=runner):
        res["skipped"] = True
        res["code"] = "rescue.fs.skipped_mounted"
        return res
    if fst == "ext4" or fst == "ext3" or fst == "ext2":
        r = _run_capture(["fsck", "-n", device], runner=runner, timeout=300)
        out = (r.stdout or "") + (r.stderr or "")
        res["detail"] = out.strip()[:8000]
        if r.returncode == 0:
            res["code"] = "rescue.fs.fsck_ok"
        elif r.returncode in (1, 2):
            res["code"] = "rescue.fs.fsck_issues"
        else:
            res["code"] = "rescue.fs.fsck_error"
        return res
    if fst == "xfs":
        r = _run_capture(["xfs_repair", "-n", device], runner=runner, timeout=300)
        out = (r.stdout or "") + (r.stderr or "")
        res["detail"] = out.strip()[:8000]
        if r.returncode == 0:
            res["code"] = "rescue.fs.xfs_repair_ok"
        elif "will make changes" in out.lower() or "would" in out.lower():
            res["code"] = "rescue.fs.xfs_repair_issues"
        else:
            res["code"] = "rescue.fs.xfs_repair_error" if r.returncode != 0 else "rescue.fs.xfs_repair_ok"
        return res
    res["code"] = "rescue.fs.unsupported_or_unknown_fstype"
    return res


__all__ = [
    "check_mountability",
    "detect_filesystems",
    "detect_uuid_conflicts",
    "list_block_devices",
    "list_physical_disks",
    "read_partition_table",
    "readonly_fs_check",
    "smart_classify_disk",
]
