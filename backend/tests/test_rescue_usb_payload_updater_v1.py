"""PI-RS-USB-UPDATER-001 — atomic FAT32 ESP payload updater tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_usb_payload_atomic_update as atomic  # noqa: E402
from core.rescue_fat32_esp_usb_writer import sha256_file  # noqa: E402

EXPECTED_SHA = "cada647ccc11a545a8b4eb6f42deb8745bdedcd5b1662e738c96d68c987621b5"
EXPECTED_VERSION = "1.10.0.17"
PAYLOAD = Path(__file__).resolve().parents[2] / "build/rescue/filesystem.squashfs.repacked-1.10.0.17"


class RescueUsbPayloadUpdaterV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        if not PAYLOAD.is_file():
            self.skipTest(f"missing payload artifact: {PAYLOAD}")

    def test_consistent_payload_1_10_0_16_accepted(self) -> None:
        report = atomic.validate_source_payload(
            PAYLOAD,
            expected_sha256=EXPECTED_SHA,
            expected_version=EXPECTED_VERSION,
        )
        self.assertFalse(report["blocked"])
        self.assertTrue(report["version_consistent"])
        self.assertEqual(report["canonical_version"], EXPECTED_VERSION)

    def test_wrong_sha_blocks(self) -> None:
        report = atomic.validate_source_payload(
            PAYLOAD,
            expected_sha256="0" * 64,
            expected_version=EXPECTED_VERSION,
        )
        self.assertTrue(report["blocked"])
        self.assertIn("source_payload_hash_mismatch", report["errors"])

    def test_symlink_source_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "real.sq"
            target.write_bytes(b"x")
            link = Path(tmp) / "link.sq"
            link.symlink_to(target)
            ok, err = atomic.is_safe_regular_file(link)
            self.assertFalse(ok)
            self.assertEqual(err, "SOURCE_IS_SYMLINK")

    def test_esp_metadata_from_payload_version(self) -> None:
        doc = atomic.build_atomic_esp_version_json(
            payload_version=EXPECTED_VERSION,
            payload_sha256=EXPECTED_SHA,
        )
        self.assertEqual(doc["project_version"], EXPECTED_VERSION)
        self.assertEqual(doc["rescue_payload_version"], EXPECTED_VERSION)
        self.assertEqual(doc["payload_sha256"], EXPECTED_SHA)
        self.assertTrue(doc["content_verified"])
        self.assertEqual(doc["update_method"], atomic.UPDATE_METHOD)

    def test_old_project_version_not_preserved(self) -> None:
        stale = {"project_version": "1.10.0.13", "git_commit": "abc"}
        doc = atomic.build_atomic_esp_version_json(
            payload_version=EXPECTED_VERSION,
            payload_sha256=EXPECTED_SHA,
            existing=stale,
        )
        self.assertEqual(doc["project_version"], EXPECTED_VERSION)
        self.assertNotEqual(doc["project_version"], "1.10.0.13")

    def test_validate_esp_metadata_ok(self) -> None:
        doc = atomic.build_atomic_esp_version_json(
            payload_version=EXPECTED_VERSION,
            payload_sha256=EXPECTED_SHA,
        )
        gate = atomic.validate_esp_metadata(
            doc,
            expected_version=EXPECTED_VERSION,
            expected_sha256=EXPECTED_SHA,
        )
        self.assertTrue(gate["ok"])

    def test_filename_version_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "filesystem.squashfs.repacked-9.9.9.9"
            fake.write_bytes(PAYLOAD.read_bytes())
            report = atomic.validate_source_payload(fake, expected_version=EXPECTED_VERSION)
            self.assertTrue(report["blocked"])
            self.assertIn("source_payload_filename_version_mismatch", report["errors"])

    def test_simulated_atomic_replace_success(self) -> None:
        report = atomic.validate_source_payload(
            PAYLOAD,
            expected_sha256=EXPECTED_SHA,
            expected_version=EXPECTED_VERSION,
        )
        with tempfile.TemporaryDirectory() as tmp:
            mount = atomic.AtomicMountState(Path(tmp) / "SETUPHELFER")
            mount.live_dir.mkdir(parents=True)
            mount.active_payload.write_bytes(b"old-payload")
            mount.version_path.parent.mkdir(parents=True, exist_ok=True)
            mount.version_path.write_text(
                json.dumps({"project_version": "1.10.0.15"}) + "\n",
                encoding="utf-8",
            )
            result = atomic.simulate_atomic_replace(mount, PAYLOAD, source_report=report)
            self.assertEqual(result["status"], "success")
            self.assertTrue(result["atomic_replace"])
            self.assertEqual(result["after"]["payload_version"], EXPECTED_VERSION)
            self.assertEqual(sha256_file(mount.active_payload), EXPECTED_SHA)

    def test_simulated_failure_before_activation_keeps_old(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mount = atomic.AtomicMountState(Path(tmp) / "SETUPHELFER")
            mount.live_dir.mkdir(parents=True)
            old_bytes = b"keep-me"
            mount.active_payload.write_bytes(old_bytes)
            bad_source = {
                "path": str(PAYLOAD),
                "actual_sha256": "deadbeef",
                "canonical_version": EXPECTED_VERSION,
                "internal_versions": {},
                "version_consistent": True,
            }
            result = atomic.simulate_atomic_replace(mount, PAYLOAD, source_report=bad_source)
            self.assertNotEqual(result["status"], "success")
            self.assertEqual(mount.active_payload.read_bytes(), old_bytes)

    def test_simulated_rollback_after_payload_swap(self) -> None:
        report = atomic.validate_source_payload(
            PAYLOAD,
            expected_sha256=EXPECTED_SHA,
            expected_version=EXPECTED_VERSION,
        )
        with tempfile.TemporaryDirectory() as tmp:
            mount = atomic.AtomicMountState(Path(tmp) / "SETUPHELFER")
            mount.live_dir.mkdir(parents=True)
            mount.active_payload.write_bytes(b"old-payload-bytes")
            mount.version_path.parent.mkdir(parents=True, exist_ok=True)
            mount.version_path.write_text(
                json.dumps({"project_version": "1.10.0.15"}) + "\n",
                encoding="utf-8",
            )
            result = atomic.simulate_atomic_replace(
                mount,
                PAYLOAD,
                source_report=report,
                rollback_inject_after_payload=True,
            )
            self.assertIn(result["status"], ("failed_rolled_back", "critical_manual_recovery_required"))
            self.assertTrue(result["rollback_required"])

    def test_path_traversal_blocked(self) -> None:
        self.assertFalse(atomic.validate_path_safe_relative("../etc/passwd"))
        self.assertFalse(atomic.validate_path_safe_relative("/absolute"))
        self.assertTrue(atomic.validate_path_safe_relative("live/filesystem.squashfs"))

    def test_setup_logs_sibling_validation(self) -> None:
        ok = atomic.validate_sibling_setup_logs_partition(
            parent_device="/dev/sda",
            logs_label="SETUP_LOGS",
            logs_fstype="vfat",
        )
        self.assertTrue(ok["sibling_setup_logs_detected"])
        self.assertFalse(ok["blocked"])
        bad = atomic.validate_sibling_setup_logs_partition(
            parent_device="/dev/sda",
            logs_label="WRONG",
            logs_fstype="vfat",
        )
        self.assertTrue(bad["blocked"])

    def test_prev_backup_name(self) -> None:
        self.assertEqual(
            atomic.plan_prev_backup_name("1.10.0.15"),
            "filesystem.squashfs.prev-1.10.0.15",
        )

    def test_redact_serial(self) -> None:
        red = atomic.redact_serial("24111412110686")
        self.assertNotIn("24111412110686", red)
        self.assertIn("…", red)


if __name__ == "__main__":
    unittest.main()
