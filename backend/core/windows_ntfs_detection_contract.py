"""
Windows/NTFS read-only detection contract (Phase F.1).

Pure functions — no mounts, no writes, no password/BitLocker bypass.
Delegates disk role heuristics to storage_role_classification where applicable.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from core import storage_role_classification as src

CONTRACT_VERSION = "1.0.0"

_BITLOCKER_STATUSES = frozenset(
    {
        "unknown",
        "not_detected",
        "detected",
        "detected_key_available",
        "detected_key_missing",
    }
)


def redact_serial(value: str | None) -> str:
    """Return sha256 prefix for evidence; empty if missing."""
    if not value or not str(value).strip():
        return ""
    digest = hashlib.sha256(str(value).strip().encode("utf-8")).hexdigest()
    return f"sha256:{digest[:16]}"


def _norm_lines(text: str) -> list[str]:
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


def parse_blkid_rows(blkid_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in _norm_lines(blkid_text):
        if not line.startswith("/dev/"):
            continue
        dev, _, rest = line.partition(":")
        row: dict[str, str] = {"device": dev.strip()}
        for match in re.finditer(r'(\w+)="([^"]*)"', rest):
            row[match.group(1).lower()] = match.group(2)
        for match in re.finditer(r"(\w+)=([^\s]+)", rest):
            key = match.group(1).lower()
            if key not in row:
                row[key] = match.group(2)
        rows.append(row)
    return rows


def parse_findmnt_rows(findmnt_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in _norm_lines(findmnt_text):
        parts = line.split()
        if len(parts) < 3:
            continue
        rows.append(
            {
                "source": parts[0],
                "target": parts[1],
                "fstype": parts[2],
                "options": " ".join(parts[3:]) if len(parts) > 3 else "",
            }
        )
    return rows


def _partition_from_blkid_row(row: dict[str, str]) -> dict[str, Any]:
    dev = row.get("device", "")
    name = dev.replace("/dev/", "") if dev.startswith("/dev/") else dev
    return {
        "name": name,
        "fstype": (row.get("type") or "").lower(),
        "parttypename": (row.get("partlabel") or row.get("parttypename") or "").lower(),
        "label": row.get("label") or "",
        "uuid": row.get("uuid") or "",
        "partuuid": row.get("partuuid") or "",
        "mountpoint": "",
        "size_bytes": 0,
    }


def _group_partitions_by_disk(partitions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for p in partitions:
        name = str(p.get("name") or "")
        if not name:
            continue
        disk = name
        if name.startswith("nvme") and "p" in name:
            disk = name.rsplit("p", 1)[0]
        elif name[-1].isdigit():
            disk = re.sub(r"\d+$", "", name)
        grouped.setdefault(disk, []).append(p)
    return grouped


def detect_efi_system_partition(partitions: list[dict[str, Any]]) -> dict[str, Any]:
    hits = [p for p in partitions if src._is_efi_partition(p)]
    return {
        "detected": bool(hits),
        "partitions": [p.get("name") for p in hits],
        "count": len(hits),
    }


def detect_ntfs_partitions(partitions: list[dict[str, Any]]) -> dict[str, Any]:
    hits = [p for p in partitions if src._is_ntfs_partition(p)]
    return {
        "detected": bool(hits),
        "partitions": [p.get("name") for p in hits],
        "count": len(hits),
    }


def detect_windows_indicators(partitions: list[dict[str, Any]]) -> dict[str, Any]:
    ms_data = [p for p in partitions if src._is_microsoft_basic_data(p)]
    recovery = [p for p in partitions if src._is_windows_recovery(p)]
    ntfs = [p for p in partitions if src._is_ntfs_partition(p)]
    efi = [p for p in partitions if src._is_efi_partition(p)]
    indicators: list[str] = []
    if ntfs:
        indicators.append("ntfs_partitions")
    if efi:
        indicators.append("efi_partition")
    if ms_data:
        indicators.append("microsoft_basic_data")
    if recovery:
        indicators.append("windows_recovery")
    if len(ntfs) >= 2:
        indicators.append("multi_ntfs_layout")
    windows_detected = bool(
        (efi and ntfs and (ms_data or recovery or len(ntfs) >= 2))
        or (efi and ntfs and any(int(p.get("size_bytes") or 0) >= src._NTFS_LARGE_BYTES for p in ntfs))
    )
    return {
        "detected": windows_detected,
        "indicators": indicators,
        "ntfs_count": len(ntfs),
        "efi_count": len(efi),
    }


def detect_bitlocker_indicators(
    partitions: list[dict[str, Any]],
    blkid_rows: list[dict[str, str]] | None = None,
    *,
    recovery_key_documented: bool = False,
) -> dict[str, Any]:
    hints: list[str] = []
    for p in partitions:
        if src._is_bitlocker_hint(p):
            hints.append(str(p.get("name") or ""))
    if blkid_rows:
        for row in blkid_rows:
            typ = (row.get("type") or "").lower()
            label = (row.get("partlabel") or row.get("label") or "").lower()
            if typ == "bitlocker" or "bitlocker" in label:
                dev = row.get("device", "")
                hints.append(dev.replace("/dev/", ""))
    hints = sorted({h for h in hints if h})
    if hints:
        status = "detected_key_available" if recovery_key_documented else "detected_key_missing"
    else:
        status = "not_detected"
    return {
        "status": status,
        "partition_hints": hints,
        "file_access_without_key": False,
        "notes": (
            "BitLocker-Indikator erkannt — kein Dateizugriff ohne Recovery-Key."
            if hints
            else "Kein expliziter BitLocker-Typ in read-only blkid/Partitionen."
        ),
    }


def classify_windows_ntfs_layout(
    lsblk_json_or_rows: Any,
    blkid_rows: list[dict[str, str]] | list[str] | str,
    findmnt_rows: list[dict[str, str]] | list[str] | str | None = None,
    *,
    live_root_device: str | None = None,
    efi_boot_hints: list[str] | None = None,
) -> dict[str, Any]:
    """Classify layout from read-only probe data (structured or parsed text)."""
    partitions: list[dict[str, Any]] = []
    disks: list[dict[str, Any]] = []

    if isinstance(lsblk_json_or_rows, dict):
        # lsblk -J style
        for dev in lsblk_json_or_rows.get("blockdevices") or []:
            if not isinstance(dev, dict):
                continue
            parts = src._flatten_partitions([dev])
            partitions.extend(parts)
            disks.append({"name": dev.get("name"), "partitions": dev.get("children") or []})
    elif isinstance(lsblk_json_or_rows, list):
        if lsblk_json_or_rows and isinstance(lsblk_json_or_rows[0], dict):
            if lsblk_json_or_rows[0].get("type") == "disk":
                for dev in lsblk_json_or_rows:
                    parts = src._flatten_partitions([dev])
                    partitions.extend(parts)
                    disks.append(dev)
            else:
                partitions = list(lsblk_json_or_rows)
    elif isinstance(lsblk_json_or_rows, str):
        # fallback: derive from blkid only
        pass

    if isinstance(blkid_rows, str):
        parsed_blkid = parse_blkid_rows(blkid_rows)
    else:
        parsed_blkid = []
        for row in blkid_rows or []:
            if isinstance(row, str):
                parsed_blkid.extend(parse_blkid_rows(row))
            elif isinstance(row, dict):
                parsed_blkid.append(row)

    if not partitions and parsed_blkid:
        partitions = [_partition_from_blkid_row(r) for r in parsed_blkid]

    if isinstance(findmnt_rows, str):
        parsed_findmnt = parse_findmnt_rows(findmnt_rows)
    else:
        parsed_findmnt = list(findmnt_rows or [])

    for m in parsed_findmnt:
        src_dev = m.get("source", "")
        mp = m.get("target", "")
        for p in partitions:
            name = str(p.get("name") or "")
            if src_dev.endswith(name) or src_dev == f"/dev/{name}":
                p["mountpoint"] = mp

    if not live_root_device:
        for m in parsed_findmnt:
            if m.get("target") == "/":
                live_root_device = m.get("source")

    efi = detect_efi_system_partition(partitions)
    ntfs = detect_ntfs_partitions(partitions)
    windows = detect_windows_indicators(partitions)
    bitlocker = detect_bitlocker_indicators(partitions, parsed_blkid)

    if efi_boot_hints:
        for hint in efi_boot_hints:
            if "windows" in hint.lower() and "boot" in hint.lower():
                windows["indicators"].append("efi_windows_boot_manager")
                windows["detected"] = True

    disk_roles: list[dict[str, Any]] = []
    grouped = _group_partitions_by_disk(partitions)
    for disk_name, parts in grouped.items():
        disk_roles.append(
            src.classify_disk_storage_role(
                {"name": disk_name, "partitions": parts},
                live_root_device=live_root_device,
            )
        )

    source_candidates = [
        r["device"]
        for r in disk_roles
        if r.get("role") == "windows_system_disk" and r.get("confidence") in ("high", "medium")
    ]

    return {
        "contract_version": CONTRACT_VERSION,
        "windows_detected": windows["detected"],
        "efi_detected": efi["detected"],
        "ntfs_detected": ntfs["detected"],
        "bitlocker_status": bitlocker["status"],
        "windows_indicators": windows,
        "efi": efi,
        "ntfs": ntfs,
        "bitlocker": bitlocker,
        "disk_roles": disk_roles,
        "source_device_candidates": source_candidates,
        "live_root_device": live_root_device,
        "partition_count": len(partitions),
    }


def build_msi_windows_precheck_decision(
    classification: dict[str, Any],
    *,
    backup_target_candidates: list[dict[str, Any]] | None = None,
    operator_selected_source: str | None = None,
) -> dict[str, Any]:
    """F.1 decision envelope — backup/restore/write always false for execute."""
    warnings: list[str] = []
    errors: list[str] = []

    sources = list(classification.get("source_device_candidates") or [])
    if operator_selected_source:
        sources = [operator_selected_source]

    if not sources:
        status = "blocked"
        errors.append("no_windows_source_candidate")
    elif len(sources) > 1 and not operator_selected_source:
        status = "review_required"
        warnings.append("multiple_windows_source_candidates")
    else:
        status = "ok"

    bl = classification.get("bitlocker_status") or "unknown"
    if bl in ("detected", "detected_key_missing"):
        status = "review_required" if status == "ok" else status
        warnings.append("bitlocker_indicator_no_file_access_claim")

    targets = backup_target_candidates or []
    external_targets = [t for t in targets if t.get("external_confirmed") and t.get("role") == "backup_target_candidate"]
    image_backup_plan = status == "ok" and bool(external_targets)

    if classification.get("bitlocker_status") == "detected_key_missing":
        warnings.append("image_backup_may_be_raw_structure_only")

    return {
        "status": status,
        "windows_detected": bool(classification.get("windows_detected")),
        "efi_detected": bool(classification.get("efi_detected")),
        "ntfs_detected": bool(classification.get("ntfs_detected")),
        "bitlocker_status": bl,
        "source_device_candidates": sources,
        "backup_allowed": False,
        "restore_allowed": False,
        "write_allowed": False,
        "requires_operator_selection": len(sources) != 1 or not operator_selected_source,
        "image_backup_plan_allowed": image_backup_plan,
        "warnings": warnings,
        "errors": errors,
        "evidence": {
            "disk_roles": classification.get("disk_roles"),
            "windows_indicators": classification.get("windows_indicators"),
        },
    }


def capabilities_payload() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "mode": "read_only",
        "supported": {
            "windows_detect": True,
            "ntfs_detect": True,
            "efi_detect": True,
            "bitlocker_indicator_detect": True,
            "image_backup_execute": False,
            "restore_execute": False,
            "wipe": False,
            "password_reset": False,
            "bitlocker_unlock": False,
            "ntfs_write": False,
            "ntfs_repair": False,
        },
        "notes": [
            "Login ist kein Restore-Abnahmekriterium wenn Windows-Passwort fehlt.",
            "BitLocker ohne Recovery-Key: nur Struktur/Rohimage planbar.",
        ],
    }
