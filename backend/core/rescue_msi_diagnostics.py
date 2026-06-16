"""
Rescue MSI read-only hardware diagnostics (Phase R.3).

No destructive commands, no rw mounts, no writes to internal disks.
"""

from __future__ import annotations

import json
import platform
import re
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from core.rescue_boot_logger import collect_bootloader_context
from core.rescue_persistence import Runner, write_rescue_json_evidence, write_rescue_text_evidence
from core.safe_device import list_classified_devices

RESCUE_MSI_DIAGNOSTICS_VERSION = 3


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_text(path: str | Path, *, limit: int = 256) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()[:limit]
    except OSError:
        return ""


def _run_capture(cmd: str, *, runner: Callable[..., Any] | None = None, timeout: int = 8) -> tuple[int, str]:
    if runner is not None:
        proc = runner(cmd.split(), capture_output=True, text=True, timeout=timeout, check=False)
        return int(proc.returncode), (proc.stdout or "")[:12000]
    import subprocess

    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, check=False)
    return proc.returncode, (proc.stdout or "")[:12000]


def _dmi_fields() -> dict[str, str | None]:
    base = Path("/sys/class/dmi/id")
    keys = (
        "sys_vendor",
        "product_name",
        "product_version",
        "board_vendor",
        "board_name",
        "bios_vendor",
        "bios_version",
        "bios_date",
        "chassis_vendor",
        "chassis_type",
    )
    out: dict[str, str | None] = {}
    for key in keys:
        val = _read_text(base / key)
        out[key] = val or None
    return out


def _is_msi_vendor(vendor: str) -> bool:
    v = (vendor or "").lower()
    return "msi" in v or "micro-star" in v or "micro star" in v


