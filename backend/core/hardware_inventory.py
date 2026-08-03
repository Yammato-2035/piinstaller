"""
Generic, read-only hardware inventory collection.

PI-RS-HW-COMPAT-PROVISION-001 Phase 3.

Design rules (see spec PHASE 3):
- Every collector is read-only. No ``apt install``, no writes, no privileged calls.
- A missing tool is recorded as a ``capability_missing`` entry, never a crash.
- Every collector accepts an optional ``raw_text``/``runner`` override so tests can
  inject fixture output without touching real hardware (``lspci``/``lsusb``/``lsmod``/
  ``dmesg``/``/proc``/``/sys`` are never required to run the test suite).
- Unknown vendor/product strings stay ``None`` — this module never guesses names.

This module does not classify devices into rich subclasses (GPU driver status, USB
composite functions, printer/scanner capabilities, ...). That is the job of the
dedicated Phase 4-9 detection modules, which consume the raw ``HardwareDevice`` rows
produced here.
"""

from __future__ import annotations

import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from core.hardware_contracts import (
    Bus,
    HardwareDevice,
    HardwareDriverState,
    HardwareInventory,
    PlatformIdentity,
)

HARDWARE_INVENTORY_VERSION = 1

Runner = Callable[..., "subprocess.CompletedProcess[str]"] | None


def _run_tool(argv: list[str], *, runner: Runner = None, timeout: int = 10) -> tuple[str, bool]:
    """Run a read-only probe tool. Returns (stdout, tool_available)."""
    try:
        if runner is not None:
            result = runner(argv, capture_output=True, text=True, timeout=timeout)
        else:
            result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)  # noqa: S603
        return (result.stdout or ""), True
    except FileNotFoundError:
        return "", False
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        return "", False


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# --------------------------------------------------------------------------- PCI

_PCI_ID_RE = re.compile(r"\[([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\]")


def collect_pci_devices(
    *, runner: Runner = None, raw_text: str | None = None
) -> tuple[list[HardwareDevice], list[str]]:
    """Parse ``lspci -nnk`` output into generic HardwareDevice rows (any PCI class)."""
    missing: list[str] = []
    text = raw_text
    if text is None:
        text, available = _run_tool(["lspci", "-nnk"], runner=runner)
        if not available:
            missing.append("lspci")
            return [], missing

    devices: list[HardwareDevice] = []
    current_addr = ""
    current_desc = ""
    current_ids: tuple[str | None, str | None] = (None, None)
    current_driver: str | None = None
    current_modules: list[str] = []

    def _flush() -> None:
        if not current_addr:
            return
        vendor_id, product_id = current_ids
        devices.append(
            HardwareDevice(
                device_id=f"pci:{current_addr}",
                device_class="pci",
                bus=Bus.PCI,
                vendor_id=vendor_id,
                product_id=product_id,
                product_name=current_desc or None,
                driver=HardwareDriverState(
                    kernel_driver_in_use=current_driver,
                    kernel_modules_loaded=tuple(current_modules),
                ),
                operational_status="detected" if current_desc else "unknown",
                detection_confidence=0.9 if vendor_id else 0.4,
            )
        )

    for line in (text or "").splitlines():
        if line and not line[0].isspace():
            _flush()
            current_driver = None
            current_modules = []
            parts = line.split(None, 1)
            current_addr = parts[0] if parts else ""
            rest = parts[1] if len(parts) > 1 else ""
            ids = _PCI_ID_RE.search(rest)
            current_ids = (ids.group(1), ids.group(2)) if ids else (None, None)
            current_desc = _PCI_ID_RE.sub("", rest).strip()
        elif "Kernel driver in use:" in line:
            current_driver = line.split(":", 1)[-1].strip()
        elif "Kernel modules:" in line:
            mods = line.split(":", 1)[-1].strip()
            current_modules = [m.strip() for m in mods.split(",") if m.strip()]
    _flush()
    return devices, missing


def collect_storage_controllers(
    *, runner: Runner = None, raw_text: str | None = None
) -> tuple[list[HardwareDevice], list[str]]:
    """Subset of PCI devices that are storage controllers (SATA/NVMe/RAID/AHCI)."""
    devices, missing = collect_pci_devices(runner=runner, raw_text=raw_text)
    keywords = ("sata", "nvme", "raid", "ahci", "non-volatile memory", "storage controller")
    out = [
        d
        for d in devices
        if d.product_name and any(k in d.product_name.lower() for k in keywords)
    ]
    return out, missing


# --------------------------------------------------------------------------- USB

