"""
PI-RS-TEL-001 — in-memory last send status for DCC / evidence (no secrets).
"""

from __future__ import annotations

import os
from typing import Any

from core.rescue_lab_telemetry_config import ENV_CLIENT_SECRET, ENV_LAB_BASE_URL, load_rescue_lab_telemetry_config
from core.rescue_lab_telemetry_model import (
    RESCUE_LAB_CLIENT_ID_DEFAULT,
    RESCUE_LAB_ENVIRONMENT,
    RESCUE_LAB_PAYLOAD_KIND,
    RESCUE_LAB_PRODUCT,
    RESCUE_LAB_SOURCE,
    RescueLabTelemetryResult,
)

_LAST_SEND: RescueLabTelemetryResult | None = None
_LAST_SEND_STATUS = "pending"


def record_last_send_result(result: RescueLabTelemetryResult) -> None:
    global _LAST_SEND, _LAST_SEND_STATUS
    _LAST_SEND = result
    if result.status == "accepted_rescue_lab_telemetry":
        _LAST_SEND_STATUS = "accepted"
    elif result.status in {"blocked_missing_secret", "blocked_missing_lab_url", "blocked_pii_violation", "blocked_invalid_payload"}:
        _LAST_SEND_STATUS = "blocked"
    elif result.status in {"rejected_auth", "rejected_product_source_or_environment", "replay_nonce"}:
        _LAST_SEND_STATUS = "rejected"
    elif result.status == "rejected_or_unavailable":
        _LAST_SEND_STATUS = "unavailable"
    else:
        _LAST_SEND_STATUS = "rejected"


def reset_last_send_status_for_tests() -> None:
    global _LAST_SEND, _LAST_SEND_STATUS
    _LAST_SEND = None
    _LAST_SEND_STATUS = "pending"


def build_rescue_lab_telemetry_dashboard_status() -> dict[str, Any]:
    config = load_rescue_lab_telemetry_config()
    last = _LAST_SEND.to_dict() if _LAST_SEND else None
    next_action = "configure_lab_secret_and_base_url"
    if not config.secret:
        next_action = "set_SETUPHELPER_LAB_CLIENT_FAKE_RESCUE_STICK_SECRET"
    elif not config.lab_base_url:
        next_action = "set_SETUPHELPER_TELEMETRY_LAB_BASE_URL"
    elif _LAST_SEND_STATUS == "pending":
        next_action = "invoke_lab_send_preview_once"
    elif _LAST_SEND_STATUS == "accepted":
        next_action = "optional_PI-RS-TEL-002_network_reachability_preview"
    return {
        "title": "Rescue Telemetry Lab Client",
        "client_id": config.client_id or RESCUE_LAB_CLIENT_ID_DEFAULT,
        "product": RESCUE_LAB_PRODUCT,
        "source": RESCUE_LAB_SOURCE,
        "environment": RESCUE_LAB_ENVIRONMENT,
        "payload_kind": RESCUE_LAB_PAYLOAD_KIND,
        "secret_configured": bool(config.secret),
        "lab_base_url_configured": bool(config.lab_base_url),
        "last_send_status": _LAST_SEND_STATUS,
        "production_ready": False,
        "next_required_action": next_action,
        "last_result": last,
        "env_keys": {
            "lab_base_url": ENV_LAB_BASE_URL,
            "client_id": "SETUPHELPER_LAB_CLIENT_FAKE_RESCUE_STICK_ID",
            "client_secret": ENV_CLIENT_SECRET,
        },
    }


def export_redacted_config_status() -> dict[str, Any]:
    status = build_rescue_lab_telemetry_dashboard_status()
    status.pop("last_result", None)
    return status
