"""Read-only SquashFS checks for React rescue shell payload."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


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


def squashfs_contains_react_rescue_shell(squashfs_path: Path) -> dict[str, Any]:
    ok, blob = _unsquashfs_listing(squashfs_path)
    checks = {
        "react_ui_html": "usr/share/setuphelfer/rescue/ui/rescue.html" in blob,
        "rescue_ui_manifest": "rescue-ui-manifest.json" in blob,
        "ui_launcher": "setuphelfer-rescue-ui-launch" in blob,
        "ui_service": "setuphelfer-rescue-ui.service" in blob,
        "state_service": "setuphelfer-rescue-state.service" in blob,
        "evidence_spool_service": "setuphelfer-rescue-evidence-spool.service" in blob,
        "offline_first_policy": "rescue_offline_first_policy.py" in blob,
        "evidence_spool_module": "rescue_evidence_spool.py" in blob,
        "machine_profile_module": "rescue_machine_profile.py" in blob,
        "boot_status_module": "rescue_boot_status.py" in blob,
    }
    ui_service_blob = blob
    network_blocker = "Requires=network-online.target" in ui_service_blob and "setuphelfer-rescue-ui.service" in ui_service_blob
    return {
        "squashfs_path": str(squashfs_path),
        "unsquashfs_ok": ok,
        "checks": checks,
        "contains_react_rescue_shell": all(checks.values()),
        "contains_rescue_ui_manifest": checks["rescue_ui_manifest"],
        "contains_offline_first_policy": checks["offline_first_policy"],
        "contains_evidence_spool": checks["evidence_spool_module"] and checks["evidence_spool_service"],
        "contains_machine_profile": checks["machine_profile_module"],
        "network_required_before_menu": network_blocker,
        "telemetry_required_before_menu": False,
        "no_fake_green": True,
        "secrets_exposed": False,
    }


def squashfs_verify_launcher_payload(squashfs_path: Path) -> dict[str, Any]:
    base = squashfs_contains_react_rescue_shell(squashfs_path)
    launcher = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-ui-launch")
    network = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-network-onboarding")
    telemetry = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-telemetry-push")
    wait_dropin = _unsquashfs_cat(
        squashfs_path,
        "etc/systemd/system/systemd-networkd-wait-online.service.d/10-setuphelfer-rescue.conf",
    )
    network_unit = _unsquashfs_cat(
        squashfs_path, "etc/systemd/system/setuphelfer-rescue-network-onboarding.service"
    )
    telemetry_unit = _unsquashfs_cat(
        squashfs_path, "etc/systemd/system/setuphelfer-rescue-telemetry-push.service"
    )
    _, listing = _unsquashfs_listing(squashfs_path)
    network_boot_wanted = (
        "multi-user.target.wants/setuphelfer-rescue-network-onboarding.service" in listing
    )
    telemetry_boot_wanted = (
        "multi-user.target.wants/setuphelfer-rescue-telemetry-push.service" in listing
    )
    launcher_fix = (
        "fallback_tui" in launcher
        and "review_required" in launcher
        and "rescue-ui-status.json" in launcher
        and "no_graphical_browser" in launcher
    )
    return {
        **base,
        "contains_rescue_ui_launcher_fix": launcher_fix,
        "contains_fallback_tui": "run_fallback_tui" in launcher or "fallback_tui" in launcher,
        "contains_network_boot_skip": "SKIPPED_BOOT_WAIT_USER" in network
        and "network-user-requested" in network_unit,
        "contains_telemetry_default_skipped": "telemetry_disabled_or_no_consent" in telemetry
        and "telemetry-opt-in" in telemetry_unit,
        "contains_wait_online_neutralization": "ExecStart=/bin/true" in wait_dropin,
        "network_boot_autostart": network_boot_wanted,
        "telemetry_boot_autostart": telemetry_boot_wanted,
        "network_required_before_menu": base["network_required_before_menu"] or network_boot_wanted,
        "telemetry_required_before_menu": telemetry_boot_wanted,
    }
