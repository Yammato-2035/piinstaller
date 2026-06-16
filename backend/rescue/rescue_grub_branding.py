"""GRUB branding for FAT32 ESP rescue USB — theme staging and validation (no USB writes)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Sequence

GRUB_THEME_DIR_REL = "boot/grub/themes/setuphelfer"
GRUB_THEME_FILE = "theme.txt"
# Workspace asset name (historical .png suffix; file may contain JPEG bytes).
GRUB_BACKGROUND_SOURCE_FILE = "setuphelfer-boot-menu-de.png"
GRUB_BACKGROUND_JPEG_FILE = "setuphelfer-boot-menu-de.jpg"
GRUB_BACKGROUND_PNG_FILE = "setuphelfer-boot-menu-de.png"
GRUB_FONT_FILE = "unicode.pf2"

GRUB_HOST_FONT_CANDIDATES: tuple[str, ...] = (
    "/usr/share/grub/unicode.pf2",
    "/boot/grub/fonts/unicode.pf2",
)

GRUB_GFX_MODULES: tuple[str, ...] = (
    "gfxterm",
    "gfxmenu",
    "jpeg",
    "png",
    "all_video",
    "efi_gop",
    "efi_uga",
    "video",
)

BOOTX64_GFX_MODULES: tuple[str, ...] = GRUB_GFX_MODULES

# Backward-compatible alias used by tests and asset manifest paths.
GRUB_BACKGROUND_FILE = GRUB_BACKGROUND_SOURCE_FILE


def detect_image_format(data: bytes) -> str:
    if data.startswith(b"\xff\xd8"):
        return "jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    return "unknown"


def staged_background_filename(image_format: str) -> str:
    if image_format == "jpeg":
        return GRUB_BACKGROUND_JPEG_FILE
    return GRUB_BACKGROUND_PNG_FILE


def generate_grub_theme_txt(*, desktop_image: str | None = None) -> str:
    image = desktop_image or GRUB_BACKGROUND_PNG_FILE
    # desktop-image is branding only; mockup PNG contains painted buttons — real entries
    # come from grub.cfg menuentry blocks, positioned via boot_menu below.
    return f"""# Setuphelfer GRUB theme — branded boot picker (kernel variants only)
desktop-image: "{image}"
title-text: ""
title-color: "#ffffff"
message-color: "#e2e8f0"