_LSUSB_LINE_RE = re.compile(
    r"^Bus\s+(?P<bus>\d+)\s+Device\s+(?P<dev>\d+):\s+ID\s+(?P<vid>[0-9a-fA-F]{4}):(?P<pid>[0-9a-fA-F]{4})\s*(?P<name>.*)$"
)


def collect_usb_devices(
    *, runner: Runner = None, raw_text: str | None = None
) -> tuple[list[HardwareDevice], list[str]]:
    """Parse plain ``lsusb`` output into generic HardwareDevice rows."""
    missing: list[str] = []
    text = raw_text
    if text is None:
        text, available = _run_tool(["lsusb"], runner=runner)
        if not available:
            missing.append("lsusb")
            return [], missing

    devices: list[HardwareDevice] = []
    for line in (text or "").splitlines():
        m = _LSUSB_LINE_RE.match(line.strip())
        if not m:
            continue
        bus = m.group("bus")
        dev = m.group("dev")
        vendor_id = m.group("vid").lower()
        product_id = m.group("pid").lower()
        name = (m.group("name") or "").strip() or None
        vendor_name = None
        product_name = name
        if name and " " in name:
            # lsusb convention: "<Vendor string> <Product string>" — best-effort split only
            # for display; classification modules must not rely on this split for logic.
            vendor_name = name.split(" ", 1)[0]
        # "0000:0000" is a reserved USB-IF placeholder, not a real assigned ID — treat as
        # no usable identity rather than a confidently "detected" device.
        has_real_id = bool(vendor_id) and bool(product_id) and (vendor_id, product_id) != ("0000", "0000")
        devices.append(
            HardwareDevice(
                device_id=f"usb:{bus}-{dev}",
                device_class="usb",
                bus=Bus.USB,
                vendor_id=vendor_id,
                product_id=product_id,
                vendor_name=vendor_name,
                product_name=product_name,
                operational_status="detected" if has_real_id else "unknown",
                detection_confidence=0.85 if (name and has_real_id) else 0.3,
            )
        )
    return devices, missing


# --------------------------------------------------------------------------- Platform bus

def collect_platform_devices(
    *, sysfs_root: Path | None = None
) -> tuple[list[HardwareDevice], list[str]]:
    """Enumerate ``/sys/bus/platform/devices`` (device-tree platform devices, no tool)."""
    root = sysfs_root or Path("/")
    base = root / "sys" / "bus" / "platform" / "devices"
    missing: list[str] = []
    if not base.exists():
        missing.append("sysfs:platform_bus")
        return [], missing
    devices: list[HardwareDevice] = []
    try:
        for entry in sorted(base.iterdir()):
            modalias = None
            modalias_path = entry / "modalias"
            if modalias_path.exists():
                try:
                    modalias = modalias_path.read_text(encoding="utf-8", errors="ignore").strip() or None
                except OSError:
                    pass
            driver = None
            driver_link = entry / "driver"
            if driver_link.exists():
                try:
                    driver = driver_link.resolve().name
                except OSError:
                    pass
            devices.append(
                HardwareDevice(
                    device_id=f"platform:{entry.name}",
                    device_class="platform",
                    bus=Bus.PLATFORM,
                    product_name=entry.name,
                    kernel_modalias=modalias,
                    driver=HardwareDriverState(kernel_driver_in_use=driver),
                    operational_status="detected",
                    detection_confidence=0.6,
                )
            )
    except OSError:
        missing.append("sysfs:platform_bus")
    return devices, missing


# --------------------------------------------------------------------------- Input devices

