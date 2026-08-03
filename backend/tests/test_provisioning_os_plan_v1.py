"""PI-RS-HW-COMPAT-PROVISION-001 Phase 13: os_compatibility/os_image_verifier/os_install_plan."""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from provisioning.os_compatibility import build_os_compatibility_diagnostics, evaluate_compatibility
from provisioning.os_image_verifier import build_verification_preview, compute_sha256_of_local_file
from provisioning.os_install_plan import build_os_install_plan_diagnostics, build_provisioning_plan

_PI5_CATALOG_ENTRY = {
    "image_id": "raspberry-pi-os-bookworm-arm64",
    "display_name": "Raspberry Pi OS (Bookworm) — arm64",
    "architecture": "aarch64",
    "sha256": None,
    "signature_required": True,
    "minimum_target_bytes": 4_000_000_000,
    "supported_platforms": ["pi5", "cm5", "pi4"],
    "supported_boot_modes": ["microsd", "usb_mass_storage"],
    "support_status": "experimental",
}

_FUTURE_CATALOG_ENTRY = {
    "image_id": "proxmox-ve-future",
    "architecture": "x86_64",
    "sha256": None,
    "signature_required": True,
    "minimum_target_bytes": 0,
    "supported_platforms": [],
    "supported_boot_modes": [],
    "support_status": "future",
}


class TestCompatibilityChecks(unittest.TestCase):
    def test_architecture_mismatch_is_incompatible(self) -> None:
        result = evaluate_compatibility(catalog_entry=_PI5_CATALOG_ENTRY, target_architecture="x86_64")
        self.assertEqual(result["compatibility_status"], "incompatible")
        self.assertIn("architecture_mismatch", result["blockers"])

    def test_matching_architecture_and_platform_is_compatible(self) -> None:
        result = evaluate_compatibility(
            catalog_entry=_PI5_CATALOG_ENTRY,
            target_architecture="aarch64",
            target_platform_id="pi5",
            target_bytes=8_000_000_000,
        )
        self.assertEqual(result["compatibility_status"], "compatible")

    def test_future_entries_always_incompatible(self) -> None:
        result = evaluate_compatibility(catalog_entry=_FUTURE_CATALOG_ENTRY, target_architecture="x86_64")
        self.assertEqual(result["compatibility_status"], "incompatible")
        self.assertIn("catalog_support_status_future", result["blockers"])

    def test_diagnostics_read_only(self) -> None:
        diag = build_os_compatibility_diagnostics()
        self.assertTrue(diag["read_only"])
        self.assertFalse(diag["writes_allowed"])


class TestImageVerifier(unittest.TestCase):
    def test_no_reference_hash_never_reports_verified(self) -> None:
        preview = build_verification_preview(catalog_entry=_PI5_CATALOG_ENTRY, local_file_sha256="abc123")
        self.assertEqual(preview["verification_status"], "no_reference_hash_in_catalog")
        self.assertFalse(preview["signature_verified"])
        self.assertFalse(preview["download_performed"])

    def test_hash_mismatch_detected(self) -> None:
        entry = dict(_PI5_CATALOG_ENTRY, sha256="deadbeef" * 8)
        preview = build_verification_preview(catalog_entry=entry, local_file_sha256="cafebabe" * 8)
        self.assertEqual(preview["verification_status"], "hash_mismatch")

    def test_hash_match_detected(self) -> None:
        entry = dict(_PI5_CATALOG_ENTRY, sha256="a" * 64)
        preview = build_verification_preview(catalog_entry=entry, local_file_sha256="A" * 64)
        self.assertEqual(preview["verification_status"], "hash_match")

    def test_compute_sha256_of_real_local_file_never_downloads(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"hello world")
            tmp_path = Path(tmp.name)
        try:
            expected = hashlib.sha256(b"hello world").hexdigest()
            self.assertEqual(compute_sha256_of_local_file(tmp_path), expected)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_missing_file_returns_none_not_crash(self) -> None:
        self.assertIsNone(compute_sha256_of_local_file(Path("/nonexistent/file/xyz")))


class TestInstallPlan(unittest.TestCase):
    def test_write_allowed_always_false(self) -> None:
        plan = build_provisioning_plan(
            catalog_entry=_PI5_CATALOG_ENTRY,
            target_architecture="aarch64",
            target_platform_id="pi5",
            target_bytes=8_000_000_000,
        )
        self.assertFalse(plan["write_allowed"])

    def test_incompatible_target_is_blocked_plan(self) -> None:
        plan = build_provisioning_plan(catalog_entry=_PI5_CATALOG_ENTRY, target_architecture="x86_64")
        self.assertEqual(plan["plan_status"], "blocked")
        self.assertFalse(plan["write_allowed"])

    def test_compatible_but_unverified_hash_is_review_required(self) -> None:
        plan = build_provisioning_plan(
            catalog_entry=_PI5_CATALOG_ENTRY,
            target_architecture="aarch64",
            target_platform_id="pi5",
            target_bytes=8_000_000_000,
        )
        self.assertEqual(plan["plan_status"], "review_required")
        self.assertIn("signed_image_with_real_checksum", plan["required_next_gates"])

    def test_diagnostics_no_destructive_tools_used(self) -> None:
        diag = build_os_install_plan_diagnostics()
        self.assertFalse(diag["write_allowed"])
        for key in ("dd_used", "mkfs_used", "parted_used", "sfdisk_used", "sgdisk_used", "wipefs_used"):
            self.assertFalse(diag[key])


if __name__ == "__main__":
    unittest.main()
