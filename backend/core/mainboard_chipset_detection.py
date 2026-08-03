"""
Mainboard / chipset detection — read-only, DMI + PCI host-bridge based.

PI-RS-HW-COMPAT-PROVISION-001 Phase 4 (mainboard/chipset half).

Chipset naming rule (spec PHASE 4): a chipset name may only be reported when backed
by a PCI host-bridge ID match against the small curated map below, or an unambiguous
DMI product string. Anything else stays ``chipset_status = "review_required"`` — no
guesses from a marketing name alone.

Deliberate parallel path (see docs/evidence/rescue/hardware-compat-001/
HARDWARE_DISCOVERY_IST_AUDIT.md): ``core.hardware_discovery`` already exposes
display-oriented DMI/PCI lookups (``get_motherboard_info``) for the product app.
This module builds a normalized, per-device ``HardwareDevice`` for the rescue
hardware-compat stack instead — it reads DMI/PCI itself (read-only) rather than
reusing that display formatting, per the intentional two-path design documented
in the audit.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.hardware_contracts import HardwareDevice

MAINBOARD_CHIPSET_DETECTION_VERSION = 1

# Small, curated host-bridge PCI-ID -> chipset name map. Deliberately not exhaustive
# (spec forbids "thousands of hardcoded devices" — see architecture rule). Extend via
# data/hardware/hardware_quirks.json for device-specific quirks, not here.
_HOST_BRIDGE_CHIPSET_MAP: dict[tuple[str, str], str] = {
    ("8086", "7a04"): "Intel 600 Series (Alder Lake/Raptor Lake)",
    ("8086", "3e34"): "Intel 300 Series (Coffee Lake)",
    ("1022", "14b5"): "AMD Socket AM5 (600 Series)",
    ("1022", "1480"): "AMD Socket AM4 (500 Series)",
}

_DMI_FIELDS = (
    "sys_vendor",
    "product_name",
    "board_vendor",
    "board_name",
    "bios_version",
    "bios_date",
    "chassis_type",
)


def read_dmi_fields(*, sysfs_root: Path | None = None) -> dict[str, str]:
    """Read ``/sys/class/dmi/id/*`` fields (read-only, no dmidecode privilege needed)."""
    root = sysfs_root or Path("/")
    base = root / "sys" / "class" / "dmi" / "id"
    out: dict[str, str] = {}
    if not base.exists():
        return out
    for field_name in _DMI_FIELDS:
        p = base / field_name
        if p.exists():
            try:
                out[field_name] = p.read_text(encoding="utf-8", errors="ignore").strip()
            except OSError:
                continue
    return out


# DMI chassis_type values per SMBIOS spec (subset relevant for classification).
_CHASSIS_LAPTOP_TYPES = {"8", "9", "10", "14", "30", "31", "32"}  # Portable/Laptop/Notebook/Sub Notebook/Tablet/Convertible/Detachable
_CHASSIS_SERVER_TYPES = {"17", "23", "28"}  # Main Server Chassis / Rack Mount / Blade


def classify_platform_class(
    *, dmi_fields: dict[str, str], is_raspberry_pi: bool
) -> str:
    """desktop|laptop|server|single_board_computer|unknown."""
    if is_raspberry_pi:
        return "single_board_computer"
    chassis_type = (dmi_fields.get("chassis_type") or "").strip()
    if chassis_type in _CHASSIS_LAPTOP_TYPES:
        return "laptop"
    if chassis_type in _CHASSIS_SERVER_TYPES:
        return "server"
    if chassis_type in {"3", "4", "6", "7", "13", "15"}:  # Desktop/Low Profile Desktop/Mini Tower/Tower/All in One/Space-saving
        return "desktop"
    if not dmi_fields:
        return "unknown"
    return "desktop"  # conservative default for a DMI-bearing x86 board of unknown chassis type


def resolve_chipset_from_host_bridge(pci_devices: list[HardwareDevice]) -> tuple[str | None, str]:
    """Look up a curated chipset name from the PCI host bridge device.

    Returns (chipset_name_or_none, chipset_status). ``chipset_status`` is
    "identified" only on an exact curated-map hit, else "review_required".
    """
    for dev in pci_devices:
        if not dev.product_name or "host bridge" not in dev.product_name.lower():
            continue
        if dev.vendor_id and dev.product_id:
            key = (dev.vendor_id.lower(), dev.product_id.lower())
            if key in _HOST_BRIDGE_CHIPSET_MAP:
                return _HOST_BRIDGE_CHIPSET_MAP[key], "identified"
        return None, "review_required"
    return None, "review_required"


def find_bridge_devices(pci_devices: list[HardwareDevice]) -> dict[str, list[str]]:
    """Group PCI devices by bridge role using their (already parsed) description text."""
    out: dict[str, list[str]] = {"host_bridge": [], "isa_lpc_bridge": [], "pcie_root_port": []}
    for dev in pci_devices:
        name = (dev.product_name or "").lower()
        if "host bridge" in name:
            out["host_bridge"].append(dev.device_id)
        elif "isa bridge" in name or "lpc" in name:
            out["isa_lpc_bridge"].append(dev.device_id)
        elif "pci bridge" in name or "pcie" in name and "root" in name:
            out["pcie_root_port"].append(dev.device_id)
    return out


def build_mainboard_chipset_report(
    *,
    dmi_fields: dict[str, str] | None = None,
    sysfs_root: Path | None = None,
    pci_devices: list[HardwareDevice] | None = None,
    is_raspberry_pi: bool = False,
) -> dict[str, Any]:
    """Full mainboard/chipset report. ``pci_devices`` should come from
    ``hardware_inventory.collect_pci_devices`` (this module never runs lspci itself,
    to avoid a second PCI parser — see audit)."""
    fields = dmi_fields if dmi_fields is not None else read_dmi_fields(sysfs_root=sysfs_root)
    devices = pci_devices or []
    chipset_name, chipset_status = resolve_chipset_from_host_bridge(devices)
    bridges = find_bridge_devices(devices)
    platform_class = classify_platform_class(dmi_fields=fields, is_raspberry_pi=is_raspberry_pi)

    return {
        "schema_version": "mainboard-chipset-report.v1",
        "system_vendor": fields.get("sys_vendor"),
        "system_product": fields.get("product_name"),
        "baseboard_vendor": fields.get("board_vendor"),
        "baseboard_product": fields.get("board_name"),
        "bios_version": fields.get("bios_version"),
        "bios_date": fields.get("bios_date"),
        "platform_class": platform_class,
        "host_bridge_devices": bridges["host_bridge"],
        "isa_lpc_bridge_devices": bridges["isa_lpc_bridge"],
        "pcie_root_port_devices": bridges["pcie_root_port"],
        "chipset_name": chipset_name,
        "chipset_status": chipset_status,
    }


def build_mainboard_chipset_detection_diagnostics() -> dict[str, Any]:
    return {
        "detection_version": MAINBOARD_CHIPSET_DETECTION_VERSION,
        "module": "core.mainboard_chipset_detection",
        "read_only": True,
        "writes_allowed": False,
        "curated_host_bridge_entries": len(_HOST_BRIDGE_CHIPSET_MAP),
    }


__all__ = [
    "MAINBOARD_CHIPSET_DETECTION_VERSION",
    "read_dmi_fields",
    "classify_platform_class",
    "resolve_chipset_from_host_bridge",
    "find_bridge_devices",
    "build_mainboard_chipset_report",
    "build_mainboard_chipset_detection_diagnostics",
]