def collect_input_devices(
    *, raw_text: str | None = None, sysfs_root: Path | None = None
) -> tuple[list[HardwareDevice], list[str]]:
    """Parse ``/proc/bus/input/devices`` blocks into generic HardwareDevice rows.

    Strict privacy rule (spec PHASE 7): this reads device metadata only (name,
    handlers, bus/vendor/product IDs) — never key/pointer events.
    """
    missing: list[str] = []
    text = raw_text
    if text is None:
        root = sysfs_root or Path("/")
        path = root / "proc" / "bus" / "input" / "devices"
        if not path.exists():
            missing.append("proc:bus_input_devices")
            return [], missing
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            missing.append("proc:bus_input_devices")
            return [], missing

    devices: list[HardwareDevice] = []
    blocks = (text or "").split("\n\n")
    for idx, block in enumerate(blocks):
        if not block.strip():
            continue
        name = None
        bus_id = None
        vendor_id = None
        product_id = None
        handlers: list[str] = []
        sysfs_path = None
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("I:"):
                m_bus = re.search(r"Bus=(\S+)", line)
                m_vendor = re.search(r"Vendor=(\S+)", line)
                m_product = re.search(r"Product=(\S+)", line)
                bus_id = m_bus.group(1) if m_bus else None
                vendor_id = m_vendor.group(1).lower() if m_vendor else None
                product_id = m_product.group(1).lower() if m_product else None
            elif line.startswith("N:"):
                m = re.search(r'Name="([^"]*)"', line)
                name = m.group(1) if m else None
            elif line.startswith("S:"):
                sysfs_path = line.split("=", 1)[-1].strip() or None
            elif line.startswith("H:"):
                handlers_str = line.split(":", 1)[-1].strip()
                handlers = [h for h in handlers_str.replace("Handlers=", "").split() if h]
        if name is None and vendor_id is None:
            continue
        devices.append(
            HardwareDevice(
                device_id=f"input:{idx}:{sysfs_path or name or idx}",
                device_class="input",
                subclass=bus_id,  # linux input.h BUS_* code, e.g. "0003" USB, "0011" i8042
                bus=Bus.INPUT,
                vendor_id=vendor_id,
                product_id=product_id,
                product_name=name,
                driver=HardwareDriverState(kernel_modules_loaded=tuple(handlers)),
                operational_status="detected" if name else "unknown",
                detection_confidence=0.8 if name else 0.3,
            )
        )
    return devices, missing


# --------------------------------------------------------------------------- Network

def collect_network_devices(
    *, sysfs_root: Path | None = None, runner: Runner = None
) -> tuple[list[HardwareDevice], list[str]]:
    """Enumerate ``/sys/class/net`` interfaces (no IP/MAC captured — see redaction)."""
    root = sysfs_root or Path("/")
    base = root / "sys" / "class" / "net"
    missing: list[str] = []
    if not base.exists():
        missing.append("sysfs:class_net")
        return [], missing
    devices: list[HardwareDevice] = []
    try:
        for entry in sorted(base.iterdir()):
            if entry.name == "lo":
                continue
            driver = None
            driver_link = entry / "device" / "driver"
            if driver_link.exists():
                try:
                    driver = driver_link.resolve().name
                except OSError:
                    pass
            wireless = (entry / "wireless").exists() or entry.name.startswith("wl")
            devices.append(
                HardwareDevice(
                    device_id=f"net:{entry.name}",
                    device_class="network",
                    subclass="wireless" if wireless else "wired",
                    bus=Bus.NETWORK,
                    product_name=entry.name,
                    driver=HardwareDriverState(kernel_driver_in_use=driver),
                    operational_status="detected",
                    detection_confidence=0.7,
                )
            )
    except OSError:
        missing.append("sysfs:class_net")
    return devices, missing


# --------------------------------------------------------------------------- Kernel driver state

def collect_kernel_driver_state(*, runner: Runner = None, raw_text: str | None = None) -> dict[str, Any]:
    """Parse ``lsmod`` output into a module → (size, used_by) mapping (sample-safe)."""
    text = raw_text
    missing: list[str] = []
    if text is None:
        text, available = _run_tool(["lsmod"], runner=runner)
        if not available:
            missing.append("lsmod")
            return {"modules": {}, "missing_tools": missing}
    modules: dict[str, dict[str, Any]] = {}
    lines = (text or "").splitlines()
    for line in lines[1:]:  # skip header
        parts = line.split()
        if len(parts) < 3:
            continue
        name, size, used_by = parts[0], parts[1], parts[2]
        modules[name] = {"size": size, "used_by_count": used_by}
    return {"modules": modules, "missing_tools": missing}


# --------------------------------------------------------------------------- Firmware errors

_FIRMWARE_ERROR_RE = re.compile(r"firmware", re.IGNORECASE)


def collect_firmware_errors(*, runner: Runner = None, raw_text: str | None = None) -> dict[str, Any]:
    """Scan ``dmesg`` (if readable) for firmware-related failure lines. Capped, no secrets."""
    text = raw_text
    missing: list[str] = []
    if text is None:
        text, available = _run_tool(["dmesg", "--ctime"], runner=runner)
        if not available:
            missing.append("dmesg")
            return {"missing_firmware_lines": [], "missing_tools": missing}
    lines = []
    for line in (text or "").splitlines():
        low = line.lower()
        if _FIRMWARE_ERROR_RE.search(low) and ("fail" in low or "not found" in low or "missing" in low):
            lines.append(line.strip()[:160])
    return {"missing_firmware_lines": lines[:20], "missing_tools": missing}


