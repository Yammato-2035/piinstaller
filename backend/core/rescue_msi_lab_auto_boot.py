"""PI-RS-MSI-AUTO-EVIDENCE-001 — GRUB defaults and lab cmdline for unattended MSI boot."""

from __future__ import annotations

import re

MSI_COMPAT_MENU_TITLE = "Setuphelfer MSI/NVIDIA Kompatibilitaetsmodus (Text)"
# 001D7B: auto-discovery explicit; physical E2E gated by run-mode / start-gate.
MSI_LAB_CMDLINE_FLAGS = (
    "setuphelfer_msi_lab_auto=1 setuphelfer_auto_discovery=1 "
    "setuphelfer_msi_e2e_auto=0 setuphelfer_auto_shutdown=1 "
    "setuphelfer_msi_lab_late_sec=120"
)
MSI_LAB_DEFAULT_TIMEOUT = 3


def msi_compat_menu_append(base_live: str) -> str:
    return (
        f"{base_live} setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_msi_compat=1 "
        "pci=noaer nouveau.modeset=0 nomodeset"
    )


def msi_lab_auto_menu_append(base_live: str) -> str:
    return f"{msi_compat_menu_append(base_live)} {MSI_LAB_CMDLINE_FLAGS}"


def _first_menuentry_index(text: str) -> int:
    return text.find('menuentry "')


def _extract_menuentry_block(text: str, title: str) -> tuple[str, str, str]:
    needle = f'menuentry "{title}"'
    start = text.find(needle)
    if start < 0:
        raise ValueError("MSI_COMPAT_MENU_ENTRY_NOT_FOUND")
    end = text.find("\n}", start)
    if end < 0:
        raise ValueError("MSI_COMPAT_MENU_ENTRY_MALFORMED")
    end += 2
    return text[:start], text[start:end], text[end:]


def _ensure_msi_lab_cmdline_flags(msi_block: str) -> str:
    out = msi_block
    if "setuphelfer_msi_lab_auto=1" not in out:
        out = re.sub(
            r"(setuphelfer_msi_compat=1\s+pci=noaer nouveau\.modeset=0 nomodeset)",
            rf"\1 {MSI_LAB_CMDLINE_FLAGS}",
            out,
            count=1,
        )
    # Discovery-first lab boot: never leave stale physical-E2E auto=1.
    out = re.sub(r"\bsetuphelfer_msi_e2e_auto=1\b", "setuphelfer_msi_e2e_auto=0", out)
    for flag in MSI_LAB_CMDLINE_FLAGS.split():
        key = flag.split("=", 1)[0]
        if re.search(rf"\b{re.escape(key)}=", out):
            out = re.sub(rf"\b{re.escape(key)}=\S+", flag, out, count=1)
        else:
            out = re.sub(
                r"(setuphelfer_msi_lab_auto=1)",
                rf"\1 {flag}",
                out,
                count=1,
            )
    return out


def patch_grub_cfg_for_msi_lab_auto_boot(grub_text: str) -> str:
    """Set MSI compat as first menu entry with short countdown and lab cmdline flags."""
    first_menu = _first_menuentry_index(grub_text)
    if first_menu < 0:
        raise ValueError("GRUB_MENU_ENTRIES_NOT_FOUND")

    before_msi, original_msi_block, after_msi = _extract_menuentry_block(grub_text, MSI_COMPAT_MENU_TITLE)
    msi_block = _ensure_msi_lab_cmdline_flags(original_msi_block)
    without_msi = before_msi + after_msi
    first_menu = _first_menuentry_index(without_msi)
    if first_menu < 0:
        raise ValueError("GRUB_MENU_ENTRIES_NOT_FOUND")
    preamble = without_msi[:first_menu]
    other_entries = without_msi[first_menu:].lstrip("\n")

    lines: list[str] = []
    for line in preamble.splitlines():
        stripped = line.strip()
        if stripped.startswith("set default="):
            lines.append("set default=0")
            continue
        if stripped.startswith("set timeout="):
            lines.append(f"set timeout={MSI_LAB_DEFAULT_TIMEOUT}")
            continue
        if stripped.startswith("set timeout_style="):
            lines.append("set timeout_style=countdown")
            continue
        lines.append(line)
    header = "\n".join(lines).rstrip() + "\n\n"
    return f"{header}{msi_block}\n{other_entries}"
