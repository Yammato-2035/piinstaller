"""Restore-Handoff-Preview v2 – konsolidierte Gates."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType

_REPO = Path(__file__).resolve().parents[2]
_CORE = _REPO / "apps" / "partitionshelfer" / "core"
_PKG = "setuphelfer_partitions_core_rh_v2"


def _load_mod(name: str, filename: str):
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


_handoff = _load_mod("restore_handoff_contract", "restore_handoff_contract.py")
_hardstop = _load_mod("partition_hardstop", "partition_hardstop.py")
_layout = _load_mod("manifest_layout_preview", "manifest_layout_preview.py")

build_partition_restore_handoff = _handoff.build_partition_restore_handoff
evaluate_partition_hardstops = _hardstop.evaluate_partition_hardstops
build_partition_hardstop_context = _hardstop.build_partition_hardstop_context
build_manifest_layout_preview = _layout.build_manifest_layout_preview


class TestRestoreHandoffPreviewV2(unittest.TestCase):
    def test_without_verify_review_required(self):
        hs = evaluate_partition_hardstops(
            build_partition_hardstop_context(target_device="/dev/sdd")
        )
        layout = build_manifest_layout_preview(
            {"kind": "setuphelfer-backup-manifest", "partitions": [{"device": "/dev/sdd1"}]}
        )
        h = build_partition_restore_handoff(
            hardstop_result=hs,
            manifest_layout_preview=layout,
            target_device="/dev/sdd",
        )
        self.assertIn(h["status"], ("review_required", "blocked"))
        self.assertIn("partition.handoff.verify_missing", h["codes"])
        self.assertFalse(h["restore_execution_allowed"])

    def test_hardstop_blocked_stays_blocked(self):
        hs = evaluate_partition_hardstops(
            build_partition_hardstop_context(
                target_device="/dev/sdb",
                backup_source_device="/dev/sdb",
            )
        )
        h = build_partition_restore_handoff(
            hardstop_result=hs,
            manifest_layout_preview={"status": "ok"},
            target_device="/dev/sdb",
            verify_evidence={"verified": True},
        )
        self.assertEqual(h["status"], "blocked")

    def test_execution_always_false(self):
        h = build_partition_restore_handoff(
            target_device="/dev/sde",
            verify_evidence={"verified": True},
        )
        self.assertFalse(h["restore_execution_allowed"])
        self.assertFalse(h["write_allowed"])

    def test_handoff_sources_for_rescue(self):
        h = build_partition_restore_handoff(
            target_device="/dev/sdf",
            backup_manifest_ref="/media/backup/job/MANIFEST.json",
        )
        self.assertIn("handoff_sources", h)
        self.assertIn("rescue_handoff_next", h)

    def test_api_handoff_endpoint(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from api.routes.partitions import partition_router

        app = FastAPI()
        app.include_router(partition_router, prefix="/api/partitions")
        client = TestClient(app)
        r = client.post(
            "/api/partitions/restore-handoff-preview",
            json={"target_device": "/dev/sdg"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["restore_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
