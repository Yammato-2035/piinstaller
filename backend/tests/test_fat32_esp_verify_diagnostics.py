"""Tests for FAT32 ESP verify structural vs label-only repair diagnostics."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_fat32_esp_usb_verify as verify  # noqa: E402

EFI = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"


class Fat32EspVerifyDiagnosticsTests(unittest.TestCase):
    def test_dos_exfat_no_label_only_repair(self) -> None:
        result = verify.evaluate_verify_probe(
            parent_pttype="dos",
            parent_signature_types=[],
            part_parttype="0x7",
            part_partlabel="",
            part_fstype="exfat",
            part_fat_label="INTENSO",
            target_device="/dev/sdb",
            partition_device="/dev/sdb1",
        )
        self.assertFalse(result["ok"])
        self.assertFalse(result["structural_layout_valid"])
        warnings_blob = "\n".join(result["warnings"])
        self.assertIn(verify.STRUCTURAL_LAYOUT_INVALID, warnings_blob)
        self.assertIn(verify.STRUCTURAL_RERUN_EXECUTE, warnings_blob)
        for err in result["errors"]:
            self.assertNotIn("fatlabel", err.get("message", "").lower())

    def test_label_only_repair_when_structure_valid(self) -> None:
        result = verify.evaluate_verify_probe(
            parent_pttype="gpt",
            parent_signature_types=[],
            part_parttype=EFI,
            part_partlabel="SETUPHELFER_RESCUE",
            part_fstype="vfat",
            part_fat_label="INTENSO",
            target_device="/dev/sdb",
            partition_device="/dev/sdb1",
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result["structural_layout_valid"])
        label_err = next(e for e in result["errors"] if e["code"] == "FAT_LABEL_MISMATCH")
        self.assertIn("fatlabel", label_err["message"].lower())
        self.assertIn("/dev/sdb1", label_err["message"])
        warnings_blob = "\n".join(result["warnings"])
        self.assertNotIn(verify.STRUCTURAL_LAYOUT_INVALID, warnings_blob)

    def test_valid_layout_no_structural_warnings(self) -> None:
        result = verify.evaluate_verify_probe(
            parent_pttype="gpt",
            parent_signature_types=[],
            part_parttype=EFI,
            part_partlabel="SETUPHELFER_RESCUE",
            part_fstype="vfat",
            part_fat_label="SETUPHELFER",
            target_device="/dev/sdb",
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["structural_layout_valid"])
        self.assertEqual(result["warnings"], [])


if __name__ == "__main__":
    unittest.main()
