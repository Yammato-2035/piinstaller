"""
Storage device discovery for the hardware baseline API — read-only.

PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 12.

Reuses ``core.storage_facade.list_physical_disk_paths`` for disk-level block
device listing (no re-implementation of ``lsblk`` parsing) and
``core.storage_health_normalizer`` for device-class classification and
block geometry. Raw SMART/NVMe attribute text is deliberately **not**
fetched here — the per-class baseline builders (``hdd_/sata_ssd_/
nvme_baseline_diagnostics``) perform their own live tool calls when no
fixture text is injected, keeping this module a thin, single-purpose
discovery step.

``is_system_disk`` is set conservatively (``False`` by default; the
orchestrator/gate treats an unknown role the same as "could be a system
disk" wherever that distinction matters) and ``is_rescue_stick`` detection
is out of scope for this phase (always ``False``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from core.storage_facade import list_physical_disk_paths
from core.storage_health_normalizer import classify_device_class, read_block_geometry

HARDWARE_BASELINE_STORAGE_DISCOVERY_VERSION = 1

Runner = Callable[..., Any] | None


def discover_storage_devices_for_baseline(
    *, runner: Runner = None, sysfs_root: Path | None = None
) -> list[dict[str, Any]]:
    """Return one dict per disk-level block device, ready to hand to
    ``rescue.hardware_baseline_orchestrator.run_hardware_baseline``'s
    ``storage_devices`` argument."""
    devices: list[dict[str, Any]] = []
    for dev_path in list_physical_disk_paths(runner=runner):
        name = dev_path[len("/dev/") :] if dev_path.startswith("/dev/") else dev_path
        device_class = classify_device_class(name, sysfs_root=sysfs_root)
        geometry = read_block_geometry(name, sysfs_root=sysfs_root)
        devices.append(
            {
                "device_id": name,
                "device_class": device_class,
                "capacity_bytes": geometry.get("capacity_bytes"),
                "logical_block_size": geometry.get("logical_block_size"),
                "read_only": geometry.get("read_only"),
                "removable": geometry.get("removable"),
                "is_system_disk": False,
                "is_rescue_stick": False,
            }
        )
    return devices


def build_hardware_baseline_storage_discovery_diagnostics() -> dict[str, Any]:
    return {
        "module_version": HARDWARE_BASELINE_STORAGE_DISCOVERY_VERSION,
        "module": "rescue.hardware_baseline_storage_discovery",
        "read_only": True,
        "fetches_smart_or_nvme_data": False,
    }


__all__ = [
    "HARDWARE_BASELINE_STORAGE_DISCOVERY_VERSION",
    "discover_storage_devices_for_baseline",
    "build_hardware_baseline_storage_discovery_diagnostics",
]
