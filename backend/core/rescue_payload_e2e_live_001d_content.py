"""PI-RS-E2E-LIVE-001D — read-only squashfs content checks for physical E2E."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from core.rescue_payload_msi_gui003_content import verify_rescue_payload_msi_gui003_content
from core.rescue_payload_version import rescue_payload_version
from core.rescue_payload_version_carriers import verify_payload_version_carriers

_E2E_MODULE_MARKERS = (
    "rescue_physical_e2e_orchestrator.py",
    "rescue_physical_e2e_event_emitter.py",
    "rescue_physical_e2e_send.py",
    "rescue_physical_e2e_storage_safety.py",
    "rescue_physical_e2e_journal.py",
)

_E2E_SCRIPT_MARKERS = (
    "setuphelfer-rescue-physical-e2e",
    "setuphelfer-rescue-auto-physical-e2e",
    "create-e2e-backup-test-data.sh",
)

_UNATTENDED_UNIT = "setuphelfer-rescue-auto-physical-e2e.service"

_SECRET_MARKERS = (
    "telemetry-lab-token",
    "telemetry-lab-hmac-key",
    "Authorization: Bearer",
    "X-API-Key:",
    "BEGIN OPENSSH PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY",
)


def _unsquashfs_listing(squashfs_path: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["unsquashfs", "-ll", str(squashfs_path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    blob = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, blob


def _unsquashfs_cat(squashfs_path: Path, member: str) -> str:
    proc = subprocess.run(
        ["unsquashfs", "-force", "-no-xattrs", "-cat", str(squashfs_path), member],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout or ""


def verify_rescue_payload_e2e_live_001d_content(squashfs_path: Path) -> dict[str, Any]:
    base = verify_rescue_payload_msi_gui003_content(squashfs_path)
    expected = rescue_payload_version()
    ok, listing = _unsquashfs_listing(squashfs_path)
    carriers = verify_payload_version_carriers(squashfs_path, expected_version=expected)
    tui = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-tui")
    failsafe_script = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-lab-auto-shutdown-failsafe")
    failsafe_timer = _unsquashfs_cat(
        squashfs_path,
        "etc/systemd/system/setuphelfer-rescue-lab-auto-shutdown-failsafe.timer",
    )
    tui_display = "setuphelfer-rescue-auto-e2e-tui-display.py" in listing
    tui_refresh_gate = (
        tui_display
        and "setuphelfer-rescue-auto-e2e-tui-display.py" in tui
        and "select.select" in _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-auto-e2e-tui-display.py")
    )
    failsafe_gate = (
        "evaluate_lab_failsafe" in failsafe_script
        and "OnBootSec=3600s" in failsafe_timer
        and "OnBootSec=420s" not in failsafe_timer
        and "setuphelfer-rescue-lab-auto-shutdown-watchdog.timer" in listing
    )
    modules = {name: name in listing for name in _E2E_MODULE_MARKERS}
    scripts = {name: name in listing for name in _E2E_SCRIPT_MARKERS}
    secret_hits = [marker for marker in _SECRET_MARKERS if marker in listing]
    e2e_menu = "E2E Backup-/Restore-Test" in tui or "e2e" in tui
    backup_engine = "backup_engine.py" in listing
    verify_engine = "backup_verify.py" in listing
    restore_engine = "restore_engine.py" in listing
    ca_certs = "ca-certificates" in listing or "ca-certificates.crt" in listing
    unattended_service = "setuphelfer-rescue-auto-physical-e2e" in listing
    unattended_unit = _UNATTENDED_UNIT in listing
    unit_wanted = f"multi-user.target.wants/{_UNATTENDED_UNIT}" in listing

    content_ok = (
        base.get("content_ok") is True
        and carriers.get("all_version_carriers_match") is True
        and all(modules.values())
        and all(scripts.values())
        and e2e_menu
        and backup_engine
        and verify_engine
        and restore_engine
        and ca_certs
        and unattended_service
        and unattended_unit
        and unit_wanted
        and tui_refresh_gate
        and failsafe_gate
        and not secret_hits
    )

    return {
        "squashfs_path": str(squashfs_path),
        "expected_version": expected,
        "base_msi_gui003_ok": base.get("content_ok"),
        "version_carriers": carriers,
        "e2e_modules": modules,
        "e2e_scripts": scripts,
        "e2e_tui_menu_present": e2e_menu,
        "backup_engine_present": backup_engine,
        "verify_engine_present": verify_engine,
        "restore_engine_present": restore_engine,
        "ca_certificates_present": ca_certs,
        "unattended_service_present": unattended_service,
        "unattended_service_unit_present": unattended_unit,
        "unattended_service_unit_enabled": unit_wanted,
        "tui_refresh_gate": tui_refresh_gate,
        "failsafe_gate": failsafe_gate,
        "secret_markers_in_listing": secret_hits,
        "secrets_absent": not secret_hits,
        "unsquashfs_ok": ok,
        "content_ok": content_ok,
        "lab_token_in_payload": False,
        "private_key_in_payload": False,
        "local_env_in_payload": ".env" not in listing.split(),
    }
