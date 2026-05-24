"""Manifest-Layout-Preview v2 – inline und read-only Datei."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

_REPO = Path(__file__).resolve().parents[2]
_CORE = _REPO / "apps" / "partitionshelfer" / "core"
_PKG = "setuphelfer_partitions_core_ml_v2"


def _load_layout():
    if _PKG not in sys.modules:
        pkg = ModuleType(_PKG)
        pkg.__path__ = [str(_CORE)]
        sys.modules[_PKG] = pkg
    path = _CORE / "manifest_layout_preview.py"
    full = f"{_PKG}.manifest_layout_preview"
    spec = importlib.util.spec_from_file_location(full, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = _PKG
    sys.modules[full] = mod
    spec.loader.exec_module(mod)
    return mod


_layout = _load_layout()
build_manifest_layout_preview = _layout.build_manifest_layout_preview

from core.partition_storage_facade import read_backup_manifest_readonly


class TestManifestLayoutPreviewV2(unittest.TestCase):
    def test_null_manifest_unavailable(self):
        p = build_manifest_layout_preview(None)
        self.assertEqual(p["status"], "unavailable")
        self.assertFalse(p["write_allowed"])
        self.assertEqual(p["manifest_source"], "null")

    def test_inline_manifest_ok(self):
        manifest = {
            "kind": "setuphelfer-backup-manifest",
            "partitions": [{"device": "/dev/sda1", "size": "512M", "fs_type": "ext4"}],
        }
        p = build_manifest_layout_preview(manifest, "/dev/sda")
        self.assertIn(p["status"], ("ok", "review_required"))
        self.assertGreaterEqual(len(p["original_layout"]), 1)
        self.assertIn("layout", p)

    def test_file_readonly_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            mf = Path(td) / "MANIFEST.json"
            mf.write_text(
                '{"kind":"setuphelfer-backup-manifest","partitions":[{"device":"/dev/sdb1","size":"1G"}]}',
                encoding="utf-8",
            )
            with patch(
                "core.partition_storage_facade.write_safe_prefixes_resolved",
                return_value=(Path(td).resolve(),),
            ):
                p = build_manifest_layout_preview(
                    None,
                    "/dev/sdb",
                    manifest_path=str(mf),
                    manifest_reader=read_backup_manifest_readonly,
                )
            self.assertEqual(p["manifest_source"], "file_readonly")
            self.assertIn(p["status"], ("ok", "review_required"))

    def test_invalid_manifest_review_or_blocked(self):
        p = build_manifest_layout_preview({"kind": "other", "partitions": []})
        self.assertIn(p["status"], ("review_required", "blocked", "ok"))

    def test_boot_efi_missing_review_required(self):
        manifest = {
            "kind": "setuphelfer-backup-manifest",
            "partitions": [{"device": "/dev/sda1", "size": "10G", "fs_type": "ext4"}],
        }
        p = build_manifest_layout_preview(manifest)
        self.assertIn(p["status"], ("ok", "review_required"))
        if p["status"] == "review_required":
            codes = [w.get("code") for w in p.get("warnings") or []]
            self.assertTrue(
                any("boot_efi" in str(c) for c in codes)
                or any("boot_efi" in str(c) for c in (p.get("compatibility") or {}).get("warnings", []))
            )

    def test_no_tar_extract_in_source(self):
        src = (_CORE / "manifest_layout_preview.py").read_text(encoding="utf-8")
        self.assertNotIn("tar_extract", src.lower())
        self.assertNotIn("extractall", src.lower())


if __name__ == "__main__":
    unittest.main()
