"""
Rescue Phase 2B: Ziel-Laufwerk / Zielpfad für Restore-Simulation bewerten (nur lesend).
"""

from __future__ import annotations

import os
import tarfile
from pathlib import Path
from typing import Any, Callable

from core.block_device_allowlist import is_allowed_block_device
from core.rescue_allowlist import path_under_prefixes, RESCUE_DRYRUN_WRITE_PREFIXES
from modules.inspect_storage import (
    detect_uuid_conflicts,
    list_physical_disks,
    read_partition_table,
    smart_classify_disk,
)
Runner = Callable[..., Any] | None


def _estimate_tar_uncompressed_bytes(archive_path: Path, *, cap_members: int = 500_000) -> int | None:
    try:
        total = 0
        n = 0
        with tarfile.open(archive_path, "r:*") as tf:
            for m in tf.getmembers():
                n += 1
                if n > cap_members:
                    return None
                if m.isfile():
                    total += m.size or 0
        return total
    except (OSError, tarfile.TarError):
        return None


def _block_device_size_bytes(dev: str, *, runner: Runner = None) -> int | None:
    from modules.inspect_storage import _run_capture

    r = _run_capture(["lsblk", "-n", "-b", "-o", "SIZE", "-p", dev], runner=runner, timeout=30)
    if r.returncode != 0:
        return None
    line = (r.stdout or "").strip().splitlines()
    if not line:
        return None
    try:
        return int(line[0].strip())
    except ValueError:
        return None


def assess_target_device(
    target_device: str | None,
    *,
    runner: Runner = None,
) -> dict[str, Any]:
    """
    Lesende Zielbewertung für Blockgerät (optional).

    Ohne ``target_device``: nur allgemeine System-Hinweise (UUID-Konflikte, Plattenliste).
    """
    out: dict[str, Any] = {
        "target_device": target_device,
        "device_allowed_whole_disk": False,
        "size_bytes": None,
        "partition_table_code": None,
        "smart_risk_code": None,
        "uuid_conflicts": False,
        "codes": [],
    }
    uuid_info = detect_uuid_conflicts(runner=runner)
    out["uuid_conflicts"] = bool(uuid_info.get("has_conflicts"))
    if uuid_info.get("has_conflicts"):
        out["codes"].append("rescue.target.duplicate_uuid_system")

    if not target_device or not str(target_device).strip():
        out["codes"].append("rescue.target.no_device_specified")
        return out

    dev = str(target_device).strip()
    out["device_allowed_whole_disk"] = is_allowed_block_device(dev)
    if not out["device_allowed_whole_disk"]:
        out["codes"].append("rescue.target.device_not_whole_disk_allowlist")

    sz = _block_device_size_bytes(dev, runner=runner)
    out["size_bytes"] = sz

    pt = read_partition_table(dev, runner=runner)
    out["partition_table_code"] = pt.get("code")
    if pt.get("code") == "rescue.storage.partition_table_unreadable":
        out["codes"].append("rescue.target.partition_table_unreadable")

    disks = list_physical_disks(runner=runner)
    sm_code = None
    if dev in disks:
        sm = smart_classify_disk(dev, runner=runner)
        sm_code = str(sm.get("risk_code") or "")
        out["smart_risk_code"] = sm_code
        if sm_code == "rescue.smart.critical":
            out["codes"].append("rescue.target.smart_critical")
        elif sm_code in ("rescue.smart.warning", "rescue.smart.command_failed"):
            out["codes"].append("rescue.target.smart_warning")

    return out


