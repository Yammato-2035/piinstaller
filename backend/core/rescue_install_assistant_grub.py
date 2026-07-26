"""GRUB menu for install assistant on Gabriel ASUS ROG (PI-RS-INSTALL-ASSISTANT-001).

Fixes observed physical failure 2026-07-25:
- Default Lab-Auto GUI Physical E2E left GUI stuck in sabrent_wait (no Xorg).
- No Linux-installation menuentry.
- Plain GUI entry lacked hybrid-GPU flags.

FROZEN default (2026-07-26 physical matrix): Rescue-Root only.
No new experimental Mint cmdline without updating G513QM_FAILURE_MATRIX.md.
amdgpu / Emergency-bash entries remain labeled WARNUNG (never default).

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
MINT_ISO_BOOT_TITLE = "Linux Mint 22.2 Installer (ISO-Loopback, Fallback)"
MINT_CASPER_BOOT_TITLE = "Linux Mint 22.2 Installer (direkt vom Stick)"
# Proven console path (emergency). Hybrid Auto is the new default for display/installer work.
MINT_CASPER_RESCUE_TITLE = "G513QM Basic Graphics Emergency (nomodeset Rescue)"
MINT_CASPER_HYBRID_TITLE = "G513QM Rescue Hybrid Auto (AMD display)"
MINT_CASPER_AMD_SAFE_TITLE = "G513QM AMD Safe Display (Installer-Fallback)"
MINT_CASPER_NVIDIA_DIAG_TITLE = "G513QM NVIDIA Proprietary Diagnostic"
MINT_CASPER_NOUVEAU_TITLE = "G513QM Nouveau Fallback Diagnostic"
MINT_CASPER_CAPTURE_TITLE = "G513QM Capture Only / Text"
MINT_CASPER_BASH_TITLE = "WARNUNG: Emergency bash (Kernel-Panic auf Gabriel)"
MINT_CASPER_AMDGPU_TITLE = "WARNUNG: legacy Text mit amdgpu (Keyboard-Hang)"
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
    "setuphelfer_msi_e2e_auto=0 setuphelfer_auto_shutdown=0 "
    "setuphelfer_hardware_discovery=0"
)

_ASUS_LAB_FLAGS = (
    "setuphelfer_asus_rog_lab=1 setuphelfer_msi_lab_auto=0 "
    "setuphelfer_auto_discovery=0 setuphelfer_msi_e2e_auto=0 setuphelfer_auto_shutdown=0"
)

MINT_ISO_REL = "/setuphelfer/iso-cache/linux_mint/linuxmint-22.2-cinnamon-64bit.iso"
MINT_CASPER_DIR = "/mint-live"
SETUP_LOGS_UUID = "9BC7-3950"


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


def _mint_casper_base_parts() -> list[str]:
    path = MINT_CASPER_DIR.lstrip("/")
    return [
        "boot=casper",
        f"live-media=/dev/disk/by-uuid/{SETUP_LOGS_UUID}",
        f"live-media-path={path}",
        "ignore_uuid",
        "username=mint",
        "hostname=mint",
        "pci=noaer",
        "noplymouth",
        "console=tty0",
        "consoleblank=0",
        "fbcon=nodefer",
        "noeject",
        "fsck.mode=skip",
        "systemd.debug-shell=1",
        "setuphelfer_capture=1",
    ]


def _mint_safe_cmdline(
    *,
    debug: bool = False,
    text_only: bool = False,
    rescue: bool = False,
    allow_amdgpu: bool = False,
    emergency_bash: bool = False,
) -> str:
    """Legacy helper retained for warning/emergency entries."""
    parts = _mint_casper_base_parts()
    parts.append("nouveau.modeset=0")
    parts.extend(
        [
            "systemd.mask=lightdm.service",
            "systemd.mask=mdm.service",
            "systemd.mask=gdm3.service",
            "systemd.mask=gdm.service",
        ]
    )
    if allow_amdgpu:
        parts.append("modprobe.blacklist=hid_asus,asus_nb_wmi,asus_wmi")
    else:
        parts.extend(
            [
                "modprobe.blacklist=nouveau,hid_asus,asus_nb_wmi,asus_wmi",
                "amdgpu.modeset=0",
                "radeon.modeset=0",
                "nomodeset",
            ]
        )
    if emergency_bash:
        parts.append("init=/bin/bash")
    elif rescue:
        parts.append("systemd.unit=rescue.target")
    elif text_only:
        parts.append("systemd.unit=multi-user.target")
    if debug:
        parts.append("debug")
    return " ".join(parts)


def _profile_cmdline(profile_id: str) -> str:
    """Build casper cmdline from config/rescue/g513qm_graphics_profiles.json intent."""
    parts = _mint_casper_base_parts()
    parts.append(f"setuphelfer_g513qm_profile={profile_id}")
    if profile_id == "g513qm_hybrid_auto":
        # AMD KMS allowed; do not blacklist amdgpu/nouveau globally; no nomodeset
        parts.append("modprobe.blacklist=hid_asus,asus_nb_wmi")
    elif profile_id == "g513qm_amd_safe":
        parts.append(
            "modprobe.blacklist=nvidia,nvidia_drm,nvidia_modeset,nvidia_uvm,nouveau,hid_asus"
        )
    elif profile_id == "g513qm_nvidia_prop_diag":
        parts.extend(
            [
                "nouveau.modeset=0",
                "modprobe.blacklist=nouveau",
                "nvidia-drm.modeset=1",
            ]
        )
    elif profile_id == "g513qm_nouveau_fallback":
        parts.append("modprobe.blacklist=nvidia,nvidia_drm,nvidia_modeset,nvidia_uvm")
    elif profile_id in ("g513qm_basic_emergency", "g513qm_capture_only"):
        parts.extend(
            [
                "nouveau.modeset=0",
                "modprobe.blacklist=nouveau,hid_asus,asus_nb_wmi,asus_wmi",
                "amdgpu.modeset=0",
                "radeon.modeset=0",
                "nomodeset",
                "systemd.unit=rescue.target",
                "systemd.mask=lightdm.service",
                "systemd.mask=mdm.service",
                "systemd.mask=gdm3.service",
                "systemd.mask=gdm.service",
            ]
        )
    if profile_id not in ("g513qm_basic_emergency", "g513qm_capture_only"):
        # Keep DM from auto-starting until operator runs start-desktop / ubiquity modes
        parts.extend(
            [
                "systemd.mask=lightdm.service",
                "systemd.mask=mdm.service",
                "systemd.mask=gdm3.service",
                "systemd.mask=gdm.service",
            ]
        )
    return " ".join(parts)


def _mint_menuentry(title: str, cmdline: str) -> str:
    """Mint casper entry; gfxpayload=text for early console; hybrid profiles may switch FB later."""
    return (
        f'menuentry "{title}" {{\n'
        "  insmod part_gpt\n"
        "  insmod fat\n"
        "  set gfxpayload=text\n"
        f"  search --no-floppy --fs-uuid {SETUP_LOGS_UUID} --set=root\n"
        '  if [ -z "$root" ]; then\n'
        "    search --no-floppy --label SETUP_LOGS --set=root\n"
        "  fi\n"
        '  if [ -z "$root" ]; then\n'
        "    search --no-floppy --label SETUP_LOGS2 --set=root\n"
        "  fi\n"
        f"  linux {MINT_CASPER_DIR}/vmlinuz {cmdline} --- \n"
        f"  initrd {MINT_CASPER_DIR}/initrd.lz\n"
        "}\n"
    )


def mint_casper_direct_entry() -> str:
    """G513QM hybrid profile matrix (STRICT rebuild).

    Default: Hybrid Auto (AMD display, no nomodeset).
    Installer fallback: AMD Safe.
    Emergency: nomodeset Rescue (historically proven text console).
    """
    return (
        _mint_menuentry(MINT_CASPER_HYBRID_TITLE, _profile_cmdline("g513qm_hybrid_auto"))
        + _mint_menuentry(MINT_CASPER_AMD_SAFE_TITLE, _profile_cmdline("g513qm_amd_safe"))
        + _mint_menuentry(MINT_CASPER_NVIDIA_DIAG_TITLE, _profile_cmdline("g513qm_nvidia_prop_diag"))
        + _mint_menuentry(MINT_CASPER_NOUVEAU_TITLE, _profile_cmdline("g513qm_nouveau_fallback"))
        + _mint_menuentry(MINT_CASPER_RESCUE_TITLE, _profile_cmdline("g513qm_basic_emergency"))
        + _mint_menuentry(MINT_CASPER_CAPTURE_TITLE, _profile_cmdline("g513qm_capture_only"))
        + _mint_menuentry(MINT_CASPER_BOOT_TITLE, _mint_safe_cmdline(text_only=True))
        + _mint_menuentry(MINT_CASPER_BASH_TITLE, _mint_safe_cmdline(emergency_bash=True))
    )


def mint_iso_loopback_entry() -> str:
    """Fallback ISO loopback — prefer mint_casper_direct_entry on Gabriel."""
    gpu = (
        "pci=noaer nouveau.modeset=0 "
        "modprobe.blacklist=nouveau,hid_asus,asus_nb_wmi,asus_wmi "
        "amdgpu.modeset=0 radeon.modeset=0 nomodeset noplymouth console=tty0 "
        "consoleblank=0 systemd.debug-shell=1"
    )
    return (
        f'menuentry "{MINT_ISO_BOOT_TITLE}" {{\n'
        "  insmod part_gpt\n"
        "  insmod fat\n"
        "  insmod loopback\n"
        "  insmod iso9660\n"
        "  set gfxpayload=text\n"
        f"  search --no-floppy --fs-uuid {SETUP_LOGS_UUID} --set=root\n"
        '  if [ -z "$root" ]; then\n'
        "    search --no-floppy --label SETUP_LOGS --set=root\n"
        "  fi\n"
        f'  set isofile="{MINT_ISO_REL}"\n'
        "  loopback loop $isofile\n"
        "  linux (loop)/casper/vmlinuz boot=casper iso-scan/filename=$isofile "
        f"ignore_uuid {gpu} noeject fsck.mode=skip "
        "systemd.unit=multi-user.target --- \n"
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
        # Default: direct Mint installer (extracted casper) — no Rescue GUI / no ISO loopback
        mint_casper_direct_entry(),
        mint_iso_loopback_entry(),
        _entry(INSTALL_TEXT_TITLE, install_assistant_text_append()),
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
            ASUS_LAB_TEXT_TITLE,
            f"{BASE_LIVE} setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_safe_ui=1 "
            f"{HYBRID_GPU_FLAGS} {_ASUS_LAB_FLAGS} nomodeset",
        ),
        _entry(
            LAB_E2E_GUI_WARN,
            f"{BASE_LIVE} setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1 "
            f"{HYBRID_GPU_FLAGS} setuphelfer_msi_lab_auto=1 setuphelfer_auto_discovery=0 "
            "setuphelfer_msi_e2e_auto=1 setuphelfer_auto_shutdown=1 "
            "setuphelfer_msi_lab_late_sec=120",
        ),
        'menuentry "Neustart (sofort)" { reboot }\n',
        'menuentry "Ausschalten (sofort)" { halt }\n',
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
        "has_mint_casper_boot": MINT_CASPER_BOOT_TITLE in grub_text,
        "has_mint_iso_boot": MINT_ISO_BOOT_TITLE in grub_text,
        "has_hybrid_auto": MINT_CASPER_HYBRID_TITLE in grub_text,
        "has_amd_safe": MINT_CASPER_AMD_SAFE_TITLE in grub_text,
        "default_zero": bool(re.search(r"(?m)^set default=0\s*$", grub_text)),
        "no_msi_e2e_as_first_entry": True,
        "first_is_hybrid_auto": False,
        "has_force_halt": "Ausschalten (sofort)" in grub_text,
        "hybrid_no_nomodeset": False,
        "hybrid_no_amdgpu_blacklist": False,
        "hybrid_pins_live_media": False,
        "emergency_has_nomodeset": False,
        "mint_no_splash": "quiet splash" not in grub_text,
        "mint_gfxpayload_text": "set gfxpayload=text" in grub_text,
    }
    first = re.search(r'menuentry "([^"]+)"', grub_text)
    if first:
        checks["first_entry"] = first.group(1)
        checks["first_is_hybrid_auto"] = first.group(1) == MINT_CASPER_HYBRID_TITLE
        checks["no_msi_e2e_as_first_entry"] = (
            "Physical E2E" not in first.group(1) and "Lab-Auto" not in first.group(1)
        )
    m = re.search(
        rf'menuentry "{re.escape(MINT_CASPER_HYBRID_TITLE)}" \{{(.*?)^\}}',
        grub_text,
        re.S | re.M,
    )
    if m:
        body = m.group(1)
        checks["hybrid_no_nomodeset"] = "nomodeset" not in body
        checks["hybrid_no_amdgpu_blacklist"] = "blacklist=amdgpu" not in body and "amdgpu.modeset=0" not in body
        checks["hybrid_pins_live_media"] = f"live-media=/dev/disk/by-uuid/{SETUP_LOGS_UUID}" in body
    e = re.search(
        rf'menuentry "{re.escape(MINT_CASPER_RESCUE_TITLE)}" \{{(.*?)^\}}',
        grub_text,
        re.S | re.M,
    )
    if e:
        checks["emergency_has_nomodeset"] = "nomodeset" in e.group(1)
    ok = all(
        bool(checks[k])
        for k in (
            "has_hybrid_auto",
            "has_amd_safe",
            "has_install_text",
            "default_zero",
            "no_msi_e2e_as_first_entry",
            "first_is_hybrid_auto",
            "has_force_halt",
            "hybrid_no_nomodeset",
            "hybrid_no_amdgpu_blacklist",
            "hybrid_pins_live_media",
            "emergency_has_nomodeset",
            "mint_no_splash",
            "mint_gfxpayload_text",
        )
    )
    return {"ok": ok, "checks": checks, "contract_version": CONTRACT_VERSION}
