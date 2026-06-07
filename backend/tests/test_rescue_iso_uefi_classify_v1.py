from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from core.rescue_iso_uefi_classify import (
    UefiIsoSignals,
    classify_rescue_uefi_gate,
    classify_uefi_iso,
    collect_uefi_iso_signals,
)


class RescueIsoUefiClassifyTests(unittest.TestCase):
    def test_isolinux_only_iso(self) -> None:
        signals = UefiIsoSignals(
            iso_exists=True,
            sha256="abc",
            has_bios_boot=True,
            has_efi_eltorito=False,
            has_bootx64_efi=False,
            xorriso_report_excerpt="-b '/isolinux/isolinux.bin'",
        )
        result = classify_uefi_iso(signals)
        self.assertFalse(result["uefi_boot_ready"])
        self.assertIn("isolinux_only_iso", result["classifications"])
        codes = {e["code"] for e in result["errors"]}
        self.assertIn("RESCUE-UEFI-003", codes)
        self.assertIn("RESCUE-UEFI-002", codes)
        self.assertIn("RESCUE-UEFI-001", codes)

    def test_bootx64_without_eltorito(self) -> None:
        signals = UefiIsoSignals(
            iso_exists=True,
            sha256="abc",
            has_bios_boot=True,
            has_efi_eltorito=False,
            has_bootx64_efi=True,
            xorriso_report_excerpt="-b '/isolinux/isolinux.bin'",
        )
        result = classify_uefi_iso(signals)
        self.assertFalse(result["uefi_boot_ready"])
        self.assertEqual(result["status"], "bootx64_without_eltorito")
        codes = {e["code"] for e in result["errors"]}
        self.assertIn("RESCUE-UEFI-007", codes)
        self.assertIn("RESCUE-UEFI-002", codes)

    def test_uefi_ready_iso(self) -> None:
        signals = UefiIsoSignals(
            iso_exists=True,
            sha256="def",
            has_bios_boot=True,
            has_efi_eltorito=True,
            has_bootx64_efi=True,
            has_plain_eltorito_uefi=True,
            has_boot_catalog=True,
            has_hybrid_usb_layout=True,
            efi_img_bootable_fat=True,
            xorriso_report_excerpt="-e boot/grub/efi.img",
        )
        result = classify_uefi_iso(signals)
        self.assertTrue(result["uefi_boot_ready"])
        self.assertEqual(result["status"], "uefi_x64_boot_ready")
        self.assertEqual(result["errors"], [])

    def test_files_present_but_no_plain_uefi_entry_fails_deep(self) -> None:
        signals = UefiIsoSignals(
            iso_exists=True,
            sha256="abc",
            has_bios_boot=True,
            has_efi_eltorito=True,
            has_bootx64_efi=True,
            has_plain_eltorito_uefi=False,
            has_boot_catalog=False,
            has_hybrid_usb_layout=True,
            efi_img_bootable_fat=True,
            xorriso_report_excerpt="-e boot/grub/efi.img",
        )
        result = classify_uefi_iso(signals)
        self.assertFalse(result["uefi_boot_ready"])
        codes = {e["code"] for e in result["errors"]}
        self.assertIn("RESCUE-UEFI-008", codes)

    def test_hybrid_layout_incomplete_fails_deep(self) -> None:
        signals = UefiIsoSignals(
            iso_exists=True,
            sha256="abc",
            has_bios_boot=True,
            has_efi_eltorito=True,
            has_bootx64_efi=True,
            has_plain_eltorito_uefi=True,
            has_boot_catalog=True,
            has_hybrid_usb_layout=False,
            efi_img_bootable_fat=True,
        )
        result = classify_uefi_iso(signals)
        self.assertFalse(result["uefi_boot_ready"])
        codes = {e["code"] for e in result["errors"]}
        self.assertIn("RESCUE-UEFI-009", codes)

    @patch("core.rescue_iso_uefi_classify._xorriso_find", return_value=False)
    @patch("core.rescue_iso_uefi_classify._xorriso_report")
    @patch("core.rescue_iso_uefi_classify._sha256", return_value="1899f5c")
    def test_collect_signals_missing_uefi(
        self,
        sha_mock,
        report_mock,
        find_mock,
    ) -> None:
        report_mock.return_value = "-b '/isolinux/isolinux.bin'\n-no-emul-boot"
        iso = Path("/tmp/fake.iso")
        with patch.object(Path, "is_file", return_value=True):
            signals = collect_uefi_iso_signals(iso)
        self.assertTrue(signals.has_bios_boot)
        self.assertFalse(signals.has_efi_eltorito)
        self.assertFalse(signals.has_bootx64_efi)

    def test_gate_blocks_windows_inspect_when_msi_failed(self) -> None:
        signals = UefiIsoSignals(
            iso_exists=True,
            sha256="abc",
            has_bios_boot=True,
            has_efi_eltorito=True,
            has_bootx64_efi=True,
            xorriso_report_excerpt="ok",
        )
        with patch(
            "core.rescue_iso_uefi_classify.load_gate_overlay",
            return_value={"msi_uefi_boot_failed_confirmed": True},
        ), patch(
            "core.rescue_iso_uefi_classify.collect_uefi_iso_signals",
            return_value=signals,
        ):
            gate = classify_rescue_uefi_gate(
                iso_path=Path("/tmp/ok.iso"),
                gate_status_path=Path("/tmp/rescue_iso_usb_gate_status_latest.json"),
            )
        self.assertFalse(gate["windows_inspect_executable"])
        self.assertTrue(
            any(b["id"] == "RESCUE_USB_UEFI_BOOT_FAILURE_MSI_WINDOWS11" for b in gate["blockers"])
        )
        self.assertIn(
            "windows_inspect_blocked_by_rescue_uefi_boot",
            gate["iso_classification"]["classifications"],
        )


if __name__ == "__main__":
    unittest.main()
