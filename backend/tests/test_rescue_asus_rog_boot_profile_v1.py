"""Unit tests: ASUS ROG boot profile + BIOS/Win11 gate."""

from __future__ import annotations

import unittest

from core.rescue_asus_rog_boot_profile import (
    dmi_suggests_asus_rog,
    evaluate_asus_rog_bios_win11_gate,
    resolve_asus_rog_boot_profile,
)
from core.rescue_asus_rog_lab_boot import (
    ASUS_ROG_LAB_MENU_TITLE,
    patch_grub_cfg_for_asus_rog_and_pi5_lab,
)


class AsusRogProfileTests(unittest.TestCase):
    def test_dmi_detects_rog_strix(self) -> None:
        self.assertTrue(
            dmi_suggests_asus_rog(
                {
                    "sys_vendor": "ASUSTeK COMPUTER INC.",
                    "product_name": "ROG Strix G16",
                    "product_version": "1.0",
                    "board_vendor": "ASUSTeK",
                    "board_name": "G614JV",
                }
            )
        )

    def test_dmi_rejects_msi(self) -> None:
        self.assertFalse(
            dmi_suggests_asus_rog(
                {
                    "sys_vendor": "Micro-Star International",
                    "product_name": "GE63 Raider",
                    "product_version": "",
                    "board_vendor": "MSI",
                    "board_name": "MS-16P5",
                }
            )
        )

    def test_profile_gui_capable(self) -> None:
        p = resolve_asus_rog_boot_profile(
            "setuphelfer_asus_rog_lab=1",
            dmi={"sys_vendor": "ASUS", "product_name": "ROG", "product_version": "", "board_vendor": "", "board_name": ""},
        )
        self.assertTrue(p["active"])
        self.assertTrue(p["gui_start_allowed"])
        self.assertEqual(p["boot_mode"], "gui_capable")

    def test_gate_does_not_block_bvr(self) -> None:
        g = evaluate_asus_rog_bios_win11_gate(
            dmi={
                "sys_vendor": "ASUSTeK",
                "product_name": "ROG Strix",
                "product_version": "",
                "board_vendor": "ASUS",
                "board_name": "STRIX",
            },
            cmdline="setuphelfer_asus_rog_lab=1",
        )
        self.assertFalse(g["blocks_bvr"])
        self.assertTrue(g["asus_rog_detected"])
        self.assertTrue(any(a for a in g["operator_next_actions"]))

    def test_grub_patch_inserts_entries(self) -> None:
        grub = 'set timeout=3\nmenuentry "Other" {\n  linux /live/vmlinuz\n  initrd /live/initrd.img\n}\n'
        out = patch_grub_cfg_for_asus_rog_and_pi5_lab(grub)
        self.assertIn(ASUS_ROG_LAB_MENU_TITLE, out)
        self.assertIn("setuphelfer_asus_rog_lab=1", out)
        self.assertIn("setuphelfer_pi5_lab=1", out)
        self.assertIn("modprobe.blacklist=nouveau", out)
        # MSI/default menuentry stays before ASUS lab entries.
        self.assertLess(out.find('menuentry "Other"'), out.find(ASUS_ROG_LAB_MENU_TITLE))


if __name__ == "__main__":
    unittest.main()