# --------------------------------------------------------------------------- Orchestration

def build_hardware_inventory_summary(inventory: HardwareInventory) -> dict[str, Any]:
    """Aggregate counts by device_class and operational_status (no raw device rows)."""
    by_class: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for dev in inventory.devices:
        by_class[dev.device_class] = by_class.get(dev.device_class, 0) + 1
        by_status[dev.operational_status] = by_status.get(dev.operational_status, 0) + 1
    return {
        "schema_version": "hardware-inventory-summary.v1",
        "run_id": inventory.run_id,
        "collected_at": inventory.collected_at,
        "platform_class": inventory.platform.platform_class,
        "architecture": inventory.platform.architecture,
        "is_raspberry_pi": inventory.platform.is_raspberry_pi,
        "device_count": len(inventory.devices),
        "device_count_by_class": by_class,
        "device_count_by_operational_status": by_status,
        "capability_missing_tools": list(inventory.capability_missing_tools),
    }


def collect_hardware_inventory(
    *,
    platform: PlatformIdentity | None = None,
    runner: Runner = None,
    run_id: str | None = None,
    pci_raw_text: str | None = None,
    usb_raw_text: str | None = None,
    input_raw_text: str | None = None,
    sysfs_root: Path | None = None,
) -> HardwareInventory:
    """Build a full, read-only HardwareInventory snapshot.

    ``platform`` should normally come from ``cpu_platform_detection`` /
    ``mainboard_chipset_detection`` (Phase 4); a minimal unknown placeholder is used
    here only when the caller does not supply one, so this module stays independently
    testable.
    """
    missing: list[str] = []
    pci_devices, pci_missing = collect_pci_devices(runner=runner, raw_text=pci_raw_text)
    usb_devices, usb_missing = collect_usb_devices(runner=runner, raw_text=usb_raw_text)
    platform_devices, platform_missing = collect_platform_devices(sysfs_root=sysfs_root)
    input_devices, input_missing = collect_input_devices(raw_text=input_raw_text, sysfs_root=sysfs_root)
    network_devices, network_missing = collect_network_devices(sysfs_root=sysfs_root, runner=runner)
    missing.extend(pci_missing + usb_missing + platform_missing + input_missing + network_missing)

    all_devices = [*pci_devices, *usb_devices, *platform_devices, *input_devices, *network_devices]

    return HardwareInventory(
        run_id=run_id or uuid.uuid4().hex,
        collected_at=_utc_now(),
        platform=platform or PlatformIdentity(platform_class="unknown"),
        devices=tuple(all_devices),
        capability_missing_tools=tuple(sorted(set(missing))),
    )


def write_hardware_inventory_evidence(
    inventory: HardwareInventory, *, evidence_root: Path | None = None
) -> dict[str, Path]:
    """Write inventory + summary JSON under docs/evidence/runtime-results/hardware/<run_id>/.

    Pure I/O helper — callers decide *when* to persist; detection/collection stays
    side-effect free so unit tests never touch disk.
    """
    import json

    root = evidence_root or Path("docs/evidence/runtime-results/hardware")
    out_dir = root / inventory.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = out_dir / "hardware_inventory.json"
    summary_path = out_dir / "hardware_inventory_summary.json"
    inventory_path.write_text(json.dumps(inventory.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    summary_path.write_text(
        json.dumps(build_hardware_inventory_summary(inventory), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return {"inventory_path": inventory_path, "summary_path": summary_path}


def build_hardware_inventory_diagnostics() -> dict[str, Any]:
    return {
        "inventory_version": HARDWARE_INVENTORY_VERSION,
        "module": "core.hardware_inventory",
        "collectors": [
            "collect_pci_devices",
            "collect_usb_devices",
            "collect_platform_devices",
            "collect_input_devices",
            "collect_network_devices",
            "collect_storage_controllers",
            "collect_kernel_driver_state",
            "collect_firmware_errors",
        ],
        "read_only": True,
        "writes_allowed": False,
        "apt_install_in_scan": False,
    }


__all__ = [
    "HARDWARE_INVENTORY_VERSION",
    "collect_pci_devices",
    "collect_usb_devices",
    "collect_platform_devices",
    "collect_input_devices",
    "collect_network_devices",
    "collect_storage_controllers",
    "collect_kernel_driver_state",
    "collect_firmware_errors",
    "build_hardware_inventory_summary",
    "collect_hardware_inventory",
    "write_hardware_inventory_evidence",
    "build_hardware_inventory_diagnostics",
]
