"""PI-RS-MSI-AUTO-EVIDENCE-001 — GRUB defaults and lab cmdline for unattended MSI boot."""

from __future__ import annotations

import re

MSI_COMPAT_MENU_TITLE = "Setuphelfer MSI/NVIDIA Kompatibilitaetsmodus (Text)"
GUI_MENU_TITLE = "Setuphelfer starten - grafische Oberflaeche"
# 001D7B: auto-discovery explicit; physical E2E gated by run-mode / start-gate.
MSI_LAB_CMDLINE_FLAGS = (
    "setuphelfer_msi_lab_auto=1 setuphelfer_auto_discovery=1 "
    "setuphelfer_msi_e2e_auto=0 setuphelfer_auto_shutdown=0 "
    "setuphelfer_msi_lab_late_sec=120"
)
# Phase A physical E2E one-shot: discovery off, e2e auto on.
MSI_LAB_PHYSICAL_E2E_CMDLINE_FLAGS = (
    "setuphelfer_msi_lab_auto=1 setuphelfer_auto_discovery=0 "
    "setuphelfer_msi_e2e_auto=1 setuphelfer_auto_shutdown=1 "
    "setuphelfer_msi_lab_late_sec=120"
)
# Interactive GUI lab (Phase B Backup/Verify/Restore) — no discovery lock, TUI via watchdog.
MSI_LAB_GUI_INTERACTIVE_FLAGS = (
    "setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0 "
    "setuphelfer_msi_e2e_auto=0 setuphelfer_auto_shutdown=0"
)
MSI_LAB_DEFAULT_TIMEOUT = 3
LAB_AUTO_MENU_TITLE = "Setuphelfer Lab-Auto (Text, Discovery)"
LAB_AUTO_GUI_MENU_TITLE = "Setuphelfer Lab-Auto (GUI, Discovery)"
LAB_GUI_INTERACTIVE_MENU_TITLE = "Setuphelfer Lab-Auto (GUI, Backup/Verify)"
LAB_TEXT_INTERACTIVE_MENU_TITLE = "Setuphelfer Lab-Auto (Text, Backup/Verify)"
LAB_PHYSICAL_E2E_MENU_TITLE = "Setuphelfer Lab-Auto (Text, Physical E2E)"


def msi_compat_menu_append(base_live: str) -> str:
    return (
        f"{base_live} setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_msi_compat=1 "
        "pci=noaer nouveau.modeset=0 nomodeset"
    )


def msi_lab_auto_text_menu_append(base_live: str) -> str:
    """Text lab/auto — operator-visible discovery; TUI-only."""
    return (
        f"{base_live} setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_safe_ui=1 "
        f"pci=noaer {MSI_LAB_CMDLINE_FLAGS}"
    )


def msi_lab_auto_gui_menu_append(base_live: str) -> str:
    """Automated GUI lab boot with gui-watchdog → TUI fallback.

    Explicit mode=gui bypasses MSI compat GUI disable; watchdog owns fallback.
    No nomodeset here so the GUI stack can try; pci=noaer keeps AER quiet.
    """
    return (
        f"{base_live} setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1 "
        f"pci=noaer {MSI_LAB_CMDLINE_FLAGS}"
    )


def msi_lab_gui_interactive_menu_append(base_live: str) -> str:
    """GUI-first interactive boot for Backup/Verify/Restore (Phase B) with TUI fallback."""
    return (
        f"{base_live} setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1 "
        f"pci=noaer {MSI_LAB_GUI_INTERACTIVE_FLAGS}"
    )


def msi_lab_text_interactive_menu_append(base_live: str) -> str:
    """Text fallback for Phase B — no discovery lock, operator can run Backup/Verify."""
    return (
        f"{base_live} setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_safe_ui=1 "
        f"pci=noaer {MSI_LAB_GUI_INTERACTIVE_FLAGS}"
    )


def msi_lab_auto_menu_append(base_live: str) -> str:
    """Default automated lab path is GUI-first (watchdog → TUI)."""
    return msi_lab_auto_gui_menu_append(base_live)


def _first_menuentry_index(text: str) -> int:
    return text.find('menuentry "')


def _extract_menuentry_block(text: str, title: str) -> tuple[str, str, str]:
    needle = f'menuentry "{title}"'
    start = text.find(needle)
    if start < 0:
        raise ValueError("MENU_ENTRY_NOT_FOUND")
    end = text.find("\n}", start)
    if end < 0:
        raise ValueError("MENU_ENTRY_MALFORMED")
    end += 2
    return text[:start], text[start:end], text[end:]


def _drop_lab_entries(grub_text: str) -> str:
    for title in (
        LAB_AUTO_GUI_MENU_TITLE,
        LAB_AUTO_MENU_TITLE,
        LAB_GUI_INTERACTIVE_MENU_TITLE,
        LAB_TEXT_INTERACTIVE_MENU_TITLE,
        LAB_PHYSICAL_E2E_MENU_TITLE,
    ):
        try:
            before, _old, after = _extract_menuentry_block(grub_text, title)
            grub_text = before + after
        except ValueError:
            pass
    return grub_text


