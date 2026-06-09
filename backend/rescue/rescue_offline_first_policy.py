"""Offline-first rescue boot policy — pure rules for tests and UI gating."""

from __future__ import annotations

from typing import Any, Mapping

POLICY_RULES: tuple[str, ...] = (
    "rescue_boot_without_network",
    "network_not_boot_prerequisite",
    "wifi_scan_user_initiated",
    "telemetry_default_disabled",
    "telemetry_requires_opt_in",
    "missing_network_review_not_failed",
    "missing_telemetry_skipped_not_failed",
    "medium_check_isolated_from_optional_services",
    "optional_service_failures_no_medium_warning",
    "first_screen_calm_main_menu",
)

FORBIDDEN_BOOT_BLOCKERS: tuple[str, ...] = (
    "Requires=network-online.target",
    "Requires=network.target",
    "Wants=network-online.target",
)


def optional_network_status(status: str) -> str:
    if status in ("unavailable", "not_configured", ""):
        return "review_required"
    return status


def optional_telemetry_status(status: str, *, opt_in: bool = False) -> str:
    if not opt_in:
        return "skipped" if status in ("failed", "queued", "sent") else "disabled"
    return status


def live_medium_warning_allowed_causes(cause: str) -> bool:
    """Only medium/squashfs/evidence/hash issues may trigger live-medium warning."""
    allowed = {
        "squashfs_missing",
        "squashfs_hash_mismatch",
        "evidence_missing",
        "required_file_missing",
        "medium_unstable",
    }
    blocked = {
        "network_failed",
        "telemetry_failed",
        "systemd_networkd_wait_online",
        "wifi_not_found",
    }
    if cause in blocked:
        return False
    return cause in allowed


def beginner_ui_may_show_systemd_failure(ui: Mapping[str, Any]) -> bool:
    return bool(ui.get("shows_systemd_failures"))
