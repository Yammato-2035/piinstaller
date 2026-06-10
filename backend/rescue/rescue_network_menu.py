"""Rescue network menu flow validation — crash-safe, offline-first."""

from __future__ import annotations

import re


INTERACTIVE_NON_FATAL_ERRORS: tuple[str, ...] = (
    "NETWORKMANAGER_NOT_RUNNING",
    "WIFI_DEVICE_NOT_FOUND",
    "WIFI_NOT_CONFIGURED",
    "WIFI_CONNECT_FAILED",
    "DEFAULT_ROUTE_MISSING",
    "TELEMETRY_HEALTH_UNREACHABLE",
    "OFFLINE_BY_OPERATOR",
    "NMCLI_MISSING",
)


def network_script_disables_errexit_after_common(script_text: str) -> bool:
    """Sourcing common.sh enables errexit; network flows must disable it."""
    if "set +e" not in script_text:
        return False
    idx = script_text.find("setuphelfer-rescue-common.sh")
    if idx < 0:
        return False
    return "set +e" in script_text[idx:]


def network_script_has_interactive_non_fatal_exit(script_text: str) -> bool:
    return "INTERACTIVE" in script_text and any(
        code in script_text for code in INTERACTIVE_NON_FATAL_ERRORS
    )


def network_common_has_safe_interactive_wrapper(common_text: str) -> bool:
    return "setuphelfer_rescue_run_network_interactive" in common_text


def network_common_checks_nmcli(common_text: str) -> bool:
    return "command -v nmcli" in common_text


def network_common_tty_override(common_text: str) -> bool:
    return "SETUPHELFER_RESCUE_TTY" in common_text


def network_onboarding_skips_boot_without_user(script_text: str) -> bool:
    return "SKIPPED_BOOT_WAIT_USER" in script_text


def network_menu_tests_cover_cases(test_text: str) -> list[str]:
    required = (
        "NMCLI_MISSING",
        "WIFI_DEVICE_NOT_FOUND",
        "no networks",
        "abort",
        "return_to_menu",
    )
    missing = [r for r in required if r.lower() not in test_text.lower()]
    return missing
