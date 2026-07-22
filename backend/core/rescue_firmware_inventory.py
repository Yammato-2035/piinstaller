"""Read-only firmware / BIOS inventory (PI-RS-ASUS-WIN11-LINUX-001).

Never flashes firmware. Never runs flashrom or capsule updates.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping

from core.rescue_machine_identity_profiles import build_machine_identity, read_dmi_fields

CONTRACT_VERSION = 1
SCHEMA_VERSION = 1


def _efivar_secure_boot() -> str:
    candidates = [
        Path("/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c"),
        Path("/sys/firmware/efi/vars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c/data"),
    ]
    for p in candidates:
        if not p.is_file():
            continue
        try:
            data = p.read_bytes()
            val = data[4] if len(data) >= 5 else (data[0] if data else None)
            if val is None:
                continue
            return "enabled" if val == 1 else "disabled"
        except OSError:
            continue
    return "unknown"


def detect_boot_mode() -> str:
    if Path("/sys/firmware/efi").is_dir():
        return "uefi"
    return "legacy" if Path("/sys/firmware").exists() else "unknown"


def detect_tpm() -> str:
    if Path("/sys/class/tpm/tpm0").exists() or Path("/dev/tpm0").exists() or Path("/dev/tpmrm0").exists():
        # Version often not reliably readable without tpm2 tools; treat presence as 2.0-ish.
        return "2.0"
    return "missing"


def fwupd_available() -> bool:
    return shutil.which("fwupdmgr") is not None


def collect_firmware_inventory(
    *,
    dmi: Mapping[str, str] | None = None,
    devices: list[Mapping[str, Any]] | None = None,
    run_fwupd: bool = False,
) -> dict[str, Any]:
    fields = dict(dmi or read_dmi_fields())
    machine = build_machine_identity(dmi=fields)
    bios = {
        "vendor": fields.get("bios_vendor") or "",
        "installed_version": fields.get("bios_version") or "",
        "installed_date": fields.get("bios_date") or "",
        "boot_mode": detect_boot_mode(),
        "secure_boot": _efivar_secure_boot(),
        "tpm": detect_tpm(),
        "fwupd_supported": fwupd_available(),
        "capsule_update_supported_unknown": True,
        "automatic_flash_allowed": False,
    }
    warnings: list[str] = []
    if machine.get("confidence") == "low":
        warnings.append("machine_confidence_low")
    if bios["boot_mode"] != "uefi":
        warnings.append("boot_mode_not_uefi")

    device_list: list[dict[str, Any]] = [dict(d) for d in (devices or [])]
    if run_fwupd and fwupd_available():
        try:
            proc = subprocess.run(
                ["fwupdmgr", "get-devices", "--json"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                device_list.append({"source": "fwupdmgr", "raw_present": True})
            else:
                warnings.append("fwupd_get_devices_failed")
        except (OSError, subprocess.TimeoutExpired):
            warnings.append("fwupd_unavailable_or_timeout")

    status = "ok"
    if warnings:
        status = "review_required"
    if machine.get("expected_profile") == "unknown":
        status = "blocked"
        warnings.append("unknown_machine")

    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "machine": machine,
        "bios": bios,
        "devices": device_list,
        "status": status,
        "warnings": warnings,
        "flash_endpoint_available": False,
        "automatic_flash_allowed": False,
    }
