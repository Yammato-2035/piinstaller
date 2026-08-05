"""
Storage device class + block geometry normalizer — read-only.

PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 6.

Determines the *device class* (rotational HDD, non-rotational SATA/SAS SSD,
NVMe, USB bridge, virtual, unknown) from sysfs, and reads basic block
geometry (sector sizes, capacity, read-only/removable flags). This is a
new, low-level sysfs reader — it does not duplicate ``core.storage_facade``
(which is ``lsblk``/``blkid``-oriented device *listing*, not per-device
class/geometry classification).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

STORAGE_HEALTH_NORMALIZER_VERSION = 1

_VIRTUAL_DEVICE_PREFIXES = ("loop", "dm-", "md", "zram", "sr")


def _read_sysfs_text(path: Path) -> str | None:
    try:
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return None


def _read_sysfs_int(path: Path) -> int | None:
    text = _read_sysfs_text(path)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def is_virtual_device_name(device_name: str) -> bool:
    return any(device_name.startswith(p) for p in _VIRTUAL_DEVICE_PREFIXES)


def is_usb_backed_device(device_name: str, *, sysfs_root: Path | None = None) -> bool:
    """Best-effort: resolve the device's sysfs symlink and check whether the
    real path traverses a ``usb`` bus node. False (not an error) when the
    device or its ``device`` symlink does not exist."""
    root = sysfs_root or Path("/")
    device_link = root / "sys" / "block" / device_name / "device"
    try:
        if not device_link.exists():
            return False
        real = device_link.resolve()
        return "/usb" in str(real) or "usb" in real.parts
    except OSError:
        return False


def classify_device_class(device_name: str, *, sysfs_root: Path | None = None) -> str:
    """rotational|non_rotational|nvme|usb_bridge|virtual|unknown."""
    if is_virtual_device_name(device_name):
        return "virtual"
    if device_name.startswith("nvme"):
        return "nvme"

    root = sysfs_root or Path("/")
    block_dir = root / "sys" / "block" / device_name
    if not block_dir.exists():
        return "unknown"

    if is_usb_backed_device(device_name, sysfs_root=sysfs_root):
        return "usb_bridge"

    rotational = _read_sysfs_int(block_dir / "queue" / "rotational")
    if rotational is None:
        return "unknown"
    return "rotational" if rotational == 1 else "non_rotational"


def read_block_geometry(device_name: str, *, sysfs_root: Path | None = None) -> dict[str, Any]:
    """Read logical/physical block size, sector count, read-only and
    removable flags. Missing sysfs entries yield ``None`` fields, never a
    fabricated default."""
    root = sysfs_root or Path("/")
    block_dir = root / "sys" / "block" / device_name
    queue_dir = block_dir / "queue"

    logical_block_size = _read_sysfs_int(queue_dir / "logical_block_size")
    physical_block_size = _read_sysfs_int(queue_dir / "physical_block_size")
    size_sectors = _read_sysfs_int(block_dir / "size")
    read_only_raw = _read_sysfs_int(block_dir / "ro")
    removable_raw = _read_sysfs_int(block_dir / "removable")

    capacity_bytes = None
    if size_sectors is not None:
        # Linux always reports /sys/block/<dev>/size in 512-byte sectors,
        # regardless of the device's actual logical_block_size.
        capacity_bytes = size_sectors * 512

    return {
        "logical_block_size": logical_block_size,
        "physical_block_size": physical_block_size,
        "size_sectors_512": size_sectors,
        "capacity_bytes": capacity_bytes,
        "read_only": bool(read_only_raw) if read_only_raw is not None else None,
        "removable": bool(removable_raw) if removable_raw is not None else None,
    }


def build_storage_health_normalizer_diagnostics() -> dict[str, Any]:
    return {
        "module_version": STORAGE_HEALTH_NORMALIZER_VERSION,
        "module": "core.storage_health_normalizer",
        "read_only": True,
        "writes_allowed": False,
    }


__all__ = [
    "STORAGE_HEALTH_NORMALIZER_VERSION",
    "is_virtual_device_name",
    "is_usb_backed_device",
    "classify_device_class",
    "read_block_geometry",
    "build_storage_health_normalizer_diagnostics",
]
