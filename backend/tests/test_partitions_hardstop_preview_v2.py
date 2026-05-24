"""Hardstop-Preview v2 – Storage-Facade-Integration."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType

from fastapi import FastAPI
from fastapi.testclient import TestClient

_REPO = Path(__file__).resolve().parents[2]
_CORE = _REPO / "apps" / "partitionshelfer" / "core"
_PKG = "setuphelfer_partitions_core_hs_v2"


def _load_core(name: str, filename: str) -> ModuleType:
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


_hardstop = _load_core("partition_hardstop", "partition_hardstop.py")
build_partition_hardstop_context = _hardstop.build_partition_hardstop_context
evaluate_partition_hardstops = _hardstop.evaluate_partition_hardstops

from core.partition_storage_facade import build_partition_target_safety_context


class TestPartitionsHardstopPreviewV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from api.routes.partitions import partition_router

        app = FastAPI()
        app.include_router(partition_router, prefix="/api/partitions")
        cls.client = TestClient(app)

    def _eval_with_facade(self, target: str, **facade_kw):
        safety = build_partition_target_safety_context(target, **facade_kw)
        ctx = build_partition_hardstop_context(
            target_device=target,
            storage_classification=safety.get("storage_classification"),
        )
        ctx["storage_safety_context"] = safety
        return evaluate_partition_hardstops(ctx)

    def test_root_blocked(self):
        r = self._eval_with_facade("/")
        self.assertEqual(r["status"], "blocked")

    def test_system_disk_blocked(self):
        r = self._eval_with_facade(
            "/dev/sda",
            system_disk_hint=True,
        )
        self.assertEqual(r["status"], "blocked")
        self.assertIn("partition.hardstop.target_is_system_disk", r["codes"])

    def test_backup_source_same_disk_blocked(self):
        r = self._eval_with_facade("/dev/sdb", backup_source_device="/dev/sdb")
        ctx = build_partition_hardstop_context(
            target_device="/dev/sdb",
            backup_source_device="/dev/sdb",
        )
        r = evaluate_partition_hardstops(ctx)
        self.assertEqual(r["status"], "blocked")

    def test_operator_override_not_allowed(self):
        r = self._eval_with_facade("/dev/sdc", operator_override=True)
        self.assertIn(r["status"], ("review_required", "blocked"))
        self.assertFalse(r["write_allowed"])

    def test_api_hardstop_includes_storage_safety(self):
        res = self.client.get(
            "/api/partitions/hardstop-preview",
            params={"target_device": "/dev/sdz"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertFalse(body["write_allowed"])
        self.assertIn("storage_safety", body)

    def test_partitions_routes_no_forbidden_tokens(self):
        routes_src = (_REPO / "backend" / "api" / "routes" / "partitions.py").read_text(encoding="utf-8")
        for token in ("mkfs", "parted", "dd ", "mount ", "umount", "tar_extract"):
            self.assertNotIn(token, routes_src.lower())


if __name__ == "__main__":
    unittest.main()
