"""
Storage-Rollen-Klassifikation – Windows-NVMe und verwandte Fälle.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO = Path(__file__).resolve().parents[2]
_BACKEND = _REPO / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))
_CORE = _REPO / "apps" / "partitionshelfer" / "core"
_PKG = "setuphelfer_partitions_core_role_test"


def _load_core_module(name: str, filename: str) -> ModuleType:
    if _PKG not in sys.modules:
        pkg = ModuleType(_PKG)
        pkg.__path__ = [str(_CORE)]
        sys.modules[_PKG] = pkg
    path = _CORE / filename
    full = f"{_PKG}.{name}"
    spec = importlib.util.spec_from_file_location(full, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = _PKG
    sys.modules[full] = mod
    spec.loader.exec_module(mod)
    return mod


_hardstop = _load_core_module("partition_hardstop", "partition_hardstop.py")
evaluate_partition_hardstops = _hardstop.evaluate_partition_hardstops
build_partition_hardstop_context = _hardstop.build_partition_hardstop_context

from core.storage_role_classification import (  # noqa: E402
    classify_disk_storage_role,
    find_classification_for_target,
)


def _windows_disk(*, recovery: bool = True, ms_data: bool = True) -> dict:
    parts = [
        {
            "name": "nvme1n1p1",
            "size_bytes": 100_663_296,
            "fstype": "vfat",
            "mountpoint": None,
            "label": "EFI",
            "parttypename": "EFI System",
            "children": [],
        },
        {
            "name": "nvme1n1p2",
            "size_bytes": 16_106_127_360,
            "fstype": "ntfs",
            "mountpoint": None,
            "label": "Windows",
            "parttypename": "Microsoft basic data" if ms_data else "Basic data",
            "children": [],
        },
    ]
    if recovery:
        parts.append(
            {
                "name": "nvme1n1p3",
                "size_bytes": 1_073_741_824,
                "fstype": "ntfs",
                "mountpoint": None,
                "label": "Recovery",
                "parttypename": "Windows recovery environment",
                "children": [],
            }
        )
    return {
        "name": "nvme1n1",
        "size_bytes": 2_000_000_000_000,
        "size_human": "2 TB",
        "vendor": "Samsung",
        "model": "980 Pro",
        "display_name": "Samsung 980 Pro",
        "tran": "nvme",
        "removable": False,
        "partitions": parts,
    }


def test_efi_ntfs_recovery_windows_system_disk_high():
    disk = _windows_disk(recovery=True)
    r = classify_disk_storage_role(disk)
    assert r["role"] == "windows_system_disk"
    assert r["confidence"] in ("high", "medium")
    assert "efi_partition_detected" in r["evidence"]
    assert "ntfs_partition_detected" in r["evidence"]
    assert r["write_allowed"] is False
    assert r["risk_level"] == "red"


def test_efi_large_ntfs_without_recovery_still_windows():
    disk = _windows_disk(recovery=False, ms_data=True)
    r = classify_disk_storage_role(disk)
    assert r["role"] == "windows_system_disk"
    assert r["write_allowed"] is False


def test_ntfs_data_without_efi_not_windows_system():
    disk = {
        "name": "sdb",
        "size_bytes": 1_000_000_000_000,
        "partitions": [
            {
                "name": "sdb1",
                "size_bytes": 1_000_000_000_000,
                "fstype": "ntfs",
                "mountpoint": "/media/user/Data",
                "parttypename": "Microsoft basic data",
                "children": [],
            }
        ],
        "tran": "usb",
        "removable": True,
    }
    r = classify_disk_storage_role(disk)
    assert r["role"] != "windows_system_disk"
    assert r["role"] in ("external_data_disk", "backup_target", "unknown_disk")


def test_windows_system_disk_hardstop_code():
    disk = _windows_disk()
    role = classify_disk_storage_role(disk)
    ctx = build_partition_hardstop_context(
        target_device="/dev/nvme1n1",
        storage_classification=role,
    )
    ev = evaluate_partition_hardstops(ctx)
    assert ev["write_allowed"] is False
    assert "partition.hardstop.target_is_windows_system_disk" in ev["codes"]


def test_windows_system_disk_find_by_target():
    disk = _windows_disk()
    found = find_classification_for_target([disk], "/dev/nvme1n1p2")
    assert found is not None
    assert found["role"] == "windows_system_disk"
