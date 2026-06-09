"""Rescue boot status model — offline-first, no runtime writes."""

from __future__ import annotations

from typing import Any, Mapping


def build_rescue_boot_status(
    *,
    medium: Mapping[str, Any] | None = None,
    network: Mapping[str, Any] | None = None,
    telemetry: Mapping[str, Any] | None = None,
    ui: Mapping[str, Any] | None = None,
    rs001: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble normalized rescue boot status for UI/API."""
    return {
        "medium": dict(medium or _default_medium()),
        "network": dict(network or _default_network()),
        "telemetry": dict(telemetry or _default_telemetry()),
        "ui": dict(ui or _default_ui()),
        "rs001": dict(rs001 or _default_rs001()),
    }


def _default_medium() -> dict[str, Any]:
    return {
        "status": "review_required",
        "squashfs_hash_ok": None,
        "evidence_ok": None,
        "required": True,
    }


def _default_network() -> dict[str, Any]:
    return {
        "status": "not_configured",
        "required": False,
        "wifi_scan_started": False,
    }


def _default_telemetry() -> dict[str, Any]:
    return {
        "status": "disabled",
        "required": False,
        "opt_in": False,
    }


def _default_ui() -> dict[str, Any]:
    return {
        "mode": "react",
        "status": "starting",
        "shows_systemd_failures": False,
    }


def _default_rs001() -> dict[str, Any]:
    return {
        "status": "yellow",
        "reason": "hardware retest pending",
        "ready_for_operator_retest": False,
    }


def medium_status_from_checks(
    *,
    squashfs_hash_ok: bool | None,
    evidence_ok: bool | None,
) -> str:
    if squashfs_hash_ok is False or evidence_ok is False:
        return "failed"
    if squashfs_hash_ok is True and evidence_ok is True:
        return "ok"
    return "review_required"


def network_is_boot_blocker(network: Mapping[str, Any]) -> bool:
    return bool(network.get("required"))


def telemetry_is_boot_blocker(telemetry: Mapping[str, Any]) -> bool:
    return bool(telemetry.get("required")) and telemetry.get("status") not in (
        "disabled",
        "skipped",
    )
