"""Zentrales Profilmodell, API-Mapping, Preview (kein Backup-Start)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.backup_profiles import (  # noqa: E402
    PROFILE_FULL_EXPERT,
    PROFILE_RECOMMENDED,
    build_profile_preview,
    filter_included_paths_for_target,
    normalize_backup_profile,
    profile_specs_public,
    resolve_profile_request,
)

try:
    from fastapi.testclient import TestClient

    from app import app as fastapi_app

    _HAS_TC = True
except Exception:  # noqa: BLE001
    TestClient = None  # type: ignore[misc, assignment]
    fastapi_app = None
    _HAS_TC = False


class BackupProfilesModelTests(unittest.TestCase):
    def test_list_five_profiles(self) -> None:
        specs = profile_specs_public()
        self.assertEqual(len(specs), 5)
        ids = {x["id"] for x in specs}
        self.assertEqual(
            ids,
            {"recommended", "fast-system", "user-data", "developer", "full-expert"},
        )

    def test_recommended_default_normalize(self) -> None:
        p, w = normalize_backup_profile(None)
        self.assertEqual(p, PROFILE_RECOMMENDED)
        self.assertEqual(p, "recommended")

    def test_legacy_full_maps_full_expert(self) -> None:
        r = resolve_profile_request(request_type="full", profile_raw=None)
        self.assertEqual(r["runner_backup_type"], "full")
        self.assertEqual(r["normalized_profile"], PROFILE_FULL_EXPERT)
        self.assertIn("legacy_type_full_maps_to_full_expert", r["warning_codes"])
        self.assertTrue(r["requires_expert_confirmation"])

    def test_profile_recommended_is_data_runner(self) -> None:
        r = resolve_profile_request(request_type="profile", profile_raw="recommended")
        self.assertEqual(r["runner_backup_type"], "data")
        self.assertTrue(r["recommended"])

    def test_full_expert_requires_confirm_flag(self) -> None:
        r = resolve_profile_request(request_type="profile", profile_raw="full-expert")
        self.assertEqual(r["runner_backup_type"], "full")
        self.assertTrue(r["requires_expert_confirmation"])

    def test_filter_excludes_target_overlap(self) -> None:
        bd = "/tmp/backup-target-subdir"
        inc, w = filter_included_paths_for_target(["/home", "/tmp"], bd)
        self.assertNotIn("/tmp", inc)
        self.assertIn("/home", inc)
        self.assertTrue(any("excluded_source_overlaps_target" in x for x in w))

    def test_preview_no_backup_side_effect(self) -> None:
        prev = build_profile_preview(profile_raw="recommended", backup_dir="/tmp/sh-preview-test", target_free_bytes=1000)
        self.assertEqual(prev["profile"], "recommended")
        self.assertIsNone(prev["estimated_size_bytes"])


class BackupProfilesApiTests(unittest.TestCase):
    @unittest.skipUnless(_HAS_TC, "FastAPI TestClient nicht verfügbar")
    def test_get_profiles(self) -> None:
        c = TestClient(fastapi_app, base_url="http://localhost")
        r = c.get("/api/backup/profiles")
        self.assertEqual(r.status_code, 200)
        b = r.json()
        self.assertEqual(b.get("status"), "success")
        self.assertEqual(len(b.get("profiles") or []), 5)

    @unittest.skipUnless(_HAS_TC, "FastAPI TestClient nicht verfügbar")
    @patch("app._validate_backup_dir")
    def test_profile_preview_ok(self, mock_vdir) -> None:
        import tempfile

        td = tempfile.mkdtemp()
        mock_vdir.return_value = td
        c = TestClient(fastapi_app, base_url="http://localhost")
        r = c.post("/api/backup/profile-preview", json={"profile": "recommended", "backup_dir": td})
        self.assertEqual(r.status_code, 200, r.text)
        b = r.json()
        self.assertEqual(b.get("status"), "success")
        prev = b.get("preview") or {}
        self.assertEqual(prev.get("profile"), "recommended")
        self.assertIn("included_paths", prev)


class BackupProfilesCreateContractTests(unittest.TestCase):
    @unittest.skipUnless(_HAS_TC, "FastAPI TestClient nicht verfügbar")
    def test_create_unknown_type(self) -> None:
        c = TestClient(fastapi_app, base_url="http://localhost")
        r = c.post("/api/backup/create", json={"type": "foobar", "target": "local"})
        self.assertEqual(r.status_code, 200)
        b = r.json()
        self.assertEqual(b.get("code"), "backup.create_unknown_type")

    @unittest.skipUnless(_HAS_TC, "FastAPI TestClient nicht verfügbar")
    @patch("app._validate_backup_dir", return_value="/mnt/setuphelfer/backups/__pytest_confirm__")
    @patch("app._detect_active_package_operations", return_value=[])
    def test_full_create_requires_confirm_full_expert(self, _pkg, _vd) -> None:
        c = TestClient(fastapi_app, base_url="http://localhost")
        r = c.post(
            "/api/backup/create",
            json={
                "type": "full",
                "backup_dir": "/mnt/setuphelfer/backups/__pytest_confirm__",
                "target": "local",
                "async": False,
            },
        )
        self.assertEqual(r.status_code, 200)
        b = r.json()
        self.assertEqual(b.get("code"), "backup.full_expert_confirmation_required")


if __name__ == "__main__":
    unittest.main()
