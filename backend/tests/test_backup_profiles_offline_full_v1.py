"""offline-full backup profile metadata."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.backup_profiles import (  # noqa: E402
    CANONICAL_BACKUP_RUNNER_MODULE,
    PROFILE_OFFLINE_FULL,
    get_backup_profile,
    logical_excluded_patterns,
    normalize_backup_profile,
)


class OfflineFullProfileTests(unittest.TestCase):
    def test_profile_exists(self) -> None:
        p = get_backup_profile(PROFILE_OFFLINE_FULL)
        self.assertFalse(p.get("unknown"))
        self.assertEqual(p["profile_id"], PROFILE_OFFLINE_FULL)

    def test_source_root_and_live_flags(self) -> None:
        p = get_backup_profile("offline-full")
        self.assertTrue(p["source_root_required"])
        self.assertFalse(p["requires_live_package_freeze"])
        self.assertFalse(p["requires_systemd_inhibit"])

    def test_manifest_and_sha256(self) -> None:
        p = get_backup_profile("offline-full")
        self.assertTrue(p["manifest_required"])
        self.assertTrue(p["sha256_required"])

    def test_default_excludes(self) -> None:
        p = get_backup_profile("offline-full")
        ex = p["default_excludes"]
        for needle in ("/proc", "/sys", "/dev", "/tmp", "/run", "/mnt", "/media", "/run/media"):
            self.assertIn(needle, ex)
        self.assertEqual(ex, logical_excluded_patterns(PROFILE_OFFLINE_FULL))

    def test_external_target_required(self) -> None:
        p = get_backup_profile("offline-full")
        self.assertTrue(p["write_target_must_be_external"])
        self.assertTrue(p["no_internal_drive_write_without_override"])

    def test_canonical_runner_constant(self) -> None:
        self.assertEqual(CANONICAL_BACKUP_RUNNER_MODULE, "backend.tools.backup_runner")

    def test_normalize_offline_full(self) -> None:
        prof, _ = normalize_backup_profile("offline-full")
        self.assertEqual(prof, PROFILE_OFFLINE_FULL)


if __name__ == "__main__":
    unittest.main()
