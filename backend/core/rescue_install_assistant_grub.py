"""GRUB menu for install assistant on Gabriel ASUS ROG (PI-RS-INSTALL-ASSISTANT-001).

Fixes observed physical failure 2026-07-25:
- Default Lab-Auto GUI Physical E2E left GUI stuck in sabrent_wait (no Xorg).
- No Linux-installation menuentry.
- Plain GUI entry lacked hybrid-GPU flags.

Never enables MSI E2E auto as default. Stick write/wipe for Gabriel linux_target
is gated in policy modules, not by this GRUB text alone.
"""

from __future__ import annotations

import re
from typing import Any

CONTRACT_VERSION = 1

HYBRID_GPU_FLAGS = "pci=noaer modprobe.blacklist=nouveau nouveau.modeset=0"

INSTALL_GUI_TITLE = "Setuphelfer Linux-Installation (Mint Assistent, GUI)"
INSTALL_TEXT_TITLE = "Setuphelfer Linux-Installation (Text)"
MINT_ISO_BOOT_TITLE = "Linux Mint 22.2 Installer (ISO vom Stick)"
GUI_SAFE_TITLE = "Setuphelfer starten - grafische Oberflaeche (ASUS-sicher)"
TEXT_SAFE_TITLE = "Setuphelfer starten - sicherer Textmodus"
ASUS_LAB_GUI_TITLE = "Setuphelfer ASUS ROG Lab (GUI, BIOS-Check)"
ASUS_LAB_TEXT_TITLE = "Setuphelfer ASUS ROG Lab (Text, BIOS-Check)"
LAB_E2E_GUI_WARN = "WARNUNG MSI-only: Lab-Auto (GUI, Physical E2E) — nicht Gabriel"

BASE_LIVE = (
    "boot=live components setuphelfer_rescue=1 setuphelfer_start_assistant=1 "
    "setuphelfer_telemetry_opt_in=1"
)

_INSTALL_FLAGS = (
    "setuphelfer_install_assistant=1 setuphelfer_linux_install=1 "
    "setuphelfer_gabriel_ops_allowed=1 "
    "setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0 "
    "setuphelfer_msi_e2e_auto=0 setuphelfer_auto_shutdown=0"
)

_ASUS_LAB_FLAGS = (
    "setuphelfer_asus_rog_lab=1 setuphelfer_msi_lab_auto=0 "
    "setuphelfer_auto_discovery=0 setuphelfer_msi_e2e_auto=0 setuphelfer_auto_shutdown=0"
)

MINT_ISO_REL = "/setuphelfer/iso-cache/linux_mint/linuxmint-22.2-cinnamon-64bit.iso"


def _entry(title: str, append: str) -> str:
    return (
        f'menuentry "{title}" {{\n'
        f"  linux /live/vmlinuz {append}\n"
        f"  initrd /live/initrd.img\n"
        f"}}\n"
    )


def install_assistant_gui_append(base_live: str = BASE_LIVE) -> str:
    return (
        f"{base_live} setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1 "
        f"{HYBRID_GPU_FLAGS} {_INSTALL_FLAGS}"
    )


def install_assistant_text_append(base_live: str = BASE_LIVE) -> str:
    return (
        f"{base_live} setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_safe_ui=1 "
        f"{HYBRID_GPU_FLAGS} {_INSTALL_FLAGS} nomodeset"
    )


def asus_safe_gui_append(base_live: str = BASE_LIVE) -> str:
    return (
        f"{base_live} setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1 "
        f"{HYBRID_GPU_FLAGS} setuphelfer_msi_lab_auto=0 setuphelfer_msi_e2e_auto=0 "
        "setuphelfer_auto_shutdown=0"
    )


def mint_iso_loopback_entry() -> str:
    """Boot official Mint installer ISO from SETUP_LOGS (no Rescue GUI required)."""
    return (
        f'menuentry "{MINT_ISO_BOOT_TITLE}" {{\n'
        "  search --no-floppy --label SETUP_LOGS --set=root\n"
        '  if [ -z "$root" ]; then\n'
        "    search --no-floppy --label SETUP_LOGS2 --set=root\n"
        "  fi\n"
        f'  set isofile="{MINT_ISO_REL}"\n'
        "  loopback loop $isofile\n"
        "  linux (loop)/casper/vmlinuz boot=casper iso-scan/filename=$isofile "
        "quiet splash --- \n"
        "  initrd (loop)/casper/initrd.lz\n"
        "}\n"
    )


