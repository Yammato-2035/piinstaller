"""Storage-Facade für Partitionshelfer (read-only)."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from core.partition_storage_facade import (
    build_partition_target_safety_context,
    read_backup_manifest_readonly,
)

_REPO = Path(__file__).resolve().parents[2]
_FORBIDDEN = ("mkfs", "parted", "dd ", "mount ", "umount", "tar_extract", "rsync")


class TestPartitionStorageFacadeV1(unittest.TestCase):
    def test_known_disk_normalized_readonly(self):
        ctx = build_partition_target_safety_context("/dev/sdz")
        self.assertEqual(ctx["normalized_target"], "/dev/sdz")
        self.assertFalse(ctx["write_allowed"])
        self.assertEqual(ctx["decision_source"], "core_storage_facade")

    def test_unknown_device_blocked_or_review(self):
        insp = {
            "storage": {
                "devices_classified": [],
                "devices_raw": [],
                "blkid": [],
            }
        }
        ctx = build_partition_target_safety_context(
            "/dev/unknowndisk99",
            inspect_result=insp,
        )
        self.assertIn(ctx["status"], ("blocked", "review_required"))
        self.assertFalse(ctx["write_allowed"])

    def test_write_allowed_always_false(self):
        ctx = build_partition_target_safety_context(
            "/dev/sda",
            operator_override=True,
            system_disk_hint=True,
        )
        self.assertFalse(ctx["write_allowed"])

    def test_system_path_blocked(self):
        ctx = build_partition_target_safety_context("/tmp")
        self.assertEqual(ctx["status"], "blocked")
        codes = [h["code"] for h in ctx["hardstops"]]
        self.assertTrue(any("system_path" in c or "live_root" in c for c in codes))

    def test_media_not_blanket_allowed(self):
        ctx = build_partition_target_safety_context("/media/user/usb")
        self.assertIn(ctx["status"], ("review_required", "blocked"))
        warn_codes = [w["code"] for w in ctx["warnings"]]
        self.assertIn("partition.facade.media_mount_not_auto_allowed", warn_codes)

    def test_operator_override_never_allowed(self):
        ctx = build_partition_target_safety_context(
            "/dev/sdb",
            operator_override=True,
        )
        self.assertFalse(ctx["write_allowed"])
        warn_codes = [w["code"] for w in ctx["warnings"]]
        self.assertIn("partition.facade.operator_override_never_allowed", warn_codes)

    def test_no_forbidden_tokens_in_facade_source(self):
        src = (Path(__file__).resolve().parents[1] / "core" / "partition_storage_facade.py").read_text(
            encoding="utf-8"
        )
        skip_fragments = ("ohne mount", "kein archiv-extract", '"""', '"message":')
        for line in src.splitlines():
            lower = line.lower()
            if any(s in lower for s in skip_fragments):
                continue
            for token in _FORBIDDEN:
                self.assertNotIn(token, lower, msg=f"{token!r} in line: {line}")

    def test_read_manifest_allowlisted(self):
        with patch(
            "core.partition_storage_facade.write_safe_prefixes_resolved",
            return_value=(Path("/tmp/allow").resolve(),),
        ):
            allow_dir = Path("/tmp/allow")
            allow_dir.mkdir(parents=True, exist_ok=True)
            mf = allow_dir / "MANIFEST.json"
            mf.write_text('{"kind":"setuphelfer-backup-manifest","partitions":[]}', encoding="utf-8")
            data, err = read_backup_manifest_readonly(str(mf))
            self.assertIsNone(err)
            self.assertIsInstance(data, dict)
            mf.unlink(missing_ok=True)

    def test_read_manifest_rejects_traversal(self):
        data, err = read_backup_manifest_readonly("/tmp/../etc/passwd")
        self.assertIsNone(data)
        self.assertIn(err, ("path_traversal", "not_manifest_filename", "path_not_allowlisted"))


if __name__ == "__main__":
    unittest.main()
