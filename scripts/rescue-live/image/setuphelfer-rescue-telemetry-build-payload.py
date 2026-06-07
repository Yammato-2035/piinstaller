#!/usr/bin/env python3
"""Build rescue boot/network telemetry JSON payload (no secrets, no inline shell heredocs)."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sh(cmd: str) -> str:
    try:
        return subprocess.check_output(
            cmd, shell=True, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, OSError):
        return ""


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def read_json_file(path: Path) -> Any:
    raw = read_text_file(path)
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"parse_error": True, "raw_length": len(raw)}


def redact_secrets(text: str) -> str:
    """Drop lines that might contain passphrases or tokens."""
    out: list[str] = []
    for line in text.splitlines():
        lower = line.lower()
        if any(k in lower for k in ("psk=", "password", "passphrase", "token", "secret", "private key")):
            out.append("[REDACTED]")
        else:
            out.append(line)
    return "\n".join(out)


def collect_dmesg(max_lines: int = 200) -> str:
    dmesg = sh(f"dmesg 2>/dev/null | tail -{max_lines}")
    if dmesg:
        return redact_secrets(dmesg)
    journal = sh(
        "journalctl -k -b --no-pager 2>/dev/null | "
        "grep -Ei 'iwlwifi|firmware|bluetooth|btintel|pcie|ACPI|squashfs|loop0|usb|reset|I/O error' "
        f"| tail -{max_lines}"
    )
    return redact_secrets(journal)


def active_connection_summary() -> dict[str, Any]:
    active = sh("nmcli -t -f NAME,UUID,TYPE,DEVICE connection show --active 2>/dev/null")
    lines = [ln for ln in active.splitlines() if ln.strip()]
    return {
        "active_connection_count": len(lines),
        "active_connections_redacted": redact_secrets(active),
    }


def boot_mode_hint() -> dict[str, Any]:
    cmdline = sh("tr '\\0' ' ' < /proc/cmdline")
    return {
        "cmdline": cmdline,
        "efi_boot": os.path.isdir("/sys/firmware/efi"),
        "setuphelfer_rescue": "setuphelfer_rescue=1" in cmdline,
        "setuphelfer_network_onboarding": "setuphelfer_network_onboarding=1" in cmdline,
        "setuphelfer_start_assistant": "setuphelfer_start_assistant=1" in cmdline,
        "setuphelfer_msi_compat": "pci=noaer" in cmdline,
        "setuphelfer_diagnose": "setuphelfer_diagnose=1" in cmdline,
    }


def build_payload(state_dir: Path) -> dict[str, Any]:
    iso_sha256 = os.environ.get("SETUPHELFER_RESCUE_ISO_SHA256", "")
    if not iso_sha256:
        sha_path = Path("/run/live/medium/live/filesystem.squashfs.sha256")
        if sha_path.is_file():
            iso_sha256 = sha_path.read_text(encoding="utf-8", errors="replace").split()[0]

    version_path = Path("/opt/setuphelfer-rescue/config/version.json")
    image_version = read_json_file(version_path) if version_path.is_file() else {}

    lsblk_raw = sh("lsblk -J 2>/dev/null") or "[]"
    try:
        lsblk_json = json.loads(lsblk_raw)
    except json.JSONDecodeError:
        lsblk_json = {"parse_error": True}

    payload: dict[str, Any] = {
        "schema_version": 1,
        "source": "rescue_stick",
        "payload_kind": "rescue_boot_network_telemetry",
        "boot_id": sh("tr -d '\\n' < /proc/sys/kernel/random/boot_id") or "unknown",
        "machine_hint": "msi",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "iso_sha256": iso_sha256,
        "image_version": image_version.get("project_version"),
        "network": {
            "ip_addr_json": json.loads(sh("ip -j addr 2>/dev/null") or "[]"),
            "route_json": json.loads(sh("ip -j route 2>/dev/null") or "[]"),
            "nmcli_general": sh("nmcli general status 2>/dev/null"),
            "nmcli_device": sh("nmcli device status 2>/dev/null"),
            "rfkill": sh("rfkill list 2>/dev/null"),
            "active_connection": active_connection_summary(),
        },
        "hardware": {
            "uname": sh("uname -a"),
            "boot_mode": boot_mode_hint(),
            "lspci": sh("lspci 2>/dev/null"),
            "lsusb": sh("lsusb 2>/dev/null"),
            "lsblk": lsblk_json,
        },
        "kernel_warnings": {
            "filtered_dmesg": collect_dmesg(),
            "networkmanager_journal": redact_secrets(
                sh("journalctl -u NetworkManager -b --no-pager 2>/dev/null | tail -200")
            ),
            "warning_journal": redact_secrets(
                sh("journalctl -b -p warning --no-pager 2>/dev/null | tail -300")
            ),
        },
        "media_check": read_json_file(state_dir / "media-check.json"),
        "network_onboarding": read_json_file(state_dir / "network-onboarding.json"),
        "operator_notes": [],
        "secrets_exposed": False,
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    payload["payload_hash_sha256"] = hashlib.sha256(body).hexdigest()
    return payload


def main() -> int:
    state_dir = Path(os.environ.get("SETUPHELFER_RESCUE_STATE_DIR", "/run/setuphelfer-rescue"))
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    payload = build_payload(state_dir)
    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    if out_path:
        out_path.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
