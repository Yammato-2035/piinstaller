"""Fallback TUI launcher validation — no runtime."""

from __future__ import annotations

import re


def fallback_tui_has_branded_title(script_text: str) -> bool:
    return "Setuphelfer Rettungsstick" in script_text


def fallback_tui_explains_safe_mode(script_text: str) -> bool:
    lowered = script_text.lower()
    return "notmenü" in lowered or "notmen" in lowered or "sicheren notmenü" in lowered


def fallback_tui_menu_items(script_text: str) -> list[str]:
    items: list[str] = []
    for match in re.finditer(r'"(\d+)"\s+"([^"]+)"', script_text):
        items.append(match.group(2))
    return items


def fallback_tui_required_menu_labels() -> tuple[str, ...]:
    return (
        "Status anzeigen",
        "Logs",
        "Netzwerk verbinden",
        "Neustart",
        "Ausschalten",
    )


def fallback_tui_has_required_menu(script_text: str) -> bool:
    text = script_text.lower()
    checks = (
        "status anzeigen" in text,
        "logs" in text and "stick" in text,
        "netzwerk verbinden" in text,
        "neustart" in text,
        ("ausschalten" in text or "herunterfahren" in text),
    )
    return all(checks)


def fallback_tui_status_not_raw_json_only(script_text: str) -> bool:
    """Status action must not dump raw JSON without summary helper."""
    if "summarize_rescue_ui_status" in script_text or "_status_summary" in script_text:
        return True
    if "Details anzeigen" in script_text:
        return True
    return 'cat "$STATUS_RUN"' not in script_text


def fallback_tui_network_uses_safe_wrapper(script_text: str) -> bool:
    return "setuphelfer_rescue_run_network_interactive" in script_text


def fallback_tui_no_restore_backup_repair(script_text: str) -> bool:
    lowered = script_text.lower()
    forbidden = ("backup starten", "restore starten", "reparatur starten", "installation starten")
    return not any(f in lowered for f in forbidden)
