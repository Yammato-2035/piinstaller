"""
Rescue boot machine identity — read-only discovery (RS-P1).
"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Any

from core.rescue_disk_role_classifier import classify_disk_roles
from core.rescue_os_detection import classify_detected_os
from core.rescue_storage_discovery import discover_rescue_storage
from core.rescue_wifi_diagnostics import classify_wifi_status
from core.windows_ntfs_detection_contract import redact_serial

CONTRACT_VERSION = 1


def detect_boot_mode() -> str:
    if Path("/sys/firmware/efi").is_dir():
        return "uefi"
    try:
        out = subprocess.check_output(["fdisk", "-l"], text=True, stderr=subprocess.DEVNULL, timeout=5)
        if "Disklabel type: dos" in out and "EFI" not in out:
            return "bios"
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def detect_booted_machine_identity() -> dict[str, Any]:
    model = ""
    vendor = ""
    serial_redacted = ""
    try:
        for base in ("/sys/class/dmi/id/product_name", "/sys/class/dmi/id/sys_vendor", "/sys/class/dmi/id/product_serial"):
            p = Path(base)
            if p.is_file():
                val = p.read_text(encoding="utf-8", errors="replace").strip()
                if base.endswith("product_name"):
                    model = val
                elif base.endswith("sys_vendor"):
                    vendor = val
                elif base.endswith("product_serial"):
                    serial_redacted = redact_serial(val)
    except OSError:
        pass
    return {
        "contract_version": CONTRACT_VERSION,
        "vendor": vendor or "unknown",
        "model": model or "unknown",
        "serial_redacted": serial_redacted,
        "boot_mode": detect_boot_mode(),
        "arch": platform.machine(),
        "kernel": platform.release(),
        "booted_from_rescue": Path("/run/live/medium").is_dir(),
    }


def build_rescue_system_summary() -> dict[str, Any]:
    discovery = discover_rescue_storage()
    devices = classify_disk_roles(discovery.get("devices") or [])
    os_profiles = [classify_detected_os(d) for d in devices if d.get("type") == "disk"]
    identity = detect_booted_machine_identity()
    wifi = classify_wifi_status()
    return {
        "contract_version": CONTRACT_VERSION,
        "identity": identity,
        "boot_mode": identity.get("boot_mode"),
        "devices": devices,
        "os_profiles": os_profiles,
        "source_candidates": [d for d in devices if d.get("source_candidate")],
        "target_candidates": [d for d in devices if d.get("target_allowed")],
        "blocked_devices": discovery.get("blocked_devices") or [],
        "network": {
            "wifi_status": wifi.get("status"),
            "wlan_required_for_hdd": wifi.get("wlan_required_for_local_hdd_backup", False),
            "blocks_cloud": wifi.get("blocks_cloud_backup", False),
        },
        "cloud_target": {"available": False, "pro_only": True, "plan_only": True},
        "execute_allowed": False,
    }