def _rewrite_preamble(preamble: str) -> str:
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
    return "\n".join(lines).rstrip() + "\n\n"


def msi_lab_physical_e2e_menu_append(base_live: str) -> str:
    """One-shot physical E2E lab boot (SABRENT wipe + synthetic backup/verify/restore)."""
    return (
        f"{base_live} setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_safe_ui=1 "
        f"pci=noaer {MSI_LAB_PHYSICAL_E2E_CMDLINE_FLAGS}"
    )


def patch_grub_cfg_for_msi_lab_auto_boot(grub_text: str) -> str:
    """Lab auto: GUI Discovery default + Text Discovery fallback; keep manual GUI entry."""
    first_menu = _first_menuentry_index(grub_text)
    if first_menu < 0:
        raise ValueError("GRUB_MENU_ENTRIES_NOT_FOUND")

    base_live = (
        "boot=live components setuphelfer_rescue=1 setuphelfer_start_assistant=1 "
        "setuphelfer_telemetry_opt_in=1"
    )
    gui_lab = (
        f'menuentry "{LAB_AUTO_GUI_MENU_TITLE}" {{\n'
        f"  linux /live/vmlinuz {msi_lab_auto_gui_menu_append(base_live)}\n"
        "  initrd /live/initrd.img\n"
        "}\n"
    )
    text_lab = (
        f'menuentry "{LAB_AUTO_MENU_TITLE}" {{\n'
        f"  linux /live/vmlinuz {msi_lab_auto_text_menu_append(base_live)}\n"
        "  initrd /live/initrd.img\n"
        "}\n"
    )

    grub_text = _drop_lab_entries(grub_text)
    first_menu = _first_menuentry_index(grub_text)
    if first_menu < 0:
        raise ValueError("GRUB_MENU_ENTRIES_NOT_FOUND")
    preamble = grub_text[:first_menu]
    other_entries = grub_text[first_menu:].lstrip("\n")
    return f"{_rewrite_preamble(preamble)}{gui_lab}\n{text_lab}\n{other_entries}"


def patch_grub_cfg_for_msi_gui_interactive_boot(grub_text: str) -> str:
    """Phase B: GUI Backup/Verify default with TUI fallback via watchdog; no discovery lock."""
    first_menu = _first_menuentry_index(grub_text)
    if first_menu < 0:
        raise ValueError("GRUB_MENU_ENTRIES_NOT_FOUND")

    base_live = (
        "boot=live components setuphelfer_rescue=1 setuphelfer_start_assistant=1 "
        "setuphelfer_telemetry_opt_in=1"
    )
    gui_block = (
        f'menuentry "{LAB_GUI_INTERACTIVE_MENU_TITLE}" {{\n'
        f"  linux /live/vmlinuz {msi_lab_gui_interactive_menu_append(base_live)}\n"
        "  initrd /live/initrd.img\n"
        "}\n"
    )
    text_fallback = (
        f'menuentry "{LAB_TEXT_INTERACTIVE_MENU_TITLE}" {{\n'
        f"  linux /live/vmlinuz {msi_lab_text_interactive_menu_append(base_live)}\n"
        "  initrd /live/initrd.img\n"
        "}\n"
    )

    grub_text = _drop_lab_entries(grub_text)
    first_menu = _first_menuentry_index(grub_text)
    if first_menu < 0:
        raise ValueError("GRUB_MENU_ENTRIES_NOT_FOUND")
    preamble = grub_text[:first_menu]
    other_entries = grub_text[first_menu:].lstrip("\n")
    return f"{_rewrite_preamble(preamble)}{gui_block}\n{text_fallback}\n{other_entries}"


def patch_grub_cfg_for_msi_physical_e2e_boot(grub_text: str) -> str:
    """One-shot physical E2E as default menu entry (Phase A)."""
    first_menu = _first_menuentry_index(grub_text)
    if first_menu < 0:
        raise ValueError("GRUB_MENU_ENTRIES_NOT_FOUND")

    base_live = (
        "boot=live components setuphelfer_rescue=1 setuphelfer_start_assistant=1 "
        "setuphelfer_telemetry_opt_in=1"
    )
    e2e_linux = msi_lab_physical_e2e_menu_append(base_live)
    e2e_block = (
        f'menuentry "{LAB_PHYSICAL_E2E_MENU_TITLE}" {{\n'
        f"  linux /live/vmlinuz {e2e_linux}\n"
        "  initrd /live/initrd.img\n"
        "}\n"
    )

    grub_text = _drop_lab_entries(grub_text)
    first_menu = _first_menuentry_index(grub_text)
    if first_menu < 0:
        raise ValueError("GRUB_MENU_ENTRIES_NOT_FOUND")
    preamble = grub_text[:first_menu]
    other_entries = grub_text[first_menu:].lstrip("\n")
    return f"{_rewrite_preamble(preamble)}{e2e_block}\n{other_entries}"
