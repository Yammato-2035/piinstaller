"""Tests for FAT32 ESP USB verify (stale parent iso9660, label detection)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_fat32_esp_usb_verify as verify  # noqa: E402

EFI = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"


class RescueFat32EspUsbVerifyTests(unittest.TestCase):
    def test_parse_blkid_label_output(self) -> None:
        self.assertEqual(verify.parse_blkid_label_output('SETUPHELFER\n'), "SETUPHELFER")
        self.assertEqual(verify.parse_blkid_label_output('"SETUPHELFER"'), "SETUPHELFER")

    def test_stale_parent_iso9660_partition_label_ok(self) -> None:
        result = verify.evaluate_verify_probe(
            parent_pttype="gpt",
            parent_signature_types=["iso9660", "gpt"],
            part_parttype=EFI,
            part_partlabel="SETUPHELFER_RESCUE",
            part_fstype="vfat",
            part_fat_label="SETUPHELFER",
            target_device="/dev/sdb",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue(result["stale_parent_iso9660"])
        self.assertIn(verify.STALE_PARENT_ISO9660_WARN, result["warnings"])
        self.assertTrue(any("wipefs -a -t iso9660" in w for w in result["warnings"]))

    def test_partition_label_really_missing_fails(self) -> None:
        result = verify.evaluate_verify_probe(
            parent_pttype="gpt",
            parent_signature_types=[],
            part_parttype=EFI,
            part_partlabel="SETUPHELFER_RESCUE",
            part_fstype="vfat",
            part_fat_label="",
            target_device="/dev/sdb",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["exit_code"], 22)
        self.assertEqual(result["errors"][0]["code"], "FAT_LABEL_MISSING")

    def test_parent_iso9660_without_gpt_fails(self) -> None:
        result = verify.evaluate_verify_probe(
            parent_pttype="dos",
            parent_signature_types=["iso9660"],
            part_parttype=EFI,
            part_partlabel="SETUPHELFER_RESCUE",
            part_fstype="vfat",
            part_fat_label="SETUPHELFER",
            target_device="/dev/sdb",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["errors"][0]["code"], "NO_GPT")

    def test_parent_iso9660_without_vfat_partition_fails(self) -> None:
        result = verify.evaluate_verify_probe(
            parent_pttype="gpt",
            parent_signature_types=["iso9660"],
            part_parttype=EFI,
            part_partlabel="SETUPHELFER_RESCUE",
            part_fstype="iso9660",
            part_fat_label="",
            target_device="/dev/sdb",
        )
        self.assertFalse(result["ok"])
        codes = {e["code"] for e in result["errors"]}
        self.assertIn("NOT_VFAT", codes)
        self.assertNotIn("FAT_LABEL_MISSING", codes)
        self.assertFalse(result["structural_layout_valid"])

    def test_probe_fat_volume_label_falls_back_to_lsblk(self) -> None:
        def runner(cmd: list[str], **_: object) -> object:
            import subprocess

            class P:
                stdout = ""
                returncode = 1

            if cmd[:2] == ["lsblk", "-no"] and cmd[2] == "LABEL":
                P.stdout = "SETUPHELFER\n"
                P.returncode = 0
            return P

        label = verify.probe_fat_volume_label("/dev/sdb1", runner=runner)
        self.assertEqual(label, "SETUPHELFER")

    def test_verify_script_rejects_sqtmp_on_mount(self) -> None:
        script = Path(__file__).resolve().parents[2] / "scripts/rescue-live/verify-fat32-esp-rescue-usb.sh"
        text = script.read_text(encoding="utf-8")
        self.assertIn(".sqtmp", text)
        self.assertIn("must not be on USB", text)

    def test_probe_fat_volume_label_prefers_sudo_blkid(self) -> None:
        calls: list[list[str]] = []

        def runner(cmd: list[str], timeout: int = 30) -> object:
            calls.append(cmd)
            if cmd[:2] == ["sudo", "blkid"]:
                return type("P", (), {"returncode": 0, "stdout": "SETUPHELFER\n", "stderr": ""})()
            return type("P", (), {"returncode": 1, "stdout": "", "stderr": ""})()

        label = verify.probe_fat_volume_label("/dev/sdb1", runner=runner)
        self.assertEqual(label, "SETUPHELFER")
        self.assertEqual(calls[0][:4], ["sudo", "blkid", "-p", "-s"])

    def test_parse_wipefs_signature_types(self) -> None:
        sample = "/dev/sdb: offset 0x200 iso9660 CD-ROM\n/dev/sdb: offset 0x0 gpt\n"
        types = verify.parse_wipefs_signature_types(sample)
        self.assertIn("iso9660", types)
        self.assertIn("gpt", types)

    def test_write_plan_includes_wipefs(self) -> None:
        from core import rescue_fat32_esp_usb_writer as fat32
        from unittest.mock import patch

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


    def test_grub_validate_requires_uuid_on_usb_when_expected(self) -> None:
        from core.rescue_fat32_esp_usb_writer import generate_fat32_esp_grub_cfg

        cfg_label_only = generate_fat32_esp_grub_cfg()
        result = verify.validate_fat32_esp_grub_cfg(
            cfg_label_only,
            expected_fat_uuid="A1B2-C3D4-E5F6-7890",
        )
        self.assertFalse(result["ok"])
        self.assertIn(verify.GRUB_ERROR_ROOT, result["errors"])

    def test_grub_validate_accepts_uuid_patched_cfg(self) -> None:
        from core.rescue_fat32_esp_usb_writer import patch_grub_cfg_for_fat_uuid, generate_fat32_esp_grub_cfg

        uuid = "A1B2-C3D4-E5F6-7890"
        cfg = patch_grub_cfg_for_fat_uuid(generate_fat32_esp_grub_cfg(), uuid)
        result = verify.validate_fat32_esp_grub_cfg(cfg, expected_fat_uuid=uuid)
        self.assertTrue(result["ok"], result["errors"])

    def test_bootx64_verify_fails_iso_copied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "EFI/BOOT").mkdir(parents=True)
            (root / "EFI/BOOT/BOOTX64.EFI").write_bytes(b"x")
            (root / "setuphelfer/rescue").mkdir(parents=True)
            evidence = {
                "bootx64_source": "grub_mkstandalone",
                "bootx64_iso_copied": False,
                "bootx64_sha256": "same",
                "iso_bootx64_sha256": "same",
            }
            (root / "setuphelfer/rescue/evidence.json").write_text(
                __import__("json").dumps(evidence), encoding="utf-8"
            )
            result = verify.validate_fat32_esp_bootx64_on_mount(root)
            self.assertFalse(result["ok"])
            self.assertIn(verify.BOOTX64_ERROR_ISO_COPIED, result["errors"])

    def test_bootx64_verify_ok_standalone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "EFI/BOOT").mkdir(parents=True)
            (root / "EFI/BOOT/BOOTX64.EFI").write_bytes(b"x")
            (root / "setuphelfer/rescue").mkdir(parents=True)
            evidence = {
                "bootx64_source": "grub_mkstandalone",
                "bootx64_iso_copied": False,
                "bootx64_sha256": "standalone",
                "iso_bootx64_sha256": "iso",
            }
            (root / "setuphelfer/rescue/evidence.json").write_text(
                __import__("json").dumps(evidence), encoding="utf-8"
            )
            result = verify.validate_fat32_esp_bootx64_on_mount(root)
            self.assertTrue(result["ok"], result["errors"])

    def test_expected_squashfs_hash_match_ok(self) -> None:
        expected = "ac95ebc3bdc4693da56d51cda1bb3f5fd36dc68d18b2ff1e8f76aad30a85f00a"
        result = verify.evaluate_expected_squashfs_sha256(
            actual_sha256=expected,
            expected_sha256=expected,
        )
        self.assertTrue(result["checked"])
        self.assertTrue(result["ok"])
        self.assertIsNone(result["message"])

    def test_expected_squashfs_hash_mismatch_fails(self) -> None:
        result = verify.evaluate_expected_squashfs_sha256(
            actual_sha256="921c3e23bfbeb99a6295b80be5f8b5d40b55994019b0e614fef633138c6bdfe7",
            expected_sha256="ac95ebc3bdc4693da56d51cda1bb3f5fd36dc68d18b2ff1e8f76aad30a85f00a",
        )
        self.assertTrue(result["checked"])
        self.assertFalse(result["ok"])
        self.assertIn("hash mismatch", result["message"] or "")

    def test_expected_squashfs_hash_omitted_skips_gate(self) -> None:
        result = verify.evaluate_expected_squashfs_sha256(
            actual_sha256="anything",
            expected_sha256=None,
        )
        self.assertFalse(result["checked"])
        self.assertTrue(result["ok"])

    def test_verify_script_supports_expected_hash_flag(self) -> None:
        script = Path(__file__).resolve().parents[2] / "scripts/rescue-live/verify-fat32-esp-rescue-usb.sh"
        text = script.read_text(encoding="utf-8")
        self.assertIn("--expected-squashfs-sha256", text)
        self.assertIn("evaluate_expected_squashfs_sha256", text)

    def test_grub_validate_rejects_iso_file_search(self) -> None:
        bad = (
            "search --set=root --file /live/filesystem.squashfs\n"
            "menuentry \"x\" { linux /live/vmlinuz boot=live\n initrd /live/initrd.img }\n"
        )
        result = verify.validate_fat32_esp_grub_cfg(bad)
        self.assertFalse(result["ok"])
        self.assertIn(verify.GRUB_ERROR_ROOT, result["errors"])


if __name__ == "__main__":
    unittest.main()