def collect_msi_hardware_snapshot(*, runner: Runner = None) -> dict[str, Any]:
    """Read-only hardware snapshot suitable for MSI investigation."""
    bl = collect_bootloader_context(runner=runner)
    dmi = _dmi_fields()
    vendor = dmi.get("sys_vendor") or ""
    is_msi = _is_msi_vendor(vendor)

    devices: list[dict[str, Any]] = []
    try:
        for dev in list_classified_devices(runner=runner):
            devices.append(
                {
                    "id": getattr(dev, "id", None),
                    "name": getattr(dev, "name", None),
                    "type": getattr(dev, "type", None),
                    "size": getattr(dev, "size", None),
                    "removable": getattr(dev, "removable", None),
                    "mountpoints": list(getattr(dev, "mountpoints", []) or []),
                    "filesystems": list(getattr(dev, "filesystems", []) or []),
                    "is_system_disk": getattr(dev, "is_system_disk", None),
                    "is_boot_disk": getattr(dev, "is_boot_disk", None),
                    "is_foreign_os_disk": getattr(dev, "is_foreign_os_disk", None),
                    "is_write_allowed": getattr(dev, "is_write_allowed", None),
                }
            )
    except Exception as exc:
        devices = [{"error": str(exc)}]

    partitions: list[dict[str, str]] = []
    from core.storage_facade import build_storage_inventory_snapshot

    snap = build_storage_inventory_snapshot(runner=runner, mode="rescue", include_tree_devices=True)
    tree = snap.get("lsblk_tree") or []

    def walk(nodes: list[Any]) -> None:
        for n in nodes:
            if not isinstance(n, dict):
                continue
            if n.get("type") == "part":
                partitions.append(
                    {
                        "name": str(n.get("name") or ""),
                        "fstype": str(n.get("fstype") or ""),
                        "size": str(n.get("size") or ""),
                        "mountpoints": json.dumps(n.get("mountpoints") or n.get("mountpoint")),
                    }
                )
            walk(n.get("children") or [])

    if isinstance(tree, list) and tree:
        walk(tree)
    else:
        for row in snap.get("lsblk_rows") or []:
            if isinstance(row, dict) and row.get("type") == "part":
                partitions.append(
                    {
                        "name": str(row.get("name") or ""),
                        "fstype": str(row.get("fstype") or ""),
                        "size": str(row.get("size") or ""),
                        "mountpoints": json.dumps(row.get("mountpoints") or row.get("mountpoint")),
                    }
                )

    bitlocker_hints: list[str] = []
    for p in partitions:
        fst = (p.get("fstype") or "").lower()
        if "bitlocker" in fst or fst in ("BitLocker",):
            bitlocker_hints.append(p.get("name", ""))

    network_adapters: list[str] = []
    rc, ip_out = _run_capture("ip -o link show 2>/dev/null", runner=runner, timeout=5)
    if rc == 0:
        network_adapters = [ln.strip() for ln in ip_out.splitlines() if ln.strip()][:32]

    wlan_adapters: list[str] = []
    rc, iw_out = _run_capture("iw dev 2>/dev/null", runner=runner, timeout=5)
    if rc == 0:
        wlan_adapters = re.findall(r"Interface\s+(\S+)", iw_out)

    smart_readonly: list[dict[str, str]] = []
    for dev in devices[:8]:
        dev_id = str(dev.get("id") or "")
        if not dev_id.startswith("/dev/"):
            continue
        rc2, smart_out = _run_capture(f"smartctl -H -n standby {dev_id} 2>/dev/null | head -5", runner=runner, timeout=6)
        if rc2 == 0 and smart_out.strip():
            smart_readonly.append({"device": dev_id, "summary": smart_out.strip()[:500]})

    mem_bytes = None
    try:
        mem_bytes = Path("/proc/meminfo").read_text(encoding="utf-8")
        m = re.search(r"MemTotal:\s+(\d+)", mem_bytes)
        mem_total_kb = int(m.group(1)) if m else None
    except OSError:
        mem_total_kb = None

    return {
        "schema_version": 1,
        "collected_at": _utc_now(),
        "hostname": socket.gethostname(),
        "is_msi_candidate": is_msi,
        "dmi": dmi,
        "bootloader": bl,
        "cpu_count": platform.processor() or None,
        "machine": platform.machine(),
        "memory_total_kb": mem_total_kb,
        "block_devices": devices,
        "partitions_readonly": partitions,
        "bitlocker_hints": bitlocker_hints,
        "network_adapters": network_adapters,
        "wlan_adapters": wlan_adapters,
        "smart_readonly": smart_readonly,
        "windows_bootloader_hints": [
            p for p in partitions if (p.get("fstype") or "").lower() in ("ntfs", "vfat", "msdos")
        ][:12],
        "linux_install_hints": [
            p for p in partitions if (p.get("fstype") or "").lower() in ("ext4", "ext3", "btrfs", "xfs")
        ][:12],
        "policy": {
            "internal_writes": False,
            "destructive_commands": False,
            "rw_mounts": False,
        },
    }


def write_msi_diagnostics_evidence(*, runner: Runner = None) -> dict[str, Any]:
    snap = collect_msi_hardware_snapshot(runner=runner)
    json_result = write_rescue_json_evidence("hardware", "msi_diagnostics_latest.json", snap, runner=runner)
    lines = [
        f"collected_at: {snap.get('collected_at')}",
        f"msi_candidate: {snap.get('is_msi_candidate')}",
        f"vendor: {(snap.get('dmi') or {}).get('sys_vendor')}",
        f"product: {(snap.get('dmi') or {}).get('product_name')}",
        f"devices: {len(snap.get('block_devices') or [])}",
        f"partitions: {len(snap.get('partitions_readonly') or [])}",
        f"bitlocker_hints: {len(snap.get('bitlocker_hints') or [])}",
    ]
    text_result = write_rescue_text_evidence("hardware", "msi_diagnostics_latest.md", "\n".join(lines), runner=runner)
    return {"status": "ok", "snapshot": snap, "json": json_result, "text": text_result}


def build_rescue_msi_diagnostics_diagnostics() -> dict[str, Any]:
    return {
        "msi_diagnostics_version": RESCUE_MSI_DIAGNOSTICS_VERSION,
        "module": "core.rescue_msi_diagnostics",
        "public_functions": [
            "collect_msi_hardware_snapshot",
            "write_msi_diagnostics_evidence",
            "build_rescue_msi_diagnostics_diagnostics",
        ],
        "destructive_commands": False,
        "rw_mounts": False,
    }
