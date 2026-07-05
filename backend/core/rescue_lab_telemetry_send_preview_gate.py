"""
PI-RS-TEL-002 — gated send-preview orchestration (dry-run default, no auto-replay).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from core.rescue_lab_telemetry_client import send_rescue_lab_telemetry
from core.rescue_lab_telemetry_config import ENV_LIVE_TEST, load_rescue_lab_telemetry_config
from core.rescue_lab_telemetry_model import (
    build_synthetic_rescue_lab_payload,
    validate_rescue_lab_payload_no_pii,
)
from core.rescue_lab_telemetry_offline_queue_preview import (
    build_offline_queue_preview_item,
    write_offline_queue_preview_item,
)
from core.rescue_lab_telemetry_reachability import build_reachability_summary
from core.rescue_lab_telemetry_status import record_last_send_result
from core.rescue_lab_telemetry_model import RescueLabTelemetryResult

_LAST_SEND_PREVIEW: dict[str, Any] | None = None


@dataclass
class SendPreviewOptions:
    allow_send_when_reachable: bool = False
    create_offline_queue_preview_when_blocked: bool = True


def _live_test_enabled() -> bool:
    return (os.environ.get(ENV_LIVE_TEST) or "").strip().lower() in ("1", "true", "yes", "on")


def _preview_reason(reachability: dict[str, Any]) -> str:
    ns = str(reachability.get("network_state") or "")
    tr = str(reachability.get("telemetry_reachability") or "")
    if ns == "blocked_profile_disabled":
        return "profile_disabled"
    if ns == "blocked_missing_config":
        return "missing_config"
    if ns == "blocked_missing_secret":
        return "missing_secret"
    if tr in {"unreachable", "timeout", "tls_error", "dns_error", "http_error"}:
        return "telemetry_unreachable"
    if ns == "telemetry_unreachable":
        return "telemetry_unreachable"
    return "offline"


def execute_send_preview(
    *,
    profile_allowed: bool,
    options: SendPreviewOptions | None = None,
    http_probe: Callable[..., Any] | None = None,
    http_post: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    global _LAST_SEND_PREVIEW
    opts = options or SendPreviewOptions()
    payload = build_synthetic_rescue_lab_payload().to_dict()
    config = load_rescue_lab_telemetry_config()
    errors: list[str] = []
    warnings: list[str] = []

    if not profile_allowed:
        return _finalize_preview(
            code="RESCUE_LAB_TELEMETRY_BLOCKED",
            send_mode="blocked",
            network_state="blocked_profile_disabled",
            telemetry_reachability="skipped_profile_disabled",
            send_executed=False,
            offline_queue_preview_created=False,
            offline_queue_preview_path=None,
            errors=["feature_disabled:rescue_lab_telemetry_requires_lab_profile"],
        )

    ok, violations = validate_rescue_lab_payload_no_pii(payload)
    if not ok:
        errors.extend([f"pii_blocked:{v}" for v in violations])
        return _finalize_preview(
            code="RESCUE_LAB_TELEMETRY_BLOCKED",
            send_mode="blocked",
            network_state="blocked_missing_config",
            telemetry_reachability="not_checked",
            send_executed=False,
            offline_queue_preview_created=False,
            offline_queue_preview_path=None,
            errors=errors,
        )

    if not config.lab_base_url:
        errors.append("lab_base_url_not_configured")
        preview_path = _maybe_queue_preview(
            payload, opts, {"network_state": "blocked_missing_config"}, "missing_config", config.lab_base_url
        )
        return _finalize_preview(
            code="RESCUE_LAB_TELEMETRY_BLOCKED",
            send_mode="offline_queue_preview" if preview_path else "blocked",
            network_state="blocked_missing_config",
            telemetry_reachability="skipped_missing_config",
            send_executed=False,
            offline_queue_preview_created=bool(preview_path),
            offline_queue_preview_path=str(preview_path) if preview_path else None,
            errors=errors,
        )

    if not config.secret:
        errors.append("lab_secret_not_configured")
        preview_path = _maybe_queue_preview(
            payload, opts, {"network_state": "blocked_missing_secret"}, "missing_secret", config.lab_base_url
        )
        return _finalize_preview(
            code="RESCUE_LAB_TELEMETRY_BLOCKED",
            send_mode="offline_queue_preview" if preview_path else "blocked",
            network_state="blocked_missing_secret",
            telemetry_reachability="skipped_missing_secret",
            send_executed=False,
            offline_queue_preview_created=bool(preview_path),
            offline_queue_preview_path=str(preview_path) if preview_path else None,
            errors=errors,
        )

    reachability = build_reachability_summary(
        profile_allowed=True,
        lab_base_url=config.lab_base_url,
        secret=config.secret,
        http_probe=http_probe,
    )
    network_state = str(reachability.get("network_state") or "unknown")
    telemetry_reachability = str(reachability.get("telemetry_reachability") or "not_checked")
    warnings.extend(reachability.get("warnings") or [])

    live_allowed = (
        opts.allow_send_when_reachable
        and _live_test_enabled()
        and telemetry_reachability == "reachable"
    )

    if live_allowed:
        result = send_rescue_lab_telemetry(config, payload, http_post=http_post)
        record_last_send_result(result)
        code = (
            "RESCUE_LAB_TELEMETRY_ACCEPTED"
            if result.status == "accepted_rescue_lab_telemetry"
            else "RESCUE_LAB_TELEMETRY_BLOCKED"
            if result.status.startswith("blocked")
            else "RESCUE_LAB_TELEMETRY_REJECTED"
            if result.status in {"rejected_auth", "rejected_product_source_or_environment", "replay_nonce"}
            else "RESCUE_LAB_TELEMETRY_UNAVAILABLE"
        )
        return _finalize_preview(
            code=code,
            send_mode="live_lab_send",
            network_state=network_state,
            telemetry_reachability=telemetry_reachability,
            send_executed=True,
            offline_queue_preview_created=False,
            offline_queue_preview_path=None,
            errors=result.errors,
            warnings=result.warnings,
            send_result=result,
        )

    # dry-run / blocked path
    preview_path = None
    send_mode = "dry_run"
    blocked_for_queue = telemetry_reachability not in {"reachable"} or network_state in {
        "telemetry_unreachable",
        "blocked_missing_config",
        "blocked_missing_secret",
        "blocked_profile_disabled",
        "offline",
    }
    if blocked_for_queue:
        reason = _preview_reason(reachability)
        if opts.create_offline_queue_preview_when_blocked:
            preview_path = _maybe_queue_preview(payload, opts, reachability, reason, config.lab_base_url)
            if preview_path:
                send_mode = "offline_queue_preview"
    if not opts.allow_send_when_reachable:
        warnings.append("allow_send_when_reachable_false_dry_run_only")
    elif not _live_test_enabled():
        warnings.append("SETUPHELPER_ENABLE_LIVE_LAB_TELEMETRY_TEST_not_set")

    return _finalize_preview(
        code="RESCUE_LAB_TELEMETRY_BLOCKED",
        send_mode=send_mode,
        network_state=network_state,
        telemetry_reachability=telemetry_reachability,
        send_executed=False,
        offline_queue_preview_created=bool(preview_path),
        offline_queue_preview_path=str(preview_path) if preview_path else None,
        warnings=warnings,
        errors=errors,
    )


def _maybe_queue_preview(
    payload: dict[str, Any],
    opts: SendPreviewOptions,
    reachability: dict[str, Any],
    reason: str,
    would_send_to: str | None,
) -> Any:
    if not opts.create_offline_queue_preview_when_blocked:
        return None
    item = build_offline_queue_preview_item(payload, reason, reachability, would_send_to=would_send_to)
    return write_offline_queue_preview_item(item)


def _finalize_preview(
    *,
    code: str,
    send_mode: str,
    network_state: str,
    telemetry_reachability: str,
    send_executed: bool,
    offline_queue_preview_created: bool,
    offline_queue_preview_path: str | None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    send_result: RescueLabTelemetryResult | None = None,
) -> dict[str, Any]:
    global _LAST_SEND_PREVIEW
    from datetime import datetime, timezone

    from core.rescue_lab_telemetry_config import load_rescue_lab_telemetry_config

    cfg = load_rescue_lab_telemetry_config()
    body = {
        "code": code,
        "result": {
            "client_id": cfg.client_id,
            "product": "setuphelfer-rescue-stick",
            "source": "rescue_stick_lab_preview",
            "environment": "lab",
            "payload_kind": "rescue_preview",
            "send_mode": send_mode,
            "network_state": network_state,
            "telemetry_reachability": telemetry_reachability,
            "send_executed": send_executed,
            "offline_queue_preview_created": offline_queue_preview_created,
            "offline_queue_preview_path": offline_queue_preview_path,
            "http_status": send_result.http_status if send_result else None,
            "server_status": send_result.server_status if send_result else None,
            "sent_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "production_ready": False,
        },
        "warnings": warnings or [],
        "errors": errors or [],
    }
    _LAST_SEND_PREVIEW = body
    return body


def get_last_send_preview_result() -> dict[str, Any] | None:
    return _LAST_SEND_PREVIEW


def reset_send_preview_for_tests() -> None:
    global _LAST_SEND_PREVIEW
    _LAST_SEND_PREVIEW = None
