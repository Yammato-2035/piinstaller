"""GRUB branding for FAT32 ESP rescue USB — theme staging and validation (no USB writes)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Sequence

GRUB_THEME_DIR_REL = "boot/grub/themes/setuphelfer"
GRUB_THEME_FILE = "theme.txt"
GRUB_BACKGROUND_FILE = "setuphelfer-boot-menu-de.png"

GRUB_GFX_MODULES: tuple[str, ...] = (
    "gfxterm",
    "png",
    "all_video",
    "efi_gop",
)

BOOTX64_GFX_MODULES: tuple[str, ...] = (
    "gfxterm",
    "png",
    "all_video",
    "efi_gop",
)


def generate_grub_theme_txt() -> str:
    return """# Setuphelfer GRUB theme — background/branding only; menu entries remain in grub.cfg
desktop-image: "setuphelfer-boot-menu-de.png"
title-text: "Setuphelfer Rettung"
title-color: "#ffffff"
message-color: "#e2e8f0"
"""


def generate_grub_cfg_branding_lines() -> list[str]:
    return [
        "insmod gfxterm",
        "insmod png",
        "insmod all_video",
        "set gfxmode=auto",
        "set gfxpayload=keep",
        f'set theme=($root)/{GRUB_THEME_DIR_REL}/{GRUB_THEME_FILE}',
    ]


def stage_grub_theme_to_fat32_staging(staging_dir: Path, repo_root: Path) -> dict[str, Any]:
    """Copy theme assets into FAT32 ESP staging tree."""
    assets_root = repo_root / "assets" / "rescue"
    bg_src = assets_root / "boot-menu" / GRUB_BACKGROUND_FILE
    theme_dst_dir = staging_dir / GRUB_THEME_DIR_REL
    theme_dst_dir.mkdir(parents=True, exist_ok=True)
    theme_path = theme_dst_dir / GRUB_THEME_FILE
    theme_path.write_text(generate_grub_theme_txt(), encoding="utf-8")
    staged: list[str] = [str(theme_path.relative_to(staging_dir))]
    if bg_src.is_file():
        bg_dst = theme_dst_dir / GRUB_BACKGROUND_FILE
        bg_dst.write_bytes(bg_src.read_bytes())
        staged.append(str(bg_dst.relative_to(staging_dir)))
    return {
        "theme_dir": GRUB_THEME_DIR_REL,
        "staged_files": staged,
        "background_present": bg_src.is_file(),
        "complete": bg_src.is_file() and theme_path.is_file(),
    }


def grub_cfg_references_theme(grub_text: str) -> bool:
    lowered = grub_text.lower()
    return "set theme=" in lowered or "grub_theme=" in lowered


def grub_cfg_loads_gfx_modules(grub_text: str) -> bool:
    return "insmod gfxterm" in grub_text and "insmod png" in grub_text


def validate_fat32_grub_branding(
    staging_dir: Path,
    grub_cfg_text: str,
    *,
    bootx64_modules: Sequence[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    theme_dir = staging_dir / GRUB_THEME_DIR_REL
    theme_file = theme_dir / GRUB_THEME_FILE
    bg_file = theme_dir / GRUB_BACKGROUND_FILE
    if not theme_file.is_file():
        errors.append("GRUB_THEME_TXT_MISSING")
    if not bg_file.is_file():
        errors.append("GRUB_BACKGROUND_PNG_MISSING")
    if not grub_cfg_references_theme(grub_cfg_text):
        errors.append("GRUB_CFG_THEME_NOT_REFERENCED")
    if not grub_cfg_loads_gfx_modules(grub_cfg_text):
        errors.append("GRUB_CFG_GFX_MODULES_MISSING")
    if bootx64_modules is not None:
        missing = [m for m in BOOTX64_GFX_MODULES if m not in bootx64_modules]
        if missing:
            errors.append(f"BOOTX64_GFX_MODULES_MISSING:{','.join(missing)}")
    manifest = staging_dir / "setuphelfer" / "rescue" / "asset-manifest.json"
    if manifest.is_file():
        text = manifest.read_text(encoding="utf-8")
        for rel in (GRUB_BACKGROUND_FILE, GRUB_THEME_FILE):
            if rel not in text:
                errors.append(f"MANIFEST_MISSING:{rel}")
    theme_txt = theme_file.read_text(encoding="utf-8") if theme_file.is_file() else ""
    if theme_txt and "desktop-image" not in theme_txt:
        errors.append("THEME_TXT_NO_DESKTOP_IMAGE")
    if re.search(r'terminal-box:\s*"terminal_box', theme_txt):
        errors.append("THEME_TXT_TERMINAL_BOX_WITHOUT_ASSETS")
    return errors