def compare_backup_to_target(
    archive_path: str | Path,
    target_assessment: dict[str, Any],
    *,
    runner: Runner = None,
) -> dict[str, Any]:
    """Kapazitätsabgleich Archiv-Inhalt vs. Zielblockgerät (heuristisch)."""
    p = Path(archive_path)
    if not (target_assessment.get("target_device") or "").strip():
        est0 = _estimate_tar_uncompressed_bytes(p)
        return {
            "backup_uncompressed_estimate_bytes": est0,
            "target_size_bytes": None,
            "capacity_ok": None,
            "codes": [],
            "skipped_no_target_device": True,
        }
    est = _estimate_tar_uncompressed_bytes(p)
    tgt = target_assessment.get("size_bytes")
    out: dict[str, Any] = {
        "backup_uncompressed_estimate_bytes": est,
        "target_size_bytes": tgt,
        "capacity_ok": None,
        "codes": [],
    }
    if est is None:
        out["codes"].append("rescue.target.backup_size_unknown")
        out["capacity_ok"] = None
        return out
    if tgt is None:
        out["codes"].append("rescue.target.size_unknown")
        out["capacity_ok"] = None
        return out
    margin = max(256 * 1024 * 1024, tgt // 20)
    if est + margin > tgt:
        out["capacity_ok"] = False
        out["codes"].append("rescue.target.capacity_insufficient")
    else:
        out["capacity_ok"] = True
        out["codes"].append("rescue.target.capacity_ok")
    return out


def detect_restore_blockers(
    backup_assessment: dict[str, Any],
    target_compare: dict[str, Any],
    target_assessment: dict[str, Any],
) -> list[str]:
    """Flache Code-Liste technischer Blocker / Risiken."""
    blockers: list[str] = []
    bc = backup_assessment.get("backup_class")
    if bc not in ("BACKUP_OK",):
        blockers.append(f"rescue.blocker.backup_{bc}")
    for c in backup_assessment.get("codes") or []:
        if c not in ("rescue.backup.ok",):
            blockers.append(c)
    if target_compare.get("capacity_ok") is False:
        blockers.append("rescue.blocker.capacity")
    for c in target_assessment.get("codes") or []:
        if c in (
            "rescue.target.smart_critical",
            "rescue.target.partition_table_unreadable",
            "rescue.target.duplicate_uuid_system",
        ):
            blockers.append(c)
    return sorted(set(blockers))


def recommend_new_target_disk(
    target_compare: dict[str, Any],
    target_assessment: dict[str, Any],
) -> str | None:
    """Empfehlungscode oder None."""
    if target_compare.get("capacity_ok") is False:
        return "rescue.decision.recommend_new_target_disk"
    if "rescue.target.smart_critical" in (target_assessment.get("codes") or []):
        return "rescue.decision.recommend_new_target_disk"
    return None


def assess_preview_directory(
    preview_dir: Path,
    *,
    runner: Runner = None,
) -> dict[str, Any]:
    """Freier Speicherplatz für Sandbox-Extract (Ziel ist Verzeichnis, kein Blockgerät)."""
    out: dict[str, Any] = {
        "preview_dir": str(preview_dir),
        "free_bytes": None,
        "under_allowlist": path_under_prefixes(preview_dir, RESCUE_DRYRUN_WRITE_PREFIXES),
        "codes": [],
    }
    if not out["under_allowlist"]:
        out["codes"].append("rescue.target.preview_not_allowlisted")
        return out
    try:
        parent = preview_dir.parent if preview_dir.is_dir() else preview_dir
        if not parent.is_dir():
            parent.mkdir(parents=True, exist_ok=True)
        usage = os.statvfs(str(parent))
        out["free_bytes"] = usage.f_bavail * usage.f_frsize
    except OSError:
        out["codes"].append("rescue.target.preview_statvfs_failed")
    return out


def compare_backup_to_preview_dir(
    archive_path: str | Path,
    preview_assessment: dict[str, Any],
) -> dict[str, Any]:
    p = Path(archive_path)
    est = _estimate_tar_uncompressed_bytes(p)
    free = preview_assessment.get("free_bytes")
    out: dict[str, Any] = {
        "backup_uncompressed_estimate_bytes": est,
        "preview_free_bytes": free,
        "capacity_ok": None,
        "codes": [],
    }
    if est is None or free is None:
        out["capacity_ok"] = None
        out["codes"].append("rescue.target.preview_capacity_unknown")
        return out
    margin = max(64 * 1024 * 1024, free // 10)
    if est + margin > free:
        out["capacity_ok"] = False
        out["codes"].append("rescue.target.preview_space_insufficient")
    else:
        out["capacity_ok"] = True
        out["codes"].append("rescue.target.preview_space_ok")
    return out


__all__ = [
    "assess_preview_directory",
    "assess_target_device",
    "compare_backup_to_preview_dir",
    "compare_backup_to_target",
    "detect_restore_blockers",
    "recommend_new_target_disk",
]
