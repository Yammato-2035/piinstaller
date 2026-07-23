"""ASUS ROG lab GRUB entries — GUI-first + BIOS gate cmdline (Phase C)."""

from __future__ import annotations

ASUS_ROG_LAB_MENU_TITLE = "Setuphelfer ASUS ROG Lab (GUI, BIOS-Check)"
ASUS_ROG_TEXT_MENU_TITLE = "Setuphelfer ASUS ROG Lab (Text, BIOS-Check)"
PI5_LAB_MENU_TITLE = "Setuphelfer Pi5 Lab (Host-Prep / USB-Boot-Check)"

# Hybrid GPU flags: same as MSI GUI — ASUS ROG Lab may be selected on hybrid MSI by mistake.
_HYBRID_GPU_FLAGS = "pci=noaer modprobe.blacklist=nouveau nouveau.modeset=0"

_ASUS_LAB_FLAGS = (
    "setuphelfer_asus_rog_lab=1 setuphelfer_msi_lab_auto=0 "
    "setuphelfer_auto_discovery=0 setuphelfer_msi_e2e_auto=0 setuphelfer_auto_shutdown=0"
)
_PI5_LAB_FLAGS = (
    "setuphelfer_pi5_lab=1 setuphelfer_msi_lab_auto=0 "
    "setuphelfer_auto_discovery=0 setuphelfer_msi_e2e_auto=0 setuphelfer_auto_shutdown=0"
)


def asus_rog_lab_gui_menu_append(base_live: str) -> str:
    return (
        f"{base_live} setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1 "
        f"{_HYBRID_GPU_FLAGS} {_ASUS_LAB_FLAGS}"
    )


def asus_rog_lab_text_menu_append(base_live: str) -> str:
    return (
        f"{base_live} setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_safe_ui=1 "
        f"{_HYBRID_GPU_FLAGS} {_ASUS_LAB_FLAGS}"
    )


def pi5_lab_menu_append(base_live: str) -> str:
    return f"{base_live} setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_safe_ui=1 {_PI5_LAB_FLAGS}"


def _first_menuentry_index(text: str) -> int:
    return text.find('menuentry "')


def _drop_titles(grub_text: str, titles: tuple[str, ...]) -> str:
    out = grub_text
    for title in titles:
        needle = f'menuentry "{title}"'
        while True:
            start = out.find(needle)
            if start < 0:
                break
            end = out.find("\n}", start)
            if end < 0:
                break
            out = out[:start] + out[end + 3 :]
    return out


def patch_grub_cfg_for_asus_rog_and_pi5_lab(grub_text: str) -> str:
    """Append ASUS ROG + Pi5 lab entries after existing menuentries (MSI stays default)."""
    first_menu = _first_menuentry_index(grub_text)
    if first_menu < 0:
        raise ValueError("GRUB_MENU_ENTRIES_NOT_FOUND")

    base_live = (
        "boot=live components setuphelfer_rescue=1 setuphelfer_start_assistant=1 "
        "setuphelfer_telemetry_opt_in=1"
    )
    titles = (ASUS_ROG_LAB_MENU_TITLE, ASUS_ROG_TEXT_MENU_TITLE, PI5_LAB_MENU_TITLE)
    grub_text = _drop_titles(grub_text, titles)
    first_menu = _first_menuentry_index(grub_text)
    if first_menu < 0:
        raise ValueError("GRUB_MENU_ENTRIES_NOT_FOUND")

    blocks = (
        f'menuentry "{ASUS_ROG_LAB_MENU_TITLE}" {{\n'
        f"  linux /live/vmlinuz {asus_rog_lab_gui_menu_append(base_live)}\n"
        "  initrd /live/initrd.img\n"
        "}\n"
        f'menuentry "{ASUS_ROG_TEXT_MENU_TITLE}" {{\n'
        f"  linux /live/vmlinuz {asus_rog_lab_text_menu_append(base_live)}\n"
        "  initrd /live/initrd.img\n"
        "}\n"
        f'menuentry "{PI5_LAB_MENU_TITLE}" {{\n'
        f"  linux /live/vmlinuz {pi5_lab_menu_append(base_live)}\n"
        "  initrd /live/initrd.img\n"
        "}\n"
    )
    # Keep MSI/default entries first — append lab entries at end.
    return f"{grub_text.rstrip()}\n\n{blocks}"
