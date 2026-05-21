"""offline-full-restore-preview profile metadata."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.restore_profiles import (  # noqa: E402
    CANONICAL_RESTORE_PREVIEW_MODULE,
    CANONICAL_VERIFY_MODULE,
    PROFILE_OFFLINE_FULL_RESTORE_PREVIEW,
    canonical_restore_preview_available,
    canonical_verify_available,
    get_restore_profile,
)


class RestoreProfilesOfflinePreviewTests(unittest.TestCase):
    def test_profile_exists(self) -> None:
        p = get_restore_profile(PROFILE_OFFLINE_FULL_RESTORE_PREVIEW)
        self.assertFalse(p.get("unknown"))
        self.assertEqual(p["profile_id"], PROFILE_OFFLINE_FULL_RESTORE_PREVIEW)

    def test_execution_not_allowed(self) -> None:
        p = get_restore_profile("offline-full-restore-preview")
        self.assertFalse(p["execution_allowed"])

    def test_requirements(self) -> None:
        p = get_restore_profile("offline-full-restore-preview")
        self.assertTrue(p["requires_manifest"])
        self.assertTrue(p["requires_archive"])
        self.assertTrue(p["requires_verify_before_restore"])
        self.assertTrue(p["requires_target_write_approval"])
        self.assertTrue(p["requires_backup_before_overwrite"])

    def test_forbidden_actions(self) -> None:
        forbidden = get_restore_profile("offline-full-restore-preview")["forbidden_actions"]
        for action in (
            "tar_extract",
            "mkfs",
            "parted",
            "mount_rw",
            "bootloader_write",
        ):
            self.assertIn(action, forbidden)

    def test_canonical_modules_available(self) -> None:
        self.assertTrue(canonical_restore_preview_available())
        self.assertTrue(canonical_verify_available())
        self.assertEqual(CANONICAL_RESTORE_PREVIEW_MODULE, "modules.rescue_restore_dryrun")
        self.assertEqual(CANONICAL_VERIFY_MODULE, "modules.backup_verify")


if __name__ == "__main__":
    unittest.main()
