"""
Partitionshelfer Phase 2 – Safety Contracts (read-only, keine Writes).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_REPO = Path(__file__).resolve().parents[2]
_CORE = _REPO / "apps" / "partitionshelfer" / "core"
_PKG = "setuphelfer_partitions_core_test"


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
_layout = _load_core_module("manifest_layout_preview", "manifest_layout_preview.py")
_handoff = _load_core_module("restore_handoff_contract", "restore_handoff_contract.py")

build_partition_hardstop_context = _hardstop.build_partition_hardstop_context
evaluate_partition_hardstops = _hardstop.evaluate_partition_hardstops
build_manifest_layout_preview = _layout.build_manifest_layout_preview
build_partition_restore_handoff = _handoff.build_partition_restore_handoff

_FORBIDDEN = (
    "mkfs",
    "parted",
    "sfdisk",
    "sgdisk",
    "wipefs",
    "dd if=",
    "dd of=",
    "mount ",
    "umount",
)


@pytest.fixture
def api_client():
    from api.routes.partitions import partition_router

    app = FastAPI()
    app.include_router(partition_router, prefix="/api/partitions")
    return TestClient(app)


def _ctx(**kwargs):
    return build_partition_hardstop_context(**kwargs)


def _eval(**kwargs):
    ctx = _ctx(**kwargs)
    return evaluate_partition_hardstops(ctx)


def test_target_equals_backup_source_blocked():
    r = _eval(target_device="/dev/sdb", backup_source_device="/dev/sdb")
    assert r["status"] == "blocked"
    assert "partition.hardstop.partition_target_is_backup_source" in r["codes"]


def test_missing_target_blocked():
    r = _eval(target_device="")
    assert r["status"] == "blocked"
    assert "partition.hardstop.target_missing" in r["codes"]


def test_smart_failing_blocked():
    r = _eval(
        target_device="/dev/sdc",
        smart_summary={"state": "FAILED", "risk_code": "rescue.smart.critical"},
    )
    assert r["status"] == "blocked"
    assert "partition.hardstop.smart_failing" in r["codes"]


def test_smart_yellow_review_required():
    r = _eval(
        target_device="/dev/sdc",
        smart_summary={"state": "WARNING", "risk_code": "rescue.smart.warning"},
    )
    assert r["status"] == "review_required"
    assert "partition.warning.smart_yellow" in r["codes"]


def test_unknown_smart_review_required():
    r = _eval(target_device="/dev/sdc", smart_summary={"state": "UNKNOWN"})
    assert r["status"] == "review_required"
    assert "partition.warning.manual_review_required" in r["codes"]


def test_system_disk_classification_blocked():
    r = _eval(
        target_device="/dev/sda",
        storage_classification={"system_disk": True},
    )
    assert r["status"] == "blocked"
    assert "partition.hardstop.target_is_system_disk" in r["codes"]


def test_manifest_layout_without_manifest_unavailable():
    p = build_manifest_layout_preview(None)
    assert p["status"] == "unavailable"
    assert p["write_allowed"] is False


def test_manifest_layout_simple_ok():
    manifest = {
        "kind": "setuphelfer-backup-manifest",
        "partitions": [
            {
                "device": "/dev/sda1",
                "size": "512M",
                "fs_type": "vfat",
                "mountpoint": "/boot/efi",
            }
        ],
    }
    p = build_manifest_layout_preview(manifest, "/dev/sda")
    assert p["status"] == "ok"
    assert len(p["original_layout"]) >= 1
    assert p["write_allowed"] is False


def test_restore_handoff_blocked_when_hardstop_blocked():
    hs = _eval(target_device="/dev/sdb", backup_source_device="/dev/sdb")
    h = build_partition_restore_handoff(
        hardstop_result=hs,
        manifest_layout_preview={"status": "ok"},
        target_device="/dev/sdb",
    )
    assert h["status"] == "blocked"
    assert "partition.handoff.blocked_by_hardstop" in h["codes"]
    assert h["restore_execution_allowed"] is False


def test_restore_handoff_ready_without_auto_restore():
    hs = _eval(target_device="/dev/sdd", smart_summary={"state": "OK"})
    layout = build_manifest_layout_preview(
        {"partitions": [{"device": "/dev/sdd1", "size": "1G"}]},
        "/dev/sdd",
    )
    h = build_partition_restore_handoff(
        hardstop_result=hs,
        manifest_layout_preview=layout,
        target_device="/dev/sdd",
    )
    assert h["status"] in ("ready", "review_required")
    assert h["restore_execution_allowed"] is False
    assert h["recommended_next_step"] == "restore_preview_only"
    assert "BACKUP_BEFORE_OVERWRITE_GATE" in h["required_next_gates"]


def test_all_phase2_functions_write_allowed_false():
    ctx = _ctx(target_device="/dev/sde")
    ev = evaluate_partition_hardstops(ctx)
    layout = build_manifest_layout_preview({"partitions": []})
    handoff = build_partition_restore_handoff(
        hardstop_result=ev,
        manifest_layout_preview=layout,
        target_device="/dev/sde",
    )
    assert ctx["write_allowed"] is False
    assert ev["write_allowed"] is False
    assert layout["write_allowed"] is False
    assert handoff["write_allowed"] is False


@pytest.mark.parametrize("filename", [
    "partition_hardstop.py",
    "manifest_layout_preview.py",
    "restore_handoff_contract.py",
])
def test_core_files_have_no_forbidden_write_tokens(filename: str):
    src = (_CORE / filename).read_text(encoding="utf-8")
    skip_fragments = (
        "_write_actions",
        "_parse_sfdisk",
        "partition_layout_sfdisk_d",
        '"mkfs"',
        '"parted"',
        '"sfdisk"',
    )
    for line in src.splitlines():
        lower = line.lower()
        if any(s in lower for s in skip_fragments):
            continue
        for token in _FORBIDDEN:
            assert token not in lower, f"{filename} Zeile enthält verbotenes Token: {token!r}\n{line}"


def test_api_hardstop_preview_endpoint(api_client):
    r = api_client.get(
        "/api/partitions/hardstop-preview",
        params={"target_device": "/dev/sdz"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["write_allowed"] is False
    assert "evaluation" in body


def test_api_manifest_layout_preview_endpoint(api_client):
    r = api_client.post(
        "/api/partitions/manifest-layout-preview",
        json={"manifest": {"partitions": [{"device": "/dev/sda1"}]}},
    )
    assert r.status_code == 200
    assert r.json()["write_allowed"] is False


def test_openapi_lists_phase2_paths(api_client):
    paths = api_client.app.openapi().get("paths", {})
    assert "/api/partitions/hardstop-preview" in paths
    assert "/api/partitions/manifest-layout-preview" in paths
    assert "/api/partitions/restore-handoff-preview" in paths