def generate_gabriel_install_grub_cfg(
    *,
    fat_uuid: str | None = "9BB9-A4A6",
    fat_label: str = "SETUPHELFER",
    timeout: int = 20,
) -> str:
    """Full GRUB cfg optimized for Gabriel Mint install — MSI E2E demoted.

    Default=0 is Text install assistant (GUI payload often missing frontend).
    Entry 1 boots Mint ISO directly from SETUP_LOGS.
    """
    root_block = [
        f"set timeout={timeout}",
        "set timeout_style=menu",
        "set default=0",
    ]
    if fat_uuid:
        root_block.append(f"search --no-floppy --fs-uuid {fat_uuid} --set=root")
        root_block.extend(
            [
                'if [ -z "$root" ]; then',
                f"  search --no-floppy --label {fat_label} --set=root",
                "fi",
            ]
        )
    else:
        root_block.append(f"search --no-floppy --label {fat_label} --set=root")
    root_block.extend(
        [
            'if [ -z "$root" ]; then',
            "  set root=($cmdpath)",
            "fi",
            "",
            "insmod all_video",
            "insmod efi_gop",
            "insmod efi_uga",
            "insmod video",
            "insmod gfxterm",
            "insmod loopback",
            "insmod iso9660",
            "set gfxmode=auto",
            "set gfxpayload=keep",
            "terminal_output gfxterm",
            "terminal_input console",
            "set menu_color_normal=white/black",
            "set menu_color_highlight=black/white",
            "",
        ]
    )

    entries = [
        # Default: text install assistant (works when GUI frontend missing)
        _entry(INSTALL_TEXT_TITLE, install_assistant_text_append()),
        mint_iso_loopback_entry(),
        _entry(INSTALL_GUI_TITLE, install_assistant_gui_append()),
        _entry(GUI_SAFE_TITLE, asus_safe_gui_append()),
        _entry(
            TEXT_SAFE_TITLE,
            f"{BASE_LIVE} setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_safe_ui=1 "
            f"{HYBRID_GPU_FLAGS} nomodeset",
        ),
        _entry(
            "Diagnose sammeln und auf Stick speichern",
            f"{BASE_LIVE} setuphelfer_mode=diagnostics setuphelfer_kiosk=0 "
            "setuphelfer_collect_diagnostics=1",
        ),
        _entry(
            "Hardware- und WLAN-Diagnose",
            f"{BASE_LIVE} setuphelfer_mode=hardware setuphelfer_kiosk=0 setuphelfer_wifi_diag=1",
        ),
        _entry(
            ASUS_LAB_GUI_TITLE,
            f"{BASE_LIVE} setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1 "
            f"{HYBRID_GPU_FLAGS} {_ASUS_LAB_FLAGS}",
        ),
        _entry(
            ASUS_LAB_TEXT_TITLE,
            f"{BASE_LIVE} setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_safe_ui=1 "
            f"{HYBRID_GPU_FLAGS} {_ASUS_LAB_FLAGS} nomodeset",
        ),
        _entry(
            "Setuphelfer ASUS Hardwarediagnose (nur Lesen)",
            f"{BASE_LIVE} init=/lib/systemd/systemd setuphelfer_mode=text "
            "setuphelfer_kiosk=0 setuphelfer_safe_ui=1 setuphelfer_hardware_discovery=1 "
            "setuphelfer_auto_win11_setup_logs=1 setuphelfer_auto_discovery=0 "
            "setuphelfer_msi_e2e_auto=0 setuphelfer_msi_lab_auto=0 "
            f"setuphelfer_auto_shutdown=0 {HYBRID_GPU_FLAGS} nomodeset",
        ),
        _entry(
            LAB_E2E_GUI_WARN,
            f"{BASE_LIVE} setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1 "
            f"{HYBRID_GPU_FLAGS} setuphelfer_msi_lab_auto=1 setuphelfer_auto_discovery=0 "
            "setuphelfer_msi_e2e_auto=1 setuphelfer_auto_shutdown=1 "
            "setuphelfer_msi_lab_late_sec=120",
        ),
        'menuentry "Neustart" { reboot }\n',
        'menuentry "Ausschalten" { halt }\n',
    ]
    return "\n".join(root_block) + "\n".join(entries)


