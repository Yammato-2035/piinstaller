"""
Rescue WiFi diagnostics — classify state without logging secrets.
"""

from __future__ import annotations

import re
import subprocess
from typing import Any

_WIFI_INTERFACE_RE = re.compile(r"^\s*Interface\s+(\S+)", re.M)
_UNMANAGED_RE = re.compile(r"^(\S+):wifi:unmanaged$", re.M)


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=8)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def classify_wifi_status() -> dict[str, Any]:
    rfkill = _run(["rfkill", "list"])
    iw = _run(["iw", "dev"])
    nm_radio = _run(["nmcli", "radio"])
    nm_dev = _run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device", "status"])

    interfaces = _WIFI_INTERFACE_RE.findall(iw)
    unmanaged = _UNMANAGED_RE.findall(nm_dev)
    wifi_hw_missing = "WIFI-HW" in nm_radio and "missing" in nm_radio.lower().split("WIFI-HW")[-1][:20]
    wifi_radio_on = "aktiviert" in nm_radio or "enabled" in nm_radio.lower()
    driver_loaded = bool(re.search(r"\biwlwifi\b", _run(["lsmod"]) or ""))

    blocks_hdd_backup = False
    blocks_cloud_backup = not bool(re.search(r":wifi:connected", nm_dev))
    required_for_local_hdd = False
    required_for_cloud = True

    fix_suggestions: list[str] = []
    if unmanaged:
        fix_suggestions.append("nmcli_device_set_managed_yes")
    if not wifi_radio_on:
        fix_suggestions.append("nmcli_radio_wifi_on")
    if "Soft blocked: yes" in rfkill:
        fix_suggestions.append("rfkill_unblock_wifi")

    return {
        "wifi_hardware_detected": bool(interfaces) or driver_loaded,
        "wifi_interface_present": bool(interfaces),
        "interfaces": interfaces,
        "unmanaged_devices": unmanaged,
        "driver_loaded": driver_loaded,
        "wifi_hw_missing_nmcli": wifi_hw_missing,
        "wifi_radio_on": wifi_radio_on,
        "rfkill_soft_blocked": "Soft blocked: yes" in rfkill,
        "wlan_required_for_local_hdd_backup": required_for_local_hdd,
        "wlan_required_for_cloud_backup": required_for_cloud,
        "blocks_local_hdd_backup": blocks_hdd_backup,
        "blocks_cloud_backup": blocks_cloud_backup,
        "fix_suggestions": fix_suggestions,
        "status": "unmanaged" if unmanaged else ("missing_hw" if wifi_hw_missing and not interfaces else "available"),
    }
