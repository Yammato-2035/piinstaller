#!/usr/bin/env python3
"""Read-only disk/partition discovery for Setuphelfer rescue start assistant."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sh_json(cmd: str) -> Any:
    try:
        out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
        return json.loads(out or "null")
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def sh_text(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return ""


def rescue_medium_hint() -> dict[str, Any]:
    hint: dict[str, Any] = {"is_live": False, "medium_path": None, "labels": []}
    if Path("/run/live/medium").is_dir():
        hint["is_live"] = True
        hint["medium_path"] = "/run/live/medium"
    for label in ("SETUPHELFER_RESCUE", "SETUPHELFER"):
        hint["labels"].append(label)
    return hint


def classify_node(node: dict[str, Any], rescue_devs: set[str]) -> str:
    name = node.get("name") or ""
    fstype = (node.get("fstype") or "").lower()
    label = (node.get("label") or "").upper()
    mountpoints = node.get("mountpoints") or []
    mp = mountpoints[0] if mountpoints else None
    tran = (node.get("tran") or "").lower()
    rm = bool(node.get("rm"))
    parttype = (node.get("parttype") or "").lower()
    size = node.get("size") or 0

    if name in rescue_devs or label in {"SETUPHELFER_RESCUE", "SETUPHELFER"}:
        return "rescue_stick"
    if mp and str(mp).startswith("/run/live/medium"):
        return "rescue_stick"
    if label in {"BACKUP", "SETUPHELFER_BACKUP"} or (tran == "usb" and size > 100 * 1024**3):
        return "external_backup_disk"
    if fstype in {"ntfs", "exfat", "vfat"} and tran == "usb":
        return "external_backup_disk"
    if parttype == "c12a7328-f81f-11d2-ba4b-00a0c93ec93b" or fstype == "vfat" and "EFI" in label:
        return "efi_system_partition"
    if fstype == "ntfs" and mp in {"/mnt/windows", None}:
        if any(x in label for x in ("WINDOWS", "OS", "C")):
            return "windows_system"
        return "windows_data_or_system"
    if fstype in {"ext4", "btrfs", "xfs"} and mp == "/":
        return "linux_system"
    if fstype in {"crypto_LUKS", "BitLocker"}:
        return "encrypted_suspected"
    if fstype in {"ntfs", "exfat"} and not rm:
        return "windows_data_or_system"
    if fstype in {"ext4", "btrfs", "xfs"}:
        return "linux_data"
    if node.get("type") == "disk" and not node.get("children"):
        return "unknown_disk"
    if node.get("type") == "part" and not fstype:
        return "unknown_partition"
    if node.get("type") == "disk":
        return "internal_disk"
    return "unknown"


def walk_lsblk(node: dict[str, Any], rescue_devs: set[str], out: list[dict[str, Any]]) -> None:
    cls = classify_node(node, rescue_devs)
    out.append(
        {
            "name": node.get("name"),
            "path": f"/dev/{node.get('name')}",
            "type": node.get("type"),
            "size_bytes": node.get("size"),
            "model": node.get("model"),
            "serial": node.get("serial"),
            "tran": node.get("tran"),
            "rm": node.get("rm"),
            "fstype": node.get("fstype"),
            "label": node.get("label"),
            "mountpoints": node.get("mountpoints"),
            "classification": cls,
            "read_only_recommended": cls
            not in {"free_space", "unknown"},
        }
    )
    for child in node.get("children") or []:
        walk_lsblk(child, rescue_devs, out)


def recommend_action(devices: list[dict[str, Any]], media_stable: bool) -> dict[str, Any]:
    risks: list[str] = []
    if not media_stable:
        risks.append("live_media_unstable")
    has_windows = any(d["classification"] in {"windows_system", "windows_data_or_system"} for d in devices)
    has_linux = any(d["classification"] == "linux_system" for d in devices)
    has_backup = any(d["classification"] == "external_backup_disk" for d in devices)
    internal = [d for d in devices if d["classification"] in {"linux_system", "windows_system", "internal_disk"}]
    rec = "diagnostics_only"
    if not media_stable:
        rec = "fix_rescue_media_first"
    elif has_windows or has_linux:
        rec = "backup_before_repair_or_install"
    if has_backup:
        risks.append("protect_external_backup_disk")
    return {
        "recommended_next_action": rec,
        "risks": risks,
        "has_windows_system": has_windows,
        "has_linux_system": has_linux,
        "has_external_backup_disk": has_backup,
        "internal_system_candidates": [d["path"] for d in internal if d["type"] == "disk"],
        "rescue_stick_paths": [d["path"] for d in devices if d["classification"] == "rescue_stick"],
    }


def discover(media_stable: bool = True) -> dict[str, Any]:
    lsblk = sh_json("lsblk -J -O") or {"blockdevices": []}
    rescue_devs: set[str] = set()
    medium = sh_text("findmnt -no SOURCE /run/live/medium 2>/dev/null")
    if medium:
        rescue_devs.add(medium.replace("/dev/", "").rstrip("0123456789"))
        rescue_devs.add(medium.replace("/dev/", ""))
    devices: list[dict[str, Any]] = []
    for top in lsblk.get("blockdevices") or []:
        walk_lsblk(top, rescue_devs, devices)
    blkid = sh_text("blkid")
    smart_available = bool(sh_text("command -v smartctl"))
    return {
        "schema_version": 1,
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "read_only": True,
        "secrets_exposed": False,
        "rescue_medium": rescue_medium_hint(),
        "devices": devices,
        "blkid_summary_lines": len(blkid.splitlines()) if blkid else 0,
        "smartctl_available": smart_available,
        "recommendation": recommend_action(devices, media_stable),
    }


def main() -> int:
    media_stable = os.environ.get("SETUPHELFER_MEDIA_STABLE", "1") == "1"
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    errors: list[str] = []
    try:
        payload = discover(media_stable=media_stable)
    except Exception as exc:  # noqa: BLE001 — must always persist evidence
        errors.append(f"discover_exception:{type(exc).__name__}")
        payload = {
            "schema_version": 1,
            "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "read_only": True,
            "status": "failed",
            "error_code": "disk_discovery_exception",
            "devices": [],
            "recommendation": {
                "recommended_next_action": "diagnostics_only",
                "risks": errors,
            },
            "secrets_exposed": False,
        }
    if not payload.get("devices") and payload.get("status") != "failed":
        payload["warnings"] = [{"code": "no_devices_detected", "message": "Keine Blockgeräte erkannt."}]
    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0 if payload.get("devices") else (0 if out_path else 1)


if __name__ == "__main__":
    raise SystemExit(main())