def patch_grub_cfg_for_install_assistant(grub_text: str) -> str:
    """Insert install-assistant entries at top and force default=0; demote MSI E2E title."""
    text = grub_text
    # Force default first entry
    text = re.sub(r"(?m)^set default=\d+\s*$", "set default=0", text, count=1)
    if "set default=" not in text:
        text = "set default=0\n" + text

    # Rename dangerous MSI E2E title if present
    text = text.replace(
        'menuentry "Setuphelfer Lab-Auto (GUI, Physical E2E)"',
        f'menuentry "{LAB_E2E_GUI_WARN}"',
    )

    # Harden plain GUI entry with hybrid flags and kill e2e if somehow present
    plain = 'menuentry "Setuphelfer starten - grafische Oberflaeche" {'
    if plain in text and GUI_SAFE_TITLE not in text:
        text = text.replace(
            plain,
            f'menuentry "{GUI_SAFE_TITLE}" {{',
            1,
        )
        # Ensure hybrid flags on that block's linux line
        def _harden_gui_linux(m: re.Match[str]) -> str:
            line = m.group(0)
            if "modprobe.blacklist=nouveau" not in line:
                line = line.rstrip() + f" {HYBRID_GPU_FLAGS}"
            line = re.sub(r"setuphelfer_msi_e2e_auto=1", "setuphelfer_msi_e2e_auto=0", line)
            line = re.sub(r"setuphelfer_msi_lab_auto=1", "setuphelfer_msi_lab_auto=0", line)
            line = re.sub(r"setuphelfer_auto_shutdown=1", "setuphelfer_auto_shutdown=0", line)
            return line

        # Only first linux after GUI_SAFE title
        idx = text.find(f'menuentry "{GUI_SAFE_TITLE}"')
        if idx >= 0:
            rest = text[idx:]
            rest2 = re.sub(
                r"(?m)^(\s*linux /live/vmlinuz .+)$",
                _harden_gui_linux,
                rest,
                count=1,
            )
            text = text[:idx] + rest2

    if INSTALL_GUI_TITLE in text:
        return text

    block = (
        _entry(INSTALL_GUI_TITLE, install_assistant_gui_append())
        + _entry(INSTALL_TEXT_TITLE, install_assistant_text_append())
        + "\n"
    )
    m = re.search(r"(?m)^menuentry \"", text)
    if not m:
        return text.rstrip() + "\n\n" + block
    return text[: m.start()] + block + text[m.start() :]


def validate_gabriel_install_grub(grub_text: str) -> dict[str, Any]:
    checks = {
        "has_install_gui": INSTALL_GUI_TITLE in grub_text,
        "has_install_text": INSTALL_TEXT_TITLE in grub_text,
        "has_mint_iso_boot": MINT_ISO_BOOT_TITLE in grub_text,
        "default_zero": bool(re.search(r"(?m)^set default=0\s*$", grub_text)),
        "no_msi_e2e_as_first_entry": True,
        "install_text_has_hybrid_gpu": False,
        "install_text_disables_msi_e2e": False,
    }
    first = re.search(r'menuentry "([^"]+)"', grub_text)
    if first:
        checks["first_entry"] = first.group(1)
        checks["no_msi_e2e_as_first_entry"] = (
            "Physical E2E" not in first.group(1) and "Lab-Auto" not in first.group(1)
        )
    m = re.search(
        rf'menuentry "{re.escape(INSTALL_TEXT_TITLE)}" \{{(.*?)^\}}',
        grub_text,
        re.S | re.M,
    )
    if m:
        body = m.group(1)
        checks["install_text_has_hybrid_gpu"] = "modprobe.blacklist=nouveau" in body
        checks["install_text_disables_msi_e2e"] = "setuphelfer_msi_e2e_auto=0" in body
        checks["install_text_flag"] = "setuphelfer_install_assistant=1" in body
    ok = all(
        bool(checks[k])
        for k in (
            "has_install_gui",
            "has_install_text",
            "has_mint_iso_boot",
            "default_zero",
            "no_msi_e2e_as_first_entry",
            "install_text_has_hybrid_gpu",
            "install_text_disables_msi_e2e",
        )
    )
    return {"ok": ok, "checks": checks, "contract_version": CONTRACT_VERSION}
