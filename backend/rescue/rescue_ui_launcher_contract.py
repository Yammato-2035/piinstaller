"""Executable contract checks for rescue UI launcher (no runtime writes)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from rescue.rescue_fallback_tui import (
    fallback_tui_explains_safe_mode,
    fallback_tui_has_branded_title,
    fallback_tui_has_required_menu,
    fallback_tui_network_uses_safe_wrapper,
    fallback_tui_no_restore_backup_repair,
    fallback_tui_status_not_raw_json_only,
)
from rescue.rescue_network_menu import (
    network_common_checks_nmcli,
    network_common_has_safe_interactive_wrapper,
    network_common_tty_override,
    network_script_disables_errexit_after_common,
    network_script_has_interactive_non_fatal_exit,
)
from rescue.rescue_ui_launcher import (
    build_rescue_ui_status,
    launcher_declares_review_when_no_graphical_browser,
    launcher_does_not_claim_success_on_url_only,
    launcher_has_fallback_tui,
    launcher_writes_status_json,
    validate_rescue_ui_status_payload,
)

EXPECTED_FALLBACK_STATUS = {
    "server_started": True,
    "browser_started": False,
    "display_mode": "fallback_tui",
    "menu_visible": True,
    "status": "review_required",
    "reason": "no_graphical_browser_available_or_not_started",
}


def validate_launcher_script_contract(launcher_text: str) -> dict[str, Any]:
    checks = {
        "writes_status_json": launcher_writes_status_json(launcher_text),
        "has_fallback_tui": launcher_has_fallback_tui(launcher_text),
        "review_when_no_browser": launcher_declares_review_when_no_graphical_browser(launcher_text),
        "no_url_only_green": launcher_does_not_claim_success_on_url_only(launcher_text),
        "rescue_ui_status_path": "rescue-ui-status.json" in launcher_text,
        "fallback_tui_branded": fallback_tui_has_branded_title(launcher_text),
        "fallback_safe_mode_text": fallback_tui_explains_safe_mode(launcher_text),
        "fallback_required_menu": fallback_tui_has_required_menu(launcher_text),
        "status_summary_not_raw": fallback_tui_status_not_raw_json_only(launcher_text),
        "network_safe_wrapper": fallback_tui_network_uses_safe_wrapper(launcher_text),
        "no_restore_backup_repair": fallback_tui_no_restore_backup_repair(launcher_text),
    }
    errors = [k for k, ok in checks.items() if not ok]
    return {
        "checks": checks,
        "contract_ok": not errors,
        "errors": errors,
    }


def validate_network_scripts_contract(
    network_text: str,
    common_text: str,
) -> dict[str, Any]:
    checks = {
        "network_set_plus_e": network_script_disables_errexit_after_common(network_text),
        "network_non_fatal_interactive": network_script_has_interactive_non_fatal_exit(network_text),
        "common_safe_wrapper": network_common_has_safe_interactive_wrapper(common_text),
        "common_nmcli_check": network_common_checks_nmcli(common_text),
        "common_tty_override": network_common_tty_override(common_text),
        "return_to_menu_field": "return_to_menu" in network_text,
        "skipped_boot_wait_user": "SKIPPED_BOOT_WAIT_USER" in network_text,
    }
    errors = [k for k, ok in checks.items() if not ok]
    return {
        "checks": checks,
        "contract_ok": not errors,
        "errors": errors,
    }


def validate_expected_fallback_status_payload(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for key, expected in EXPECTED_FALLBACK_STATUS.items():
        if payload.get(key) != expected:
            errors.append(f"STATUS_{key.upper()}_MISMATCH")
    errors.extend(validate_rescue_ui_status_payload(payload))
    return errors


def build_expected_fallback_status_json() -> dict[str, Any]:
    return build_rescue_ui_status(
        ui_url="http://127.0.0.1:8765/rescue.html",
        server_started=True,
        browser_candidate="",
        browser_started=False,
        display_mode="fallback_tui",
        menu_visible=True,
        status="review_required",
        reason="no_graphical_browser_available_or_not_started",
    )


def simulate_fallback_status_contract() -> dict[str, Any]:
    payload = build_expected_fallback_status_json()
    errors = validate_expected_fallback_status_payload(payload)
    return {"payload": payload, "contract_ok": not errors, "errors": errors}


def read_script_from_paths(*paths: Path) -> str:
    for path in paths:
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return ""


def evaluate_workspace_launcher_contract(repo_root: Path) -> dict[str, Any]:
    image = repo_root / "scripts/rescue-live/image"
    launcher = read_script_from_paths(
        image / "setuphelfer-rescue-ui-launch",
    )
    network = read_script_from_paths(image / "setuphelfer-rescue-network-onboarding")
    common = read_script_from_paths(image / "setuphelfer-rescue-common.sh")
    launcher_result = validate_launcher_script_contract(launcher)
    network_result = validate_network_scripts_contract(network, common)
    status_result = simulate_fallback_status_contract()
    ok = (
        launcher_result["contract_ok"]
        and network_result["contract_ok"]
        and status_result["contract_ok"]
    )
    return {
        "launcher": launcher_result,
        "network": network_result,
        "fallback_status": status_result,
        "contract_ok": ok,
    }
