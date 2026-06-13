"""
Rescue boot and menu logger — early boot context capture (Phase R.3).

Read-only probes only; writes go through rescue_persistence (stick or RAM fallback).
"""

from __future__ import annotations

import os
import platform
import re
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from core.rescue_persistence import Runner, write_rescue_json_evidence, write_rescue_text_evidence

RESCUE_BOOT_LOGGER_VERSION = 3

_JOURNAL_SAFE_UNITS = (
    "setuphelfer-rescue-start-assistant.service",
    "setuphelfer-rescue-ui-launch.service",
    "NetworkManager.service",
    "systemd-logind.service",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_text(path: str | Path, *, limit: int = 8000) -> str:
    try:
        p = Path(path)
        if not p.is_file():
            return ""
        return p.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def _run_capture(cmd: str, *, runner: Callable[..., Any] | None = None, timeout: int = 5) -> tuple[int, str]:
    if runner is not None:
        proc = runner(cmd.split(), capture_output=True, text=True, timeout=timeout, check=False)
        return int(proc.returncode), (proc.stdout or "")[:8000]
    import subprocess

    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, check=False)
    return proc.returncode, (proc.stdout or "")[:8000]


def collect_kernel_cmdline(*, runner: Runner = None) -> dict[str, Any]:
    raw = _read_text("/proc/cmdline", limit=4096).strip()
    tokens = raw.split() if raw else []
    flags = {
        "setuphelfer_rescue": any("setuphelfer_rescue=1" in t for t in tokens),
        "setuphelfer_start_assistant": any("setuphelfer_start_assistant=1" in t for t in tokens),
        "setuphelfer_network_onboarding": any("setuphelfer_network_onboarding=1" in t for t in tokens),
        "boot_live": any(t.startswith("boot=live") for t in tokens),
        "toram": any("toram" in t for t in tokens),
    }
    return {"raw": raw, "tokens": tokens, "flags": flags}


def collect_boot_context(*, runner: Runner = None) -> dict[str, Any]:
    uname = platform.uname()
    boot_id = _read_text("/proc/sys/kernel/random/boot_id", limit=64).strip()
    return {
        "collected_at": _utc_now(),
        "hostname": socket.gethostname(),
        "kernel": uname.release,
        "machine": uname.machine,
        "boot_id": boot_id or None,
        "live_medium_dir_exists": Path("/run/live/medium").is_dir(),
        "cmdline": collect_kernel_cmdline(runner=runner),
    }


def collect_bootloader_context(*, runner: Runner = None) -> dict[str, Any]:
    efi_present = Path("/sys/firmware/efi").is_dir()
    secure_boot: str | None = None
    if efi_present:
        for candidate in (
            "/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c",
            "/sys/firmware/efi/efivars/SecureBootEnable-8be4df61-93ca-11d2-aa0d-00e098032b8c",
        ):
            if Path(candidate).is_file():
                secure_boot = "present_var"
                break
        if secure_boot is None:
            secure_boot = "unknown"
    vendor = _read_text("/sys/class/dmi/id/sys_vendor", limit=128).strip()
    product = _read_text("/sys/class/dmi/id/product_name", limit=128).strip()
    return {
        "collected_at": _utc_now(),
        "firmware_mode": "uefi" if efi_present else "bios_or_unknown",
        "efi_present": efi_present,
        "secure_boot_indicators": secure_boot,
        "dmi_vendor": vendor or None,
        "dmi_product": product or None,
        "isolinux_cfg_exists": Path("/isolinux/isolinux.cfg").is_file(),
        "grub_cfg_exists": Path("/boot/grub/grub.cfg").is_file(),
    }


