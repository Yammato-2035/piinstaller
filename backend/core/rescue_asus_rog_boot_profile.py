"""ASUS ROG rescue boot profile + read-only BIOS/Win11 gate (Phase C)."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROFILE_SCHEMA_VERSION = 1
GATE_SCHEMA_VERSION = 1

_ASUS_DMI_RE = re.compile(r"asus", re.I)
_ROG_DMI_RE = re.compile(r"rog|strix|zephyrus|tuf.?gaming", re.I)


def _read_text(path: Path, limit: int = 256) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit].strip()
    except OSError:
        return ""


def read_dmi_fields(*, sys_class_dmi: Path | None = None) -> dict[str, str]:
    root = sys_class_dmi or Path("/sys/class/dmi/id")
    return {
        "sys_vendor": _read_text(root / "sys_vendor"),
        "product_name": _read_text(root / "product_name"),
        "product_version": _read_text(root / "product_version"),
        "board_vendor": _read_text(root / "board_vendor"),
        "board_name": _read_text(root / "board_name"),
    }


def dmi_suggests_asus_rog(dmi: dict[str, str] | None = None) -> bool:
    fields = dmi or read_dmi_fields()
    blob = " ".join(fields.values())
    return bool(_ASUS_DMI_RE.search(blob) and _ROG_DMI_RE.search(blob))


def resolve_asus_rog_boot_profile(
    cmdline: str = "",
    *,
    dmi: dict[str, str] | None = None,
) -> dict[str, Any]:
    """GUI-capable profile for ASUS ROG; never forces nomodeset."""
    is_rog = dmi_suggests_asus_rog(dmi)
    cmdline_flag = bool(re.search(r"(?:^|\s)setuphelfer_asus_rog_lab=1(?:\s|$)", cmdline or ""))
    active = is_rog or cmdline_flag
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "profile_id": "asus_rog",
        "active": active,
        "boot_mode": "gui_capable",
        "gui_available": True,
        "gui_start_allowed": True,
        "gui_progress_allowed": True,
        "reason_code": "asus_rog_lab" if active else "not_asus_rog",
        "operator_mode": "standard",
        "dmi": dmi or read_dmi_fields(),
    }


def _efivar_secure_boot_on() -> bool | None:
    """Return True/False if detectable, else None."""
    candidates = [
        Path("/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c"),
        Path("/sys/firmware/efi/vars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c/data"),
    ]
    for p in candidates:
        if not p.is_file():
            continue
        try:
            data = p.read_bytes()
            # efivarfs: 4-byte attributes + 1-byte value
            if len(data) >= 5:
                return data[4] == 1
            if len(data) == 1:
                return data[0] == 1
        except OSError:
            continue
    return None


def _bitlocker_hint_present() -> bool:
    # Best-effort: look for BitLocker metadata markers on block devices (read-only).
    try:
        for line in Path("/proc/partitions").read_text(encoding="utf-8", errors="replace").splitlines()[2:]:
            parts = line.split()
            if len(parts) < 4:
                continue
            name = parts[3]
            if not re.match(r"^(nvme\d+n\d+|sd[a-z]+|vd[a-z]+)$", name):
                continue
            # Do not open whole disks for scanning here — too slow/risky in gate.
            _ = name
    except OSError:
        pass
    # Evidence from prior discovery if present.
    for cand in (
        Path("/run/setuphelfer-rescue/disk-discovery.json"),
        Path("/run/setuphelfer/disk-discovery.json"),
    ):
        if not cand.is_file():
            continue
        try:
            blob = cand.read_text(encoding="utf-8", errors="replace").lower()
            if "bitlocker" in blob or "fve" in blob:
                return True
        except OSError:
            continue
    return False


def evaluate_asus_rog_bios_win11_gate(
    *,
    dmi: dict[str, str] | None = None,
    cmdline: str | None = None,
) -> dict[str, Any]:
    """
    Read-only checklist for BIOS settings that commonly block Windows 11 install
    on ASUS ROG (Secure Boot off, CSM on, VMD/RAID, Fast Boot, BitLocker).
    Never writes BIOS/EFI variables.
    """
    dmi_fields = dmi or read_dmi_fields()
    is_rog = dmi_suggests_asus_rog(dmi_fields)
    cmdline = cmdline if cmdline is not None else _read_text(Path("/proc/cmdline"), 4096)
    findings: list[dict[str, Any]] = []
    actions: list[str] = []

    efi = Path("/sys/firmware/efi").is_dir()
    findings.append(
        {
            "id": "uefi_mode",
            "status": "ok" if efi else "warn",
            "detail": "UEFI firmware interface present" if efi else "No EFI sysfs — Legacy/CSM likely",
        }
    )
    if not efi:
        actions.append("BIOS: CSM/Legacy deaktivieren, reiner UEFI-Boot")

    sb = _efivar_secure_boot_on()
    if sb is True:
        findings.append({"id": "secure_boot", "status": "ok", "detail": "Secure Boot enabled"})
    elif sb is False:
        findings.append({"id": "secure_boot", "status": "warn", "detail": "Secure Boot disabled"})
        actions.append("BIOS: Secure Boot aktivieren (Win11-Setup erfordert oft Secure Boot)")
    else:
        findings.append({"id": "secure_boot", "status": "unknown", "detail": "Secure Boot not readable"})

    # Fast Boot / VMD cannot be read reliably from Linux without vendor tools —
    # emit operator checklist items when ROG is detected.
    if is_rog:
        findings.append(
            {
                "id": "fast_boot",
                "status": "checklist",
                "detail": "Operator must verify Fast Boot is Off for USB install media",
            }
        )
        actions.append("BIOS: Fast Boot = Disabled beim USB-Install")
        findings.append(
            {
                "id": "vmd_raid",
                "status": "checklist",
                "detail": "VMD/RAID can hide NVMe from Win11 setup — prefer AHCI if install fails",
            }
        )
        actions.append("BIOS: VMD/RAID prüfen — bei fehlender Systemdisk AHCI/Non-RAID")
        findings.append(
            {
                "id": "usb_boot_order",
                "status": "checklist",
                "detail": "USB storage must be above internal disk for rescue/install stick",
            }
        )
        actions.append("BIOS: Boot Order — USB Stick vor interner NVMe")

    if _bitlocker_hint_present():
        findings.append({"id": "bitlocker", "status": "warn", "detail": "BitLocker markers seen in discovery"})
        actions.append("BitLocker: Wiederherstellungsschlüssel bereithalten vor Partitionierung")
    else:
        findings.append({"id": "bitlocker", "status": "unknown", "detail": "No BitLocker hint in runtime discovery"})

    warn_count = sum(1 for f in findings if f["status"] in ("warn", "checklist"))
    return {
        "schema_version": GATE_SCHEMA_VERSION,
        "gate_id": "asus_rog_bios_win11",
        "asus_rog_detected": is_rog,
        "evaluated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cmdline_asus_lab": bool(re.search(r"(?:^|\s)setuphelfer_asus_rog_lab=1(?:\s|$)", cmdline or "")),
        "findings": findings,
        "operator_next_actions": actions,
        "severity": "attention" if (is_rog and warn_count) else ("info" if is_rog else "n/a"),
        "blocks_bvr": False,
        "production_ready": False,
        "secrets_exposed": False,
    }


def write_asus_rog_bios_gate_evidence(
    gate: dict[str, Any] | None = None,
    *,
    state_dir: Path | None = None,
    evidence_base: Path | None = None,
) -> dict[str, Any]:
    doc = gate or evaluate_asus_rog_bios_win11_gate()
    state = state_dir or Path(os.environ.get("SETUPHELFER_RESCUE_STATE_DIR", "/run/setuphelfer-rescue"))
    state.mkdir(parents=True, exist_ok=True)
    out = state / "asus-rog-bios-gate.json"
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    if evidence_base is not None:
        dest = evidence_base / "setuphelfer" / "evidence" / "boot" / "asus-rog-bios-gate.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc
