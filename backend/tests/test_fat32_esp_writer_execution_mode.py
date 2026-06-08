"""Tests for FAT32 ESP writer --execute-write gates and execution plan (no real devices)."""

from __future__ import annotations

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

CANONICAL_SHA = "c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194"


def _mock_usb_device(*, mounted: bool = False, device: str = "/dev/sdb"):
    mock_cd = type(
        "CD",
        (),
        {
            "id": device,
            "name": device.rsplit("/", 1)[-1],
            "type": "disk",
            "size": "58G",
            "removable": True,
            "mountpoints": ["/mnt/usb"] if mounted else [],
            "filesystems": [],
            "partitions": [],
            "is_system_disk": False,
            "is_boot_disk": False,
            "is_foreign_os_disk": False,
            "is_write_allowed": False,
        },
    )()
    row = {
        "device": device,
        "selectable": True,
        "transport": "usb",
        "size": "58G",
    }
    return mock_cd, row


def _valid_evidence(device: str = "/dev/sdb") -> dict:
    return {
        "write_allowed": True,
        "selected_device": device,
        "operator_confirmations": {k: True for k in REQUIRED_CONFIRMATIONS},
    }


def _staging_with_required(tmp: Path) -> Path:
    for rel in fat32.STAGING_REQUIRED_PATHS:
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
    return tmp