+ boot_menu {{
  left = 8%
  width = 84%
  top = 52%
  height = 42%
  item_color = "#e2e8f0"
  selected_item_color = "#ffffff"
  item_height = 32
  item_padding = 10
  item_spacing = 6
  scrollbar = false
  scrollbar_width = 0
}}
"""


def generate_grub_cfg_branding_lines(*, image_format: str = "jpeg") -> list[str]:
    # Workspace boot-menu asset is JPEG-with-.png-suffix; GRUB needs `insmod jpeg` and a
    # matching .jpg desktop-image or theme load fails silently → text fallback on hardware.
    lines = [
        "insmod efi_gop",
        "insmod efi_uga",
        "insmod gfxterm",
        "insmod gfxmenu",
        "insmod all_video",
        "insmod video",
    ]
    if image_format == "jpeg":
        lines.append("insmod jpeg")
    else:
        lines.append("insmod png")
    lines.extend(
        [
            f'if [ -f ($root)/{GRUB_THEME_DIR_REL}/{GRUB_FONT_FILE} ]; then',
            f"  loadfont ($root)/{GRUB_THEME_DIR_REL}/{GRUB_FONT_FILE}",
            "fi",
            "set gfxmode=auto",
            "set gfxpayload=keep",
            "terminal_output gfxterm",
            "terminal_input gfxterm",
            f'set theme=($root)/{GRUB_THEME_DIR_REL}/{GRUB_THEME_FILE}',
        ]
    )
    return lines


def stage_grub_theme_to_fat32_staging(staging_dir: Path, repo_root: Path) -> dict[str, Any]:
    """Copy theme assets into FAT32 ESP staging tree."""
    assets_root = repo_root / "assets" / "rescue"
    bg_src = assets_root / "boot-menu" / GRUB_BACKGROUND_SOURCE_FILE
    theme_dst_dir = staging_dir / GRUB_THEME_DIR_REL
    theme_dst_dir.mkdir(parents=True, exist_ok=True)

    image_format = "unknown"
    background_staged = ""
    background_present = False
    if bg_src.is_file():
        raw = bg_src.read_bytes()
        image_format = detect_image_format(raw)
        background_staged = staged_background_filename(image_format)
        bg_dst = theme_dst_dir / background_staged
        bg_dst.write_bytes(raw)
        staged_bg_rel = str(bg_dst.relative_to(staging_dir))
        background_present = True
    else:
        staged_bg_rel = ""

    theme_path = theme_dst_dir / GRUB_THEME_FILE
    theme_path.write_text(
        generate_grub_theme_txt(
            desktop_image=background_staged or GRUB_BACKGROUND_PNG_FILE,
        ),
        encoding="utf-8",
    )
    staged: list[str] = [str(theme_path.relative_to(staging_dir))]
    if staged_bg_rel:
        staged.append(staged_bg_rel)

    font_staged = False
    for font_src in GRUB_HOST_FONT_CANDIDATES:
        src = Path(font_src)
        if src.is_file():
            font_dst = theme_dst_dir / GRUB_FONT_FILE
            font_dst.write_bytes(src.read_bytes())
            staged.append(str(font_dst.relative_to(staging_dir)))
            font_staged = True
            break

    return {
        "theme_dir": GRUB_THEME_DIR_REL,
        "staged_files": staged,
        "background_present": background_present,
        "background_format": image_format,
        "background_staged_name": background_staged or None,
        "font_present": font_staged,
        "complete": background_present and theme_path.is_file() and font_staged and image_format != "unknown",
    }


def grub_cfg_references_theme(grub_text: str) -> bool:
    lowered = grub_text.lower()
    return "set theme=" in lowered or "grub_theme=" in lowered


def grub_cfg_loads_gfx_modules(grub_text: str, *, image_format: str = "jpeg") -> bool:
    if "insmod gfxterm" not in grub_text or "insmod gfxmenu" not in grub_text:
        return False
    if image_format == "jpeg":
        return "insmod jpeg" in grub_text
    return "insmod png" in grub_text


def validate_fat32_grub_branding(
    staging_dir: Path,
    grub_cfg_text: str,
    *,
    bootx64_modules: Sequence[str] | None = None,
    image_format: str = "jpeg",
) -> list[str]:
    errors: list[str] = []
    theme_dir = staging_dir / GRUB_THEME_DIR_REL
    theme_file = theme_dir / GRUB_THEME_FILE
    if not theme_file.is_file():
        errors.append("GRUB_THEME_TXT_MISSING")
        return errors

    theme_txt = theme_file.read_text(encoding="utf-8")
    desktop_match = re.search(r'desktop-image:\s*"([^"]+)"', theme_txt)
    desktop_name = desktop_match.group(1) if desktop_match else ""
    bg_file = theme_dir / desktop_name if desktop_name else theme_dir / GRUB_BACKGROUND_JPEG_FILE
    if not bg_file.is_file():
        errors.append("GRUB_BACKGROUND_IMAGE_MISSING")

    font_file = theme_dir / GRUB_FONT_FILE
    if not font_file.is_file():
        errors.append("GRUB_FONT_MISSING")
    if not grub_cfg_references_theme(grub_cfg_text):
        errors.append("GRUB_CFG_THEME_NOT_REFERENCED")
    if not grub_cfg_loads_gfx_modules(grub_cfg_text, image_format=image_format):
        errors.append("GRUB_CFG_GFX_MODULES_MISSING")
    if bootx64_modules is not None:
        missing = [m for m in BOOTX64_GFX_MODULES if m not in bootx64_modules]
        if missing:
            errors.append(f"BOOTX64_GFX_MODULES_MISSING:{','.join(missing)}")
    manifest = staging_dir / "setuphelfer" / "rescue" / "asset-manifest.json"
    if manifest.is_file():
        text = manifest.read_text(encoding="utf-8")
        for rel in (desktop_name, GRUB_THEME_FILE):
            if rel and rel not in text:
                errors.append(f"MANIFEST_MISSING:{rel}")
    if theme_txt and "desktop-image" not in theme_txt:
        errors.append("THEME_TXT_NO_DESKTOP_IMAGE")
    if re.search(r'terminal-box:\s*"terminal_box', theme_txt):
        errors.append("THEME_TXT_TERMINAL_BOX_WITHOUT_ASSETS")
    if image_format == "jpeg" and desktop_name.endswith(".png"):
        errors.append("GRUB_DESKTOP_IMAGE_JPEG_MISMATCH_PNG_EXT")
    return errors
