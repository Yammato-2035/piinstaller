"""Input device inventory + keyboard classification for TUI input diagnostic."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from core.rescue_tui_input_diagnostic_contract import redact_serial_like


def parse_proc_bus_input_devices(text: str) -> list[dict[str, Any]]:
    blocks = re.split(r"\n(?=I: )", text.strip() + "\n") if text.strip() else []
    devices: list[dict[str, Any]] = []
    for block in blocks:
        if not block.strip():
            continue
        entry: dict[str, Any] = {
            "name": "",
            "phys": "",
            "sysfs": "",
            "handlers": [],
            "bus": "unknown",
            "vendor_id": "",
            "product_id": "",
            "is_keyboard": False,
            "event_node": "",
        }
        for line in block.splitlines():
            if line.startswith("N: Name="):
                entry["name"] = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("P: Phys="):
                entry["phys"] = line.split("=", 1)[1].strip()
            elif line.startswith("S: Sysfs="):
                entry["sysfs"] = line.split("=", 1)[1].strip()
            elif line.startswith("H: Handlers="):
                handlers = line.split("=", 1)[1].strip().split()
                entry["handlers"] = handlers
                for h in handlers:
                    if h.startswith("event"):
                        entry["event_node"] = f"/dev/input/{h}"
            elif line.startswith("I: "):
                # I: Bus=0011 Vendor=0001 Product=0001 Version=ab41
                m = re.search(r"Bus=([0-9a-fA-F]+).*Vendor=([0-9a-fA-F]+).*Product=([0-9a-fA-F]+)", line)
                if m:
                    bus_hex = int(m.group(1), 16)
                    entry["vendor_id"] = m.group(2)
                    entry["product_id"] = m.group(3)
                    entry["bus"] = _bus_name(bus_hex, entry["phys"])
        name_l = entry["name"].lower()
        handlers = " ".join(entry["handlers"]).lower()
        entry["is_keyboard"] = ("kbd" in handlers) or ("keyboard" in name_l)
        devices.append(entry)
    return devices


def _bus_name(bus_hex: int, phys: str) -> str:
    # linux input.h BUS_* 
    if bus_hex == 0x11 or "isa" in (phys or "").lower() or "i8042" in (phys or "").lower():
        return "i8042"
    if bus_hex == 0x03 or (phys or "").lower().startswith("usb-"):
        return "usb"
    if bus_hex == 0x05:
        return "bluetooth"
    return "unknown"


def classify_keyboard(device: dict[str, Any]) -> dict[str, Any]:
    bus = str(device.get("bus") or "unknown")
    name = str(device.get("name") or "")
    name_l = name.lower()
    internal = False
    external = False
    if not device.get("is_keyboard"):
        pass
    elif bus == "i8042" or "at translated" in name_l or "i8042" in str(device.get("phys") or "").lower():
        internal = True
    elif bus == "usb":
        external = True
    out = {
        "event_node": device.get("event_node") or "",
        "name": name,
        "phys": redact_serial_like(str(device.get("phys") or "")),
        "bus": bus,
        "is_keyboard": bool(device.get("is_keyboard")),
        "is_internal_candidate": internal,
        "is_external_candidate": external,
        "vendor_id": str(device.get("vendor_id") or ""),
        "product_id": str(device.get("product_id") or ""),
        "sysfs_path_redacted": redact_serial_like(str(device.get("sysfs") or "")),
    }
    return out


def inventory_from_proc_devices(path: Path | None = None) -> list[dict[str, Any]]:
    p = path or Path("/proc/bus/input/devices")
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [classify_keyboard(d) for d in parse_proc_bus_input_devices(text) if d.get("is_keyboard")]


def diff_new_external_keyboards(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> list[dict[str, Any]]:
    before_nodes = {d.get("event_node") for d in before}
    return [
        d
        for d in after
        if d.get("event_node") not in before_nodes and d.get("is_external_candidate")
    ]
