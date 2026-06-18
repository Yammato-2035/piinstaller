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

    def test_generate_fat32_esp_grub_cfg_required_menus(self) -> None:
        cfg = fat32.generate_fat32_esp_grub_cfg()
        for title in (
            "sicherer Textmodus",
            "grafische Oberflaeche",
            "Diagnose sammeln",
            "WLAN-Diagnose",
            "Neustart",
            "Ausschalten",
        ):
            self.assertIn(title.split()[0], cfg)
        self.assertIn("linux /live/vmlinuz", cfg)
        self.assertIn("initrd /live/initrd.img", cfg)
        self.assertIn(f"search --no-floppy --label {fat32.FAT_VOLUME_LABEL} --set=root", cfg)
        self.assertIn("setuphelfer_mode=text", cfg)
        self.assertIn("setuphelfer_kiosk=0", cfg)
        self.assertNotIn("setuphelfer_kiosk=1 setuphelfer_safe_ui", cfg)
        self.assertIn("pci=noaer", cfg)
        self.assertIn("nomodeset", cfg)
        self.assertIn("nouveau.modeset=0", cfg)

    def test_generate_grub_cfg_required_menus(self) -> None:
        params = fat32.parse_live_cfg_boot_params(SAMPLE_LIVE_CFG)
        cfg = fat32.generate_grub_cfg(params)
        self.assertIn("linux /live/vmlinuz", cfg)

    def test_generate_fat32_esp_grub_cfg_with_uuid(self) -> None:
        cfg = fat32.generate_fat32_esp_grub_cfg(fat_uuid="ABCD-1234")
        self.assertIn("search --no-floppy --fs-uuid ABCD-1234 --set=root", cfg)
        self.assertIn(f"search --no-floppy --label {fat32.FAT_VOLUME_LABEL} --set=root", cfg)

    def test_patch_grub_cfg_for_fat_uuid(self) -> None:
        base = fat32.generate_fat32_esp_grub_cfg()
        patched = fat32.patch_grub_cfg_for_fat_uuid(base, "A1B2-C3D4-E5F6-7890")
        self.assertIn("search --no-floppy --fs-uuid A1B2-C3D4-E5F6-7890 --set=root", patched)
        self.assertIn("linux /live/vmlinuz", patched)

    def test_fat32_esp_grub_cfg_staging_paths(self) -> None:
        from core.rescue_fat32_esp_usb_verify import validate_fat32_esp_grub_cfg

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "live").mkdir(parents=True)
            (root / "live" / "vmlinuz").write_bytes(b"kernel")
            (root / "live" / "initrd.img").write_bytes(b"initrd")
            cfg = fat32.generate_fat32_esp_grub_cfg()
            result = validate_fat32_esp_grub_cfg(cfg, mount_root=root)
            self.assertTrue(result["ok"], result["errors"])
            self.assertEqual(result["boot_menu_entries"], 5)

    def test_fat32_esp_grub_verify_fails_missing_kernel(self) -> None:
        from core.rescue_fat32_esp_usb_verify import (
            GRUB_ERROR_KERNEL,
            validate_fat32_esp_grub_cfg,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "live").mkdir()
            (root / "live" / "initrd.img").write_bytes(b"x")
            cfg = fat32.generate_fat32_esp_grub_cfg()
            result = validate_fat32_esp_grub_cfg(cfg, mount_root=root)
            self.assertFalse(result["ok"])
            self.assertIn(GRUB_ERROR_KERNEL, result["errors"])

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

    def test_write_plan_uses_fat_compatible_rsync(self) -> None:
        iso = Path("/tmp/fake-rescue.iso")
        with patch.object(Path, "is_file", return_value=True):
            with patch.object(fat32, "sha256_file", return_value="abc"):
                with patch.object(fat32, "validate_fat32_write_target", return_value={"blocked": False, "blockers": []}):
                    with patch.object(fat32, "extract_iso_files", side_effect=OSError("skip")):
                        plan = fat32.build_write_plan(iso_path=iso, target_device="/dev/sdb", dry_run=True)
        plan_blob = json.dumps(plan)
        self.assertNotIn('rsync -a "', plan_blob)
        self.assertNotIn("rsync -a ${", plan_blob)
        for opt in ("--no-owner", "--no-group", "--no-perms", "--omit-dir-times"):
            self.assertIn(opt, plan_blob)
        self.assertIn(".sqtmp", plan_blob)
        self.assertEqual(plan["gpt_partition_name"], "SETUPHELFER_RESCUE")
        self.assertEqual(plan["fat_volume_label"], "SETUPHELFER")

    def test_operator_terminal_commands_fat_rsync_and_labels(self) -> None:
        cmds = fat32.build_operator_terminal_commands(
            iso_path=Path("/tmp/fake.iso"),
            target_device="/dev/sdb",
            workspace=Path("/tmp/ws"),
        )
        manual = cmds["write_manual"]
        self.assertNotIn("rsync -a \"", manual)
        self.assertNotIn("rsync -a ${", manual)
        self.assertIn("--no-owner", manual)
        self.assertIn("--no-group", manual)
        self.assertIn("--no-perms", manual)
        self.assertIn("--omit-dir-times", manual)
        self.assertIn("--exclude='.sqtmp/'", manual)
        self.assertIn("mkfs.vfat -F 32 -n SETUPHELFER", manual)
        self.assertIn("-c 1:SETUPHELFER_RESCUE", manual)
        self.assertIn("partprobe", manual)
        self.assertIn("udevadm settle", manual)
        self.assertIn("fatlabel", manual)
        self.assertIn("wipefs --no-act", manual)
        self.assertIn("wipefs -a", manual)

    def test_embedded_bootstrap_has_partition_modules(self) -> None:
        cfg = fat32.generate_fat32_esp_embedded_bootstrap_cfg()
        for token in (
            "insmod part_gpt",
            "insmod fat",
            "insmod search_label",
            "insmod configfile",
            "search --no-floppy --label SETUPHELFER",
        ):
            self.assertIn(token, cfg)

    def test_build_bootx64_not_iso_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "EFI/BOOT/BOOTX64.EFI"
            iso_sha = "8656837e2f3ac643ca86931bf5419885bcfc0cbdfe75b087382c768b04fc81db"

            def runner(cmd: list[str], timeout: int = 120) -> object:
                if cmd[0] == "grub-mkstandalone":
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_bytes(b"\x00" * 400_000)
                    return type("P", (), {"returncode": 0, "stdout": "", "stderr": ""})()
                return type("P", (), {"returncode": 1, "stdout": "", "stderr": ""})()

            with patch.object(fat32, "grub_mkstandalone_tooling", return_value={"available": True, "modules_requested": ["part_gpt"]}):
                with patch.object(fat32, "sha256_file", return_value="deadbeef" * 8):
                    meta = fat32.build_fat32_esp_bootx64_efi(out, runner=runner)
            self.assertEqual(meta["bootx64_source"], "grub_mkstandalone")
            self.assertFalse(meta["bootx64_iso_copied"])
            self.assertNotEqual(meta["sha256"], iso_sha)

    def test_fat32_staging_rsync_command(self) -> None:
        cmd = fat32.fat32_staging_rsync_command(staging="/staging", mount="/mnt", sudo=False)
        self.assertNotIn("rsync -a", cmd)
        self.assertIn("--no-owner", cmd)
        self.assertIn(".sqtmp", cmd)

    def test_write_plan_includes_wipefs(self) -> None:
        iso = Path("/tmp/fake-rescue.iso")
        with patch.object(Path, "is_file", return_value=True):
            with patch.object(fat32, "sha256_file", return_value="abc"):
                with patch.object(
                    fat32,
                    "validate_fat32_write_target",
                    return_value={"blocked": False, "blockers": []},
                ):
                    with patch.object(fat32, "extract_iso_files", side_effect=OSError("skip")):
                        plan = fat32.build_write_plan(
                            iso_path=iso,
                            target_device="/dev/sdb",
                            dry_run=True,
                        )
        blob = " ".join(plan["destructive_actions"])
        self.assertIn("wipefs", blob)
        self.assertIn("iso9660", plan["signature_wipe"]["repair_stale_iso9660"])


if __name__ == "__main__":
    unittest.main()