def collect_live_environment(*, runner: Runner = None) -> dict[str, Any]:
    display = os.environ.get("DISPLAY", "")
    wayland = os.environ.get("WAYLAND_DISPLAY", "")
    browsers: list[str] = []
    for name in ("chromium", "chromium-browser", "firefox", "firefox-esr", "links", "w3m"):
        rc, _ = _run_capture(f"command -v {name}", runner=runner, timeout=2)
        if rc == 0:
            browsers.append(name)
    x_present = bool(display) or Path("/tmp/.X11-unix").exists()
    wayland_present = bool(wayland)
    nm_active = False
    rc, out = _run_capture("systemctl is-active NetworkManager 2>/dev/null", runner=runner, timeout=3)
    if rc == 0 and "active" in out:
        nm_active = True
    return {
        "collected_at": _utc_now(),
        "user": os.environ.get("USER") or os.environ.get("LOGNAME"),
        "display_env": display or None,
        "wayland_display": wayland or None,
        "x_present": x_present,
        "wayland_present": wayland_present,
        "browser_candidates": browsers,
        "network_manager_active": nm_active,
        "whiptail_available": _run_capture("command -v whiptail", runner=runner)[0] == 0,
    }


def collect_menu_context(*, runner: Runner = None) -> dict[str, Any]:
    ui_status_path = Path("/run/setuphelfer/rescue-ui-status.json")
    ui_status: dict[str, Any] = {}
    if ui_status_path.is_file():
        try:
            import json

            ui_status = json.loads(ui_status_path.read_text(encoding="utf-8"))
        except Exception:
            ui_status = {"parse_error": True}
    mode = "unknown"
    if ui_status.get("display_mode"):
        mode = str(ui_status.get("display_mode"))
    elif ui_status.get("browser_started"):
        mode = "graphical"
    elif os.environ.get("SETUPHELFER_RESCUE_FORCE_HEADLESS") == "1":
        mode = "headless"
    elif _run_capture("command -v whiptail", runner=runner)[0] == 0:
        mode = "tui"
    return {
        "collected_at": _utc_now(),
        "menu_mode": mode,
        "ui_status": ui_status,
        "start_assistant_status_exists": Path("/run/setuphelfer-rescue/start-assistant-status.json").is_file(),
        "wizard_state_exists": Path("/run/setuphelfer-rescue/wizard-state.json").is_file(),
    }


def _collect_journal_snippets(*, runner: Runner = None) -> list[dict[str, str]]:
    snippets: list[dict[str, str]] = []
    for unit in _JOURNAL_SAFE_UNITS:
        rc, out = _run_capture(
            f"journalctl -u {unit} -n 20 --no-pager -o short-iso 2>/dev/null",
            runner=runner,
            timeout=4,
        )
        if rc == 0 and out.strip():
            snippets.append({"unit": unit, "tail": out.strip()[:4000]})
    return snippets


def write_boot_evidence_bundle(*, runner: Runner = None) -> dict[str, Any]:
    """Collect boot/menu/live context and persist under setuphelfer-evidence/boot/."""
    bundle = {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "boot": collect_boot_context(runner=runner),
        "bootloader": collect_bootloader_context(runner=runner),
        "live_environment": collect_live_environment(runner=runner),
        "menu": collect_menu_context(runner=runner),
        "journal_snippets": _collect_journal_snippets(runner=runner),
    }
    json_result = write_rescue_json_evidence("boot", "boot_evidence_latest.json", bundle, runner=runner)
    lines = [
        f"generated_at: {bundle['generated_at']}",
        f"hostname: {bundle['boot'].get('hostname')}",
        f"kernel: {bundle['boot'].get('kernel')}",
        f"firmware: {bundle['bootloader'].get('firmware_mode')}",
        f"menu_mode: {bundle['menu'].get('menu_mode')}",
        f"browsers: {', '.join(bundle['live_environment'].get('browser_candidates') or []) or 'none'}",
    ]
    text_result = write_rescue_text_evidence("boot", "boot_evidence_latest.txt", "\n".join(lines), runner=runner)
    return {"status": "ok", "bundle": bundle, "json": json_result, "text": text_result}


def build_rescue_boot_logger_diagnostics() -> dict[str, Any]:
    return {
        "logger_version": RESCUE_BOOT_LOGGER_VERSION,
        "module": "core.rescue_boot_logger",
        "public_functions": [
            "collect_boot_context",
            "collect_bootloader_context",
            "collect_kernel_cmdline",
            "collect_live_environment",
            "collect_menu_context",
            "write_boot_evidence_bundle",
            "build_rescue_boot_logger_diagnostics",
        ],
        "destructive_commands": False,
        "read_only_probes": True,
    }
