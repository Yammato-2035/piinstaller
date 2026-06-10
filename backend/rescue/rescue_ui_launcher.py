"""Rescue UI launcher status model and script validation (no runtime writes)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

GRAPHICAL_BROWSERS: tuple[str, ...] = (
    "chromium",
    "chromium-browser",
    "firefox-esr",
    "firefox",
)

TEXT_BROWSERS: tuple[str, ...] = ("w3m", "links", "links2", "lynx")

RESCUE_UI_STATUS_SCHEMA_VERSION = 1


def classify_browser_candidate(found: str | None) -> str:
    if not found:
        return "none"
    if found in GRAPHICAL_BROWSERS:
        return "graphical"
    if found in TEXT_BROWSERS:
        return "text"
    return "unknown"


def build_rescue_ui_status(
    *,
    ui_url: str,
    server_started: bool,
    browser_candidate: str = "",
    browser_started: bool = False,
    display_mode: str = "failed",
    menu_visible: bool = False,
    status: str = "review_required",
    reason: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": RESCUE_UI_STATUS_SCHEMA_VERSION,
        "rescue_ui": {
            "server_status": "started" if server_started else "failed",
            "url": ui_url,
            "display_mode": display_mode,
            "menu_visible": menu_visible,
            "status": status,
            "reason": reason,
        },
        "ui_url": ui_url,
        "server_started": server_started,
        "browser_candidate": browser_candidate,
        "browser_started": browser_started,
        "display_mode": display_mode,
        "menu_visible": menu_visible,
        "status": status,
        "reason": reason,
        "network_required": False,
        "telemetry_required": False,
        "secrets_exposed": False,
    }


def launcher_declares_review_when_no_graphical_browser(script_text: str) -> bool:
    return "review_required" in script_text and "no_graphical_browser" in script_text


def launcher_has_fallback_tui(script_text: str) -> bool:
    return "fallback_tui" in script_text and "Netzwerk verbinden" in script_text


def launcher_writes_status_json(script_text: str) -> bool:
    return "rescue-ui-status.json" in script_text


def launcher_does_not_claim_success_on_url_only(script_text: str) -> bool:
    lowered = script_text.lower()
    return (
        "url_only" in lowered
        and "review_required" in lowered
        and "no_graphical_browser" in lowered
        and '"status": "ready"' not in lowered
    )


def squashfs_package_list_has_graphical_browser(package_list_text: str) -> bool:
    browsers = ("chromium", "firefox", "firefox-esr", "xorg", "wayland", "cage", "weston")
    lowered = package_list_text.lower()
    return any(b in lowered for b in browsers)


def react_kiosk_blocked_reason(package_list_text: str) -> str:
    if squashfs_package_list_has_graphical_browser(package_list_text):
        return "browser_packages_present_launcher_or_display_issue"
    return "blocked_missing_browser_or_display_runtime"


def unit_has_no_network_online_hard_dependency(unit_text: str) -> bool:
    return "Requires=network-online.target" not in unit_text


def prepare_tree_skips_boot_network_onboarding(prepare_text: str) -> bool:
    """Boot hook must not enable network-onboarding at multi-user."""
    hook_blocks = re.findall(
        r"010-enable-setuphelfer-services\.hook\.chroot.*?EOF(.*?)EOF",
        prepare_text,
        flags=re.DOTALL,
    )
    if not hook_blocks:
        return False
    return all("setuphelfer-rescue-network-onboarding.service" not in block for block in hook_blocks)


def prepare_tree_skips_boot_telemetry_push(prepare_text: str) -> bool:
    hook_blocks = re.findall(
        r"010-enable-setuphelfer-services\.hook\.chroot.*?EOF(.*?)EOF",
        prepare_text,
        flags=re.DOTALL,
    )
    if not hook_blocks:
        return False
    return all("setuphelfer-rescue-telemetry-push.service" not in block for block in hook_blocks)


def validate_rescue_ui_status_payload(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("network_required") is True:
        errors.append("NETWORK_REQUIRED")
    if payload.get("telemetry_required") is True:
        errors.append("TELEMETRY_REQUIRED")
    mode = str(payload.get("display_mode") or "")
    visible = payload.get("menu_visible")
    status = str(payload.get("status") or "")
    if mode == "url_only" and visible is True:
        errors.append("URL_ONLY_CANNOT_BE_MENU_VISIBLE")
    if mode in ("url_only", "fallback_tui") and status == "ready":
        errors.append("NON_GRAPHICAL_CANNOT_BE_READY")
    return errors
