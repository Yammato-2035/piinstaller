"""NVMe install-target identity and stable role binding (PI-RS-INSTALL-ASSISTANT-001).

Never trust /dev/nvme0n1 vs nvme1n1 alone. Roles bind via serial_hash + model + size + PCI path.
No destructive I/O in this module.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

CONTRACT_VERSION = 1
SCHEMA_VERSION = 1

# Plan roles (canonical) + ASUS-branch aliases
ROLE_WINDOWS_SYSTEM = "windows_system"
ROLE_LINUX_TARGET = "linux_target"
ROLE_RESCUE_USB = "rescue_usb"
ROLE_UNASSIGNED = "unassigned"
# Legacy aliases from ASUS port
ROLE_WINDOWS = "windows"
ROLE_LINUX = "linux"

CANONICAL_ROLES = frozenset(
    {ROLE_WINDOWS_SYSTEM, ROLE_LINUX_TARGET, ROLE_RESCUE_USB, ROLE_UNASSIGNED}
)
ROLE_ALIASES = {
    ROLE_WINDOWS: ROLE_WINDOWS_SYSTEM,
    ROLE_LINUX: ROLE_LINUX_TARGET,
    "windows_nvme": ROLE_WINDOWS_SYSTEM,
    "linux_nvme": ROLE_LINUX_TARGET,
}

RESCUE_USB_LABEL_HINTS = frozenset(
    {
        "SETUPHELFER",
        "SETUP_LOGS",
        "SETUP_LOGS2",
        "RESCUE",
        "CASPER-RW",
    }
)


def canonicalize_role(role: str) -> str:
    r = (role or "").strip()
    if r in ROLE_ALIASES:
        return ROLE_ALIASES[r]
    if r in CANONICAL_ROLES:
        return r
    return ROLE_UNASSIGNED


def mask_serial(serial: str) -> str:
    s = (serial or "").strip()
    if not s:
        return ""
    if len(s) <= 4:
        return "****"
    return f"…{s[-4:]}"


def hash_serial(serial: str) -> str:
    s = (serial or "").strip()
    if not s:
        return ""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def stable_nvme_identity_key(entry: Mapping[str, Any]) -> str:
    parts = [
        str(entry.get("model") or ""),
        str(entry.get("serial_hash") or hash_serial(str(entry.get("serial") or ""))),
        str(entry.get("size_bytes") or 0),
        str(entry.get("pci_address") or entry.get("pci_path") or ""),
        str(entry.get("nguid") or entry.get("eui64") or ""),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def is_likely_rescue_usb(raw: Mapping[str, Any]) -> bool:
    """Heuristic: USB transport or known Setuphelfer volume labels — never a linux_target."""
    transport = str(raw.get("transport") or raw.get("tran") or "").lower()
    if transport in {"usb", "usb-storage"}:
        return True
    device_path = str(raw.get("device_path") or raw.get("path") or "").lower()
    if device_path.startswith("/dev/sd") and not device_path.startswith("/dev/nvme"):
        # sd* alone is not enough; require label hint or explicit flag
        if bool(raw.get("is_rescue_usb") or raw.get("rescue_medium")):
            return True
    labels = []
    for key in ("label", "fs_label", "volume_label"):
        v = raw.get(key)
        if v:
            labels.append(str(v).upper())
    for part in list(raw.get("partitions") or []) + list(raw.get("filesystems") or []):
        if isinstance(part, Mapping):
            for key in ("label", "name", "PARTLABEL", "LABEL"):
                v = part.get(key)
                if v:
                    labels.append(str(v).upper())
    return any(lab in RESCUE_USB_LABEL_HINTS for lab in labels)


def normalize_nvme_entry(raw: Mapping[str, Any]) -> dict[str, Any]:
    serial = str(raw.get("serial") or raw.get("SerialNumber") or "")
    serial_hash = str(raw.get("serial_hash") or "") or hash_serial(serial)
    size = int(raw.get("size_bytes") or raw.get("PhysicalSize") or raw.get("size") or 0)
    model = str(raw.get("model") or raw.get("ModelNumber") or raw.get("Model") or "")
    device_path = str(raw.get("device_path") or raw.get("DevicePath") or raw.get("path") or "")
    controller = str(raw.get("controller") or "")
    if not controller and device_path.startswith("/dev/nvme"):
        m = re.match(r"(/dev/nvme\d+)", device_path)
        controller = m.group(1) if m else ""
    intended = canonicalize_role(str(raw.get("intended_role") or ROLE_UNASSIGNED))
    if is_likely_rescue_usb(raw):
        intended = ROLE_RESCUE_USB
    entry = {
        "device_path": device_path,
        "controller": controller,
        "model": model,
        "serial_masked": mask_serial(serial) if serial else str(raw.get("serial_masked") or ""),
        "serial_hash": serial_hash,
        "firmware_revision": str(raw.get("firmware_revision") or raw.get("Firmware") or ""),
        "size_bytes": size,
        "logical_sector_size": int(raw.get("logical_sector_size") or 0),
        "physical_sector_size": int(raw.get("physical_sector_size") or 0),
        "eui64": raw.get("eui64"),
        "nguid": raw.get("nguid"),
        "pci_address": str(raw.get("pci_address") or raw.get("pci_path") or ""),
        "sysfs_path": str(raw.get("sysfs_path") or ""),
        "namespace_id": int(raw.get("namespace_id") or 1),
        "partition_table": str(raw.get("partition_table") or "unknown"),
        "partitions": list(raw.get("partitions") or []),
        "filesystems": list(raw.get("filesystems") or []),
        "smart_status": str(raw.get("smart_status") or "unknown"),
        "intended_role": intended,
        "is_rescue_usb": intended == ROLE_RESCUE_USB,
        "write_allowed": False,
        "identity_key": "",
        "health_status": str(raw.get("health_status") or raw.get("smart_status") or "unknown"),
        "transport": str(raw.get("transport") or raw.get("tran") or ""),
    }
    entry["identity_key"] = stable_nvme_identity_key(entry)
    return entry


def inventory_from_nvme_list_json(payload: Mapping[str, Any] | list[Any]) -> list[dict[str, Any]]:
    """Parse `nvme list -o json` style payload into normalized entries."""
    devices: list[Any]
    if isinstance(payload, list):
        devices = payload
    else:
        devices = list(payload.get("Devices") or payload.get("devices") or [])
    return [normalize_nvme_entry(d if isinstance(d, Mapping) else {}) for d in devices]


def bind_role_by_identity(
    inventory: list[Mapping[str, Any]],
    *,
    serial_hash: str,
    role: str,
    model: str | None = None,
    size_bytes: int | None = None,
    pci_path: str | None = None,
    allow_rescue_usb: bool = False,
) -> dict[str, Any]:
    role = canonicalize_role(role)
    if role == ROLE_RESCUE_USB and not allow_rescue_usb:
        return {
            "ok": False,
            "role": role,
            "match_count": 0,
            "entry": None,
            "error": "rescue_usb_not_bindable_as_install_target",
        }
    matches: list[dict[str, Any]] = []
    for raw in inventory:
        entry = normalize_nvme_entry(raw)
        if entry["is_rescue_usb"] and role in {ROLE_LINUX_TARGET, ROLE_WINDOWS_SYSTEM}:
            continue
        if entry["serial_hash"] != serial_hash:
            continue
        if model and entry["model"] and entry["model"] != model:
            continue
        if size_bytes is not None and entry["size_bytes"] and entry["size_bytes"] != size_bytes:
            continue
        if pci_path and entry["pci_address"] and entry["pci_address"] != pci_path:
            continue
        matches.append(entry)
    if len(matches) != 1:
        return {
            "ok": False,
            "role": role,
            "match_count": len(matches),
            "entry": None,
            "error": "ambiguous_or_missing_nvme_identity",
        }
    bound = dict(matches[0])
    bound["intended_role"] = role
    bound["write_allowed"] = False
    return {"ok": True, "role": role, "match_count": 1, "entry": bound, "error": None}


def build_asus_install_targets_manifest(
    *,
    windows: Mapping[str, Any] | None,
    linux: Mapping[str, Any] | None,
    machine_profile: str = "asus_rog_gabriel",
) -> dict[str, Any]:
    def _slot(entry: Mapping[str, Any] | None) -> dict[str, Any]:
        if not entry:
            return {
                "serial_hash": "",
                "model": "",
                "size_bytes": 0,
                "pci_path": "",
                "confirmed": False,
            }
        n = normalize_nvme_entry(entry)
        return {
            "serial_hash": n["serial_hash"],
            "model": n["model"],
            "size_bytes": n["size_bytes"],
            "pci_path": n["pci_address"],
            "identity_key": n["identity_key"],
            "serial_masked": n["serial_masked"],
            "confirmed": bool(entry.get("confirmed")),
        }

    win = _slot(windows)
    lin = _slot(linux)
    same = bool(win["serial_hash"] and win["serial_hash"] == lin["serial_hash"])
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "machine_profile": machine_profile,
        "windows_target": win,
        "linux_target": lin,
        "windows_system": win,
        "targets_distinct": not same,
        "roles_device_path_independent": True,
        "write_allowed_windows": False,
        "write_allowed_linux": False,
        "write_allowed_windows_system": False,
        "write_allowed_linux_target": False,
    }


def resolve_role_after_device_rename(
    inventory: list[Mapping[str, Any]],
    targets: Mapping[str, Any],
) -> dict[str, Any]:
    """Re-resolve windows/linux roles after /dev/nvmeXn1 names shuffled."""
    win_src = targets.get("windows_target") or targets.get("windows_system") or {}
    lin_src = targets.get("linux_target") or {}
    win_hash = str(win_src.get("serial_hash") or "")
    lin_hash = str(lin_src.get("serial_hash") or "")
    win = (
        bind_role_by_identity(inventory, serial_hash=win_hash, role=ROLE_WINDOWS_SYSTEM)
        if win_hash
        else {"ok": False, "error": "windows_serial_missing", "entry": None}
    )
    lin = (
        bind_role_by_identity(inventory, serial_hash=lin_hash, role=ROLE_LINUX_TARGET)
        if lin_hash
        else {"ok": False, "error": "linux_serial_missing", "entry": None}
    )
    win_path = (win.get("entry") or {}).get("device_path")
    lin_path = (lin.get("entry") or {}).get("device_path")
    return {
        "ok": bool(win.get("ok") and lin.get("ok") and win_path and lin_path and win_path != lin_path),
        "windows": win,
        "linux": lin,
        "windows_system": win,
        "linux_target": lin,
        "device_names_may_differ": True,
        "identity_stable": True,
    }


def evaluate_nvme_health(entry: Mapping[str, Any]) -> dict[str, Any]:
    status = str(entry.get("smart_status") or entry.get("health_status") or "unknown").lower()
    critical = bool(entry.get("critical_warning"))
    media_errors = int(entry.get("media_errors") or entry.get("media_and_data_integrity_errors") or 0)
    if critical or status in {"critical", "failed"} or media_errors > 0:
        health = "unsuitable_for_install"
    elif status in {"warning", "review"}:
        health = "review_required"
    elif status in {"ok", "healthy", "passed"}:
        health = "healthy"
    else:
        health = "unknown"
    return {
        "health_status": health,
        "install_allowed": health == "healthy",
        "smart_status": status,
        "media_errors": media_errors,
        "critical_warning": critical,
    }


def load_targets_manifest(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def save_targets_manifest(manifest: Mapping[str, Any], path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(manifest), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"written": True, "path": str(path)}
