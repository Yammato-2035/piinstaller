"""Tests for FAT32 ESP live payload update (no real block devices)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_fat32_esp_payload_update as payload  # noqa: E402

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/rescue-live/update-fat32-esp-live-payload.sh"
CONFIRM = payload.CONFIRM_PHRASE_PAYLOAD_UPDATE


class RescueFat32EspPayloadUpdateTests(unittest.TestCase):
    def _safe_probe(self, **overrides: object) -> dict:
        base = {
            "target_device": "/dev/sdb",
            "partition_device": "/dev/sdb1",
            "transport": "usb",
            "size": "59G",
            "model": "Ultra Line",
            "serial": payload.EXPECTED_USB_SERIAL,
            "fstype": "vfat",
            "label": "SETUPHELFER",
            "parttypename": "EFI System",
            "gpt_partname": "SETUPHELFER_RESCUE",
            "mountpoints": [],
        }
        base.update(overrides)
        return payload.validate_payload_update_target_probe(**base)

    def test_without_confirm_blocked_in_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sq = Path(tmp) / "filesystem.squashfs"
            sq.write_bytes(b"x" * 128)
            plan = payload.build_payload_update_plan(
                target_device="/dev/sdb",
                new_squashfs=sq,
                confirm_phrase=None,
                confirm_update=False,
                execute_update=True,
                safety=self._safe_probe(),
            )
            self.assertTrue(plan["blocked"])
            self.assertFalse(plan["payload_update_executed"])

    def test_wrong_confirm_phrase_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sq = Path(tmp) / "filesystem.squashfs"
            sq.write_bytes(b"x")
            plan = payload.build_payload_update_plan(
                target_device="/dev/sdb",
                new_squashfs=sq,
                confirm_phrase="WRONG",
                confirm_update=True,
                execute_update=True,
                safety=self._safe_probe(),
            )
            self.assertIn("CONFIRM_PHRASE_MISMATCH", plan["blockers"])

    def test_not_vfat_blocked(self) -> None:
        probe = self._safe_probe(fstype="exfat", label="INTENSO")
        self.assertTrue(probe["blocked"])
        self.assertIn("NOT_VFAT_PARTITION", probe["blockers"])

    def test_wrong_label_blocked(self) -> None:
        probe = self._safe_probe(label="INTENSO")
        self.assertIn("FAT_LABEL_MISMATCH", probe["blockers"])

    def test_not_efi_partition_blocked(self) -> None:
        probe = self._safe_probe(parttypename="HPFS/NTFS/exFAT", gpt_partname="")
        self.assertIn("NOT_EFI_SYSTEM_PARTITION", probe["blockers"])

    def test_valid_probe_allows_write(self) -> None:
        probe = self._safe_probe()
        self.assertFalse(probe["blocked"])
        self.assertTrue(probe["write_allowed"])
        self.assertFalse(probe["partition_rewritten"])

    def test_script_has_no_destructive_partition_commands(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        hits = payload.script_has_forbidden_destructive_commands(text)
        self.assertEqual(hits, [], hits)

    def test_allowed_payload_paths_only(self) -> None:
        self.assertIn("live/filesystem.squashfs", payload.ALLOWED_PAYLOAD_REL_PATHS)
        self.assertNotIn("EFI/BOOT/BOOTX64.EFI", payload.ALLOWED_PAYLOAD_REL_PATHS)

    def test_evidence_update_sets_new_squashfs_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sq = Path(tmp) / "filesystem.squashfs"
            sq.write_bytes(b"new-squashfs-content")
            old = {
                "writer_mode": "fat32_esp",
                "files": [
                    {
                        "staging_path": "live/filesystem.squashfs",
                        "sha256": "oldhash",
                        "size_bytes": 1,
                    }
                ],
            }
            updated = payload.build_updated_stick_evidence(
                medium_evidence=old,
                new_squashfs=sq,
                project_version="1.7.9.3",
            )
            entry = next(f for f in updated["files"] if f["staging_path"] == "live/filesystem.squashfs")
            self.assertNotEqual(entry["sha256"], "oldhash")
            self.assertEqual(entry["size_bytes"], sq.stat().st_size)

    def test_script_invokes_verify_after_update(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("verify-fat32-esp-rescue-usb.sh", text)

    def test_script_uses_sudo_for_mount_writes(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertTrue(payload.script_uses_sudo_for_root_owned_mount_writes(text))

    def test_stick_hash_mismatch_not_success(self) -> None:
        gate = payload.evaluate_stick_squashfs_hash(
            actual_sha256="921c3e23bfbeb99a6295b80be5f8b5d40b55994019b0e614fef633138c6bdfe7",
            expected_sha256="ac95ebc3bdc4693da56d51cda1bb3f5fd36dc68d18b2ff1e8f76aad30a85f00a",
        )
        self.assertFalse(gate["ok"])
        result = payload.build_payload_update_result(
            target_device="/dev/sdb",
            old_squashfs_sha256="921c3e23",
            new_squashfs_sha256="ac95ebc3",
            stick_squashfs_sha256="921c3e23",
            started_at="2026-06-09T00:00:00Z",
            completed_at="2026-06-09T00:01:00Z",
            payload_update_executed=False,
            payload_update_status="failed",
            verify_status="review_required",
            write_errors_detected=True,
            failed_step="copy_or_metadata_write",
        )
        self.assertEqual(result["stick_squashfs_hash_ok"], False)
        self.assertIn("not allowed", result["rs001_reason"])

    def test_success_requires_matching_stick_hash(self) -> None:
        new_sha = "ac95ebc3bdc4693da56d51cda1bb3f5fd36dc68d18b2ff1e8f76aad30a85f00a"
        result = payload.build_payload_update_result(
            target_device="/dev/sdb",
            old_squashfs_sha256="921c3e23",
            new_squashfs_sha256=new_sha,
            stick_squashfs_sha256=new_sha,
            started_at="2026-06-09T00:00:00Z",
            completed_at="2026-06-09T00:01:00Z",
            payload_update_executed=True,
            payload_update_status="success",
            verify_status="success",
        )
        self.assertTrue(result["stick_squashfs_hash_ok"])
        self.assertIn("hardware retest pending", result["rs001_reason"])

    def test_metadata_failure_review_required(self) -> None:
        new_sha = "ac95ebc3bdc4693da56d51cda1bb3f5fd36dc68d18b2ff1e8f76aad30a85f00a"
        result = payload.build_payload_update_result(
            target_device="/dev/sdb",
            old_squashfs_sha256="921c3e23bfbeb99a6295b80be5f8b5d40b55994019b0e614fef633138c6bdfe7",
            new_squashfs_sha256=new_sha,
            stick_squashfs_sha256=new_sha,
            started_at="2026-06-09T00:00:00Z",
            completed_at="2026-06-09T00:01:00Z",
            payload_update_executed=True,
            payload_update_status="review_required",
            verify_status="review_required",
            write_errors_detected=True,
            failed_step="metadata_write",
        )
        self.assertIn("metadata evidence failed", result["rs001_reason"])

    def test_result_keeps_rs001_yellow(self) -> None:
        result = payload.build_payload_update_result(
            target_device="/dev/sdb",
            old_squashfs_sha256="aaa",
            new_squashfs_sha256="bbb",
            stick_squashfs_sha256="bbb",
            started_at="2026-06-09T00:00:00Z",
            completed_at="2026-06-09T00:01:00Z",
            payload_update_executed=True,
            payload_update_status="success",
            verify_status="success",
        )
        self.assertEqual(result["rs001_status"], "yellow")
        self.assertFalse(result["partition_rewritten"])
        self.assertFalse(result["filesystem_reformatted"])


if __name__ == "__main__":
    unittest.main()
