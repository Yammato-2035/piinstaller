"""Tests for FAT32 ESP Rescue USB writer (staging, safety, dry-run)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_fat32_esp_usb_writer as fat32  # noqa: E402
from core.rescue_usb_operator_selection import REQUIRED_CONFIRMATIONS  # noqa: E402


SAMPLE_LIVE_CFG = """
label setuphelfer-rescue-default
	menu label ^Setuphelfer Rettung starten
	kernel /live/vmlinuz
	append initrd=/live/initrd.img boot=live config boot=live components quiet splash setuphelfer_start_assistant=1

label setuphelfer-rescue-network
	menu label Netzwerk
	kernel /live/vmlinuz
	append initrd=/live/initrd.img boot=live setuphelfer_network_onboarding=1
"""


class RescueFat32EspUsbTests(unittest.TestCase):
    def test_parse_live_cfg_boot_params(self) -> None:
        params = fat32.parse_live_cfg_boot_params(SAMPLE_LIVE_CFG)
        self.assertIn("setuphelfer_start_assistant=1", params.base_append)
        self.assertIn("setuphelfer_network_onboarding=1", params.labels["setuphelfer-rescue-network"])

    def test_generate_grub_cfg_required_menus(self) -> None:
        params = fat32.parse_live_cfg_boot_params(SAMPLE_LIVE_CFG)
        cfg = fat32.generate_grub_cfg(params)
        for title in (
            "Setuphelfer Rettung starten",
            "Netzwerk-Assistent",
            "MSI/NVIDIA",
            "Diagnosemodus",
            "RAM-Modus",
            "Neustart",
            "Herunterfahren",
        ):
            self.assertIn(title.split()[0], cfg)
        self.assertIn("linux /live/vmlinuz", cfg)
        self.assertIn("initrd /live/initrd.img", cfg)

    def test_validate_blocks_nvme_and_sda(self) -> None:
        with patch.object(fat32, "list_classified_devices", return_value=[]):
            with patch.object(fat32, "build_usb_candidates_payload", return_value={"devices": []}):
                for dev in ("/dev/nvme0n1", "/dev/sda"):
                    result = fat32.validate_fat32_write_target(
                        dev,
                        operator_evidence=None,
                        confirm_phrase=None,
                        dry_run=True,
                    )
                    self.assertTrue(result["blocked"])
                    self.assertIn("FORBIDDEN_SYSTEM_OR_BACKUP_DEVICE", result["blockers"])

    def test_validate_write_requires_confirm_phrase(self) -> None:
        evidence = {
            "write_allowed": True,
            "selected_device": "/dev/sdb",
            "operator_confirmations": {k: True for k in REQUIRED_CONFIRMATIONS},
        }
        mock_cd = type(
            "CD",
            (),
            {
                "id": "/dev/sdb",
                "name": "sdb",
                "type": "disk",
                "size": "58G",
                "removable": True,
                "mountpoints": [],
                "filesystems": [],
                "partitions": [],
                "is_system_disk": False,
                "is_boot_disk": False,
                "is_foreign_os_disk": False,
                "is_write_allowed": False,
            },
        )()
        devices = [
            {
                "device": "/dev/sdb",
                "selectable": True,
                "transport": "usb",
                "size": "58G",
            }
        ]
        with patch.object(fat32, "list_classified_devices", return_value=[mock_cd]):
            with patch.object(fat32, "build_usb_candidates_payload", return_value={"devices": devices}):
                bad = fat32.validate_fat32_write_target(
                    "/dev/sdb",
                    operator_evidence=evidence,
                    confirm_phrase="wrong",
                    dry_run=False,
                )
                self.assertIn("CONFIRM_PHRASE_MISMATCH", bad["blockers"])
                good = fat32.validate_fat32_write_target(
                    "/dev/sdb",
                    operator_evidence=evidence,
                    confirm_phrase=fat32.CONFIRM_PHRASE_FAT32_ESP,
                    dry_run=False,
                )
                self.assertFalse(good["blocked"])
                self.assertTrue(good["write_allowed"])

    def test_build_write_plan_dry_run_does_not_execute_write(self) -> None:
        iso = Path("/tmp/fake-rescue.iso")
        with patch.object(Path, "is_file", return_value=True):
            with patch.object(fat32, "sha256_file", return_value="abc"):
                with patch.object(fat32, "validate_fat32_write_target", return_value={"blocked": False, "blockers": []}):
                    with patch.object(fat32, "extract_iso_files", side_effect=OSError("mock extract skipped")):
                        plan = fat32.build_write_plan(
                            iso_path=iso,
                            target_device="/dev/sdb",
                            dry_run=True,
                        )
        self.assertEqual(plan["mode"], "dry_run")
        self.assertFalse(plan["write_executed"])
        self.assertFalse(plan["secrets_exposed"])

    def test_grub_cfg_no_secrets(self) -> None:
        params = fat32.parse_live_cfg_boot_params(SAMPLE_LIVE_CFG)
        cfg = fat32.generate_grub_cfg(params)
        self.assertNotIn("password", cfg.lower())
        self.assertNotIn("psk", cfg.lower())

    def test_required_confirmations_import(self) -> None:
        self.assertEqual(fat32.CONFIRM_PHRASE_FAT32_ESP, "WRITE SETUPHELFER FAT32 ESP USB")

    def test_fat32_label_spec(self) -> None:
        spec = fat32.fat32_esp_label_spec()
        self.assertEqual(spec["gpt_partition_name"], "SETUPHELFER_RESCUE")
        self.assertEqual(spec["fat_volume_label"], "SETUPHELFER")
        self.assertLessEqual(len(spec["fat_volume_label"]), fat32.FAT_VOLUME_LABEL_MAX_LEN)

    def test_fat_volume_label_max_length_enforced(self) -> None:
        with self.assertRaises(ValueError):
            fat32.assert_valid_fat_volume_label("SETUPHELFER_RESCUE")
        fat32.assert_valid_fat_volume_label("SETUPHELFER")

    def test_build_write_plan_exposes_separate_labels(self) -> None:
        iso = Path("/tmp/fake-rescue.iso")
        with patch.object(Path, "is_file", return_value=True):
            with patch.object(fat32, "sha256_file", return_value="abc"):
                with patch.object(fat32, "validate_fat32_write_target", return_value={"blocked": False, "blockers": []}):
                    with patch.object(fat32, "extract_iso_files", side_effect=OSError("skip")):
                        plan = fat32.build_write_plan(iso_path=iso, target_device="/dev/sdb", dry_run=True)
        self.assertEqual(plan["gpt_partition_name"], "SETUPHELFER_RESCUE")
        self.assertEqual(plan["fat_volume_label"], "SETUPHELFER")
        part0 = plan["partition_layout"]["partitions"][0]
        self.assertEqual(part0["gpt_partition_name"], "SETUPHELFER_RESCUE")
        self.assertEqual(part0["fat_volume_label"], "SETUPHELFER")
        mkfs_line = next(a for a in plan["destructive_actions"] if a.startswith("mkfs.vfat"))
        self.assertIn("SETUPHELFER", mkfs_line)
        self.assertNotIn("SETUPHELFER_RESCUE", mkfs_line)


if __name__ == "__main__":
    unittest.main()
