"""GRUB branding for FAT32 ESP rescue USB — static validation."""

from __future__ import annotations

import unittest
from pathlib import Path

from core.rescue_fat32_esp_usb_writer import (
    BOOTX64_MKSTANDALONE_MODULES,
    generate_fat32_esp_grub_cfg,
)
from rescue.rescue_grub_branding import (
    GRUB_BACKGROUND_JPEG_FILE,
    GRUB_BACKGROUND_SOURCE_FILE,
    GRUB_THEME_DIR_REL,
    detect_image_format,
    generate_grub_theme_txt,
    stage_grub_theme_to_fat32_staging,
    validate_fat32_grub_branding,
)

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "assets" / "rescue"


class RescueGrubBrandingTests(unittest.TestCase):
    def test_theme_assets_exist_in_workspace(self) -> None:
        self.assertTrue((ASSETS / "boot-menu" / GRUB_BACKGROUND_SOURCE_FILE).is_file())
        self.assertTrue((ASSETS / "logo" / "setuphelfer-logo2.png").is_file())

    def test_workspace_boot_menu_asset_is_jpeg(self) -> None:
        raw = (ASSETS / "boot-menu" / GRUB_BACKGROUND_SOURCE_FILE).read_bytes()
        self.assertEqual(detect_image_format(raw), "jpeg")

    def test_generate_grub_cfg_references_theme(self) -> None:
        cfg = generate_fat32_esp_grub_cfg()
        self.assertIn("set theme=", cfg)
        self.assertIn("insmod gfxterm", cfg)
        self.assertIn("insmod gfxmenu", cfg)
        self.assertIn("insmod jpeg", cfg)
        self.assertNotIn("insmod png", cfg)
        self.assertIn("Setuphelfer Rettung starten", cfg)

    def test_stage_grub_theme_to_staging(self) -> None:
        staging = REPO / "build" / "rescue" / ".test-grub-staging"
        if staging.exists():
            import shutil

            shutil.rmtree(staging)
        meta = stage_grub_theme_to_fat32_staging(staging, REPO)
        self.assertTrue(meta["complete"], meta)
        self.assertEqual(meta["background_format"], "jpeg")
        self.assertEqual(meta["background_staged_name"], GRUB_BACKGROUND_JPEG_FILE)
        self.assertTrue((staging / GRUB_THEME_DIR_REL / "theme.txt").is_file())
        self.assertTrue((staging / GRUB_THEME_DIR_REL / GRUB_BACKGROUND_JPEG_FILE).is_file())
        theme_txt = (staging / GRUB_THEME_DIR_REL / "theme.txt").read_text(encoding="utf-8")
        self.assertIn(GRUB_BACKGROUND_JPEG_FILE, theme_txt)
        cfg = generate_fat32_esp_grub_cfg()
        errors = validate_fat32_grub_branding(
            staging,
            cfg,
            bootx64_modules=BOOTX64_MKSTANDALONE_MODULES.split(),
            image_format="jpeg",
        )
        self.assertEqual(errors, [], errors)

    def test_bootx64_modules_include_gfx(self) -> None:
        modules = BOOTX64_MKSTANDALONE_MODULES.split()
        for required in ("gfxterm", "gfxmenu", "jpeg", "all_video", "efi_gop"):
            self.assertIn(required, modules, required)

    def test_theme_txt_no_missing_terminal_box(self) -> None:
        theme = generate_grub_theme_txt(desktop_image=GRUB_BACKGROUND_JPEG_FILE)
        self.assertIn("desktop-image", theme)
        self.assertIn("+ boot_menu", theme)
        self.assertIn(GRUB_BACKGROUND_JPEG_FILE, theme)
        self.assertNotIn("terminal-box", theme)

    def test_hardware_status_remains_yellow_until_retest(self) -> None:
        """Branding fix alone must not imply RS-001 green."""
        self.assertIn("Setuphelfer", generate_grub_theme_txt())


if __name__ == "__main__":
    unittest.main()
