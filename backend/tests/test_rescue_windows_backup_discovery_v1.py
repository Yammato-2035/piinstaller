"""Windows backup discovery grouping + auto-selection (MSI root-cause fix)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_BACKEND = _REPO / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from core.rescue_backup_plan_contract import build_rescue_full_backup_plan  # noqa: E402
from core.rescue_disk_role_classifier import validate_source_target_pair  # noqa: E402
from core.rescue_storage_discovery import (  # noqa: E402
    build_system_source_candidates,
    discover_rescue_storage,
    pick_auto_backup_source,
)


def _msi_windows_tree() -> list[dict]:
    return [
        {
            "name": "nvme0n1",
            "path": "/dev/nvme0n1",
            "type": "disk",
            "size": 1_000_000_000_000,
            "fstype": "",
            "label": "",
            "mountpoints": [None],
            "tran": "nvme",
            "rm": False,
            "model": "Samsung 970",
            "children": [
                {
                    "name": "nvme0n1p1",
                    "path": "/dev/nvme0n1p1",
                    "type": "part",
                    "size": 100_663_296,
                    "fstype": "vfat",
                    "label": "EFI",
                    "mountpoints": [None],
                    "tran": "nvme",
                    "rm": False,
                },
                {
                    "name": "nvme0n1p3",
                    "path": "/dev/nvme0n1p3",
                    "type": "part",
                    "size": 500_000_000_000,
                    "fstype": "ntfs",
                    "label": "Windows",
                    "mountpoints": [None],
                    "tran": "nvme",
                    "rm": False,
                },
                {
                    "name": "nvme0n1p4",
                    "path": "/dev/nvme0n1p4",
                    "type": "part",
                    "size": 1_000_000_000,
                    "fstype": "ntfs",
                    "label": "Recovery",
                    "mountpoints": [None],
                    "tran": "nvme",
                    "rm": False,
                },
            ],
        },
        {
            "name": "sda",
            "path": "/dev/sda",
            "type": "disk",
            "size": 32_000_000_000,
            "fstype": "",
            "label": "SETUPHELFER",
            "mountpoints": [None],
            "tran": "usb",
            "rm": True,
            "children": [
                {
                    "name": "sda1",
                    "path": "/dev/sda1",
                    "type": "part",
                    "size": 8_000_000_000,
                    "fstype": "vfat",
                    "label": "SETUPHELFER",
                    "mountpoints": ["/run/live/medium"],
                    "tran": "usb",
                    "rm": True,
                }
            ],
        },
        {
            "name": "sdb",
            "path": "/dev/sdb",
            "type": "disk",
            "size": 2_000_000_000_000,
            "fstype": "",
            "label": "BACKUP",
            "mountpoints": [None],
            "tran": "usb",
            "rm": True,
        },
    ]


def test_windows_system_grouping_efi_windows_recovery():
    tree = _msi_windows_tree()
    classified = []
    for node in tree:
        disk_role = "windows_system_disk" if node["path"] == "/dev/nvme0n1" else "rescue_usb_stick"
        classified.append(
            {
                "path": node["path"],
                "type": "disk",
                "role": disk_role,
                "size": node["size"],
                "size_bytes": node["size"],
                "tran": node.get("tran"),
                "model": node.get("model"),
            }
        )
        for child in node.get("children") or []:
            part_role = disk_role if node["path"] == "/dev/nvme0n1" else "rescue_usb_stick"
            classified.append(
                {
                    **child,
                    "parent_path": node["path"],
                    "role": part_role,
                    "size_bytes": child["size"],
                }
            )
    groups = build_system_source_candidates(classified)
    assert len(groups) == 1
    group = groups[0]
    assert group["path"] == "/dev/nvme0n1"
    assert group["type"] == "system_group"
    assert group["group_kind"] == "windows_system"
    assert set(group["tags"]) == {"efi", "recovery", "windows"}
    assert group["auto_select_score"] == 100
    assert group["recommended"] is True


def test_discover_prefers_windows_system_over_rescue_usb(monkeypatch):
    monkeypatch.setattr("core.rescue_storage_discovery._lsblk_tree", lambda: _msi_windows_tree())
    monkeypatch.setattr("core.rescue_storage_discovery._blkid_type_map", lambda: {})

    out = discover_rescue_storage()
    pick = pick_auto_backup_source(out)
    assert pick is not None
    assert pick["path"] == "/dev/nvme0n1"
    assert pick["type"] == "system_group"
    source_paths = {d["path"] for d in out["source_candidates"]}
    assert "/dev/nvme0n1" in source_paths
    assert "/dev/nvme0n1p3" not in source_paths
    assert "/dev/sda1" not in source_paths
    assert "/dev/sdb" in {d["path"] for d in out["target_candidates"]}


def test_validate_source_target_honors_explicit_windows_role():
    pair = validate_source_target_pair(
        {"path": "/dev/nvme0n1", "role": "windows_system_disk", "type": "system_group"},
        {"path": "/dev/sdb", "label": "BACKUP", "tran": "usb", "type": "disk"},
    )
    assert pair["source_role"] == "windows_system_disk"
    assert pair["ok"] is True
    assert not any(e["code"] == "source_unknown" for e in pair["errors"])


def test_full_backup_plan_ready_with_grouped_source():
    body = {
        "source_device": "/dev/nvme0n1",
        "source_role": "windows_system_disk",
        "source_type": "system_group",
        "source_size_bytes": 1_000_000_000_000,
        "source_fstype": "multi",
        "target_device": "/dev/sdb",
        "target_mount": "/media/backup",
        "target_label": "BACKUP",
        "target_tran": "usb",
        "free_bytes": 3_000_000_000_000,
        "backup_mode": "auto",
        "encryption_requested": False,
        "verify_requested": True,
        "operator_confirm_source": True,
        "operator_confirm_target": True,
        "operator_confirm_no_restore": True,
        "operator_confirm_no_wipe": True,
        "booted_from_rescue": True,
    }
    plan = build_rescue_full_backup_plan(body)
    assert not any(e.get("code") == "source_unknown" for e in plan.get("errors") or [])
    assert not any(e.get("code") == "source_ambiguous" for e in plan.get("errors") or [])
    assert plan.get("source", {}).get("device") == "/dev/nvme0n1"
    assert plan.get("source", {}).get("scope") == "system_disk"