class Fat32EspWriterExecutionModeTests(unittest.TestCase):
    def test_partition_path_for_target_sd_nvme_mmc(self) -> None:
        self.assertEqual(fat32.partition_path_for_target("/dev/sdb", 1), "/dev/sdb1")
        self.assertEqual(fat32.partition_path_for_target("/dev/nvme0n1", 1), "/dev/nvme0n1p1")
        self.assertEqual(fat32.partition_path_for_target("/dev/mmcblk0", 1), "/dev/mmcblk0p1")

    def test_without_execute_write_flag_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            staging = _staging_with_required(Path(tmp))
            iso = staging / "fake.iso"
            iso.write_bytes(b"iso")
            mock_cd, row = _mock_usb_device()
            with patch.object(fat32, "list_classified_devices", return_value=[mock_cd]):
                with patch.object(fat32, "build_usb_candidates_payload", return_value={"devices": [row]}):
                    with patch.object(fat32, "sha256_file", return_value=CANONICAL_SHA):
                        gates = fat32.validate_fat32_execute_write_gates(
                            target_device="/dev/sdb",
                            iso_path=iso,
                            staging_dir=staging,
                            operator_evidence=_valid_evidence(),
                            confirm_phrase=fat32.CONFIRM_PHRASE_FAT32_ESP,
                            execute_write=False,
                            confirm_write=True,
                            expected_iso_sha256=CANONICAL_SHA,
                        )
        self.assertTrue(gates["blocked"])
        self.assertIn("EXECUTE_WRITE_FLAG_MISSING", gates["blockers"])

    def test_without_confirm_write_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            staging = _staging_with_required(Path(tmp))
            iso = staging / "fake.iso"
            iso.write_bytes(b"iso")
            mock_cd, row = _mock_usb_device()
            with patch.object(fat32, "list_classified_devices", return_value=[mock_cd]):
                with patch.object(fat32, "build_usb_candidates_payload", return_value={"devices": [row]}):
                    with patch.object(fat32, "sha256_file", return_value=CANONICAL_SHA):
                        gates = fat32.validate_fat32_execute_write_gates(
                            target_device="/dev/sdb",
                            iso_path=iso,
                            staging_dir=staging,
                            operator_evidence=_valid_evidence(),
                            confirm_phrase=fat32.CONFIRM_PHRASE_FAT32_ESP,
                            execute_write=True,
                            confirm_write=False,
                            expected_iso_sha256=CANONICAL_SHA,
                        )
        self.assertTrue(gates["blocked"])
        self.assertIn("OPERATOR_CONFIRM_WRITE_MISSING", gates["blockers"])

    def test_wrong_confirm_phrase_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            staging = _staging_with_required(Path(tmp))
            iso = staging / "fake.iso"
            iso.write_bytes(b"iso")
            mock_cd, row = _mock_usb_device()
            with patch.object(fat32, "list_classified_devices", return_value=[mock_cd]):
                with patch.object(fat32, "build_usb_candidates_payload", return_value={"devices": [row]}):
                    with patch.object(fat32, "sha256_file", return_value=CANONICAL_SHA):
                        gates = fat32.validate_fat32_execute_write_gates(
                            target_device="/dev/sdb",
                            iso_path=iso,
                            staging_dir=staging,
                            operator_evidence=_valid_evidence(),
                            confirm_phrase="WRONG PHRASE",
                            execute_write=True,
                            confirm_write=True,
                            expected_iso_sha256=CANONICAL_SHA,
                        )
        self.assertIn("CONFIRM_PHRASE_MISMATCH", gates["blockers"])

    def test_mounted_target_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            staging = _staging_with_required(Path(tmp))
            iso = staging / "fake.iso"
            iso.write_bytes(b"iso")
            mock_cd, row = _mock_usb_device(mounted=True)
            with patch.object(fat32, "list_classified_devices", return_value=[mock_cd]):
                with patch.object(fat32, "build_usb_candidates_payload", return_value={"devices": [row]}):
                    with patch.object(fat32, "sha256_file", return_value=CANONICAL_SHA):
                        gates = fat32.validate_fat32_execute_write_gates(
                            target_device="/dev/sdb",
                            iso_path=iso,
                            staging_dir=staging,
                            operator_evidence=_valid_evidence(),
                            confirm_phrase=fat32.CONFIRM_PHRASE_FAT32_ESP,
                            execute_write=True,
                            confirm_write=True,
                            expected_iso_sha256=CANONICAL_SHA,
                        )
        self.assertTrue(gates["blocked"])
        self.assertIn("TARGET_DEVICE_MOUNTED", gates["blockers"])

    def test_non_usb_target_blocked(self) -> None:
        mock_cd, _ = _mock_usb_device()
        with patch.object(fat32, "list_classified_devices", return_value=[mock_cd]):
            with patch.object(fat32, "build_usb_candidates_payload", return_value={"devices": []}):
                result = fat32.validate_fat32_write_target(
                    "/dev/sdb",
                    operator_evidence=_valid_evidence(),
                    confirm_phrase=fat32.CONFIRM_PHRASE_FAT32_ESP,
                    dry_run=False,
                )
        self.assertIn("DEVICE_NOT_IN_USB_CANDIDATES", result["blockers"])

    def test_evidence_device_mismatch_blocked(self) -> None:
        mock_cd, row = _mock_usb_device(device="/dev/sdb")
        evidence = _valid_evidence(device="/dev/sdc")
        with patch.object(fat32, "list_classified_devices", return_value=[mock_cd]):
            with patch.object(fat32, "build_usb_candidates_payload", return_value={"devices": [row]}):
                result = fat32.validate_fat32_write_target(
                    "/dev/sdb",
                    operator_evidence=evidence,
                    confirm_phrase=fat32.CONFIRM_PHRASE_FAT32_ESP,
                    dry_run=False,
                )
        self.assertIn("EVIDENCE_DEVICE_MISMATCH", result["blockers"])

    def test_valid_usb_gates_unblocked_and_step_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            staging = _staging_with_required(Path(tmp))
            iso = staging / "fake.iso"
            iso.write_bytes(b"iso")
            mock_cd, row = _mock_usb_device()
            with patch.object(fat32, "list_classified_devices", return_value=[mock_cd]):
                with patch.object(fat32, "build_usb_candidates_payload", return_value={"devices": [row]}):
                    with patch.object(fat32, "sha256_file", return_value=CANONICAL_SHA):
                        gates = fat32.validate_fat32_execute_write_gates(
                            target_device="/dev/sdb",
                            iso_path=iso,
                            staging_dir=staging,
                            operator_evidence=_valid_evidence(),
                            confirm_phrase=fat32.CONFIRM_PHRASE_FAT32_ESP,
                            execute_write=True,
                            confirm_write=True,
                            expected_iso_sha256=CANONICAL_SHA,
                        )
        self.assertFalse(gates["blocked"])
        self.assertTrue(gates["write_allowed"])
        self.assertEqual(gates["target_partition"], "/dev/sdb1")
        steps = gates["execution_step_ids"]
        self.assertEqual(steps[0], "wipefs_probe")
        self.assertEqual(steps[-1], "verify_fat32_esp")
        self.assertLess(steps.index("mkfs_vfat"), steps.index("rsync_staging"))
        self.assertLess(steps.index("patch_grub_uuid"), steps.index("mount_esp"))

    def test_dry_run_plan_never_executes_write(self) -> None:
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
        self.assertFalse(plan["write_executed"])
        self.assertEqual(plan["mode"], "dry_run")

    def test_operator_write_command_includes_execute_write(self) -> None:
        cmds = fat32.build_operator_terminal_commands(
            iso_path=Path("/tmp/fake.iso"),
            target_device="/dev/sdb",
            workspace=Path("/tmp/ws"),
        )
        self.assertIn("--execute-write", cmds["write"])
        self.assertNotIn("--execute-write", cmds["write_prepared"])

    def test_write_result_rs001_stays_red(self) -> None:
        result = fat32.build_fat32_esp_write_result(
            target_device="/dev/sdb",
            iso_path=Path("/tmp/iso"),
            iso_sha256=CANONICAL_SHA,
            started_at="2026-06-08T00:00:00Z",
            completed_at="2026-06-08T00:05:00Z",
            write_executed=True,
            write_status="success",
            failed_step=None,
            fat_uuid="ABCD-1234",
            pre_state={},
            post_state={},
            verify_status="success",
        )
        self.assertEqual(result["rs001_status"], "red")
        self.assertIn("hardware boot", result["rs001_reason"].lower())


if __name__ == "__main__":
    unittest.main()
