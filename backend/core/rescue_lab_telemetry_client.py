"""
PI-RS-TEL-001 — HTTP client for synthetic Rescue Stick lab telemetry send (lab URL only).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable

from core.rescue_lab_telemetry_model import (
    RESCUE_LAB_CLIENT_ID_DEFAULT,
    RESCUE_LAB_ENVIRONMENT,
    RESCUE_LAB_PAYLOAD_KIND,
    RESCUE_LAB_PRODUCT,
    RESCUE_LAB_SOURCE,
    RescueLabTelemetryConfig,
    RescueLabTelemetryResult,
    build_rescue_lab_envelope,
    validate_rescue_lab_payload_no_pii,
)
from core.rescue_lab_telemetry_config import load_rescue_lab_telemetry_config

__all__ = ["load_rescue_lab_telemetry_config", "send_rescue_lab_telemetry"]


def _map_http_status(http_status: int | None, body: dict[str, Any] | None) -> tuple[str, str | None, str]:
    reason = (body or {}).get("reason_code") if isinstance(body, dict) else None
    if http_status == 202:
        return "accepted_rescue_lab_telemetry", str(reason or "accepted_rescue_lab_telemetry"), "new"
    if http_status == 401:
        return "rejected_auth", str(reason or "rejected_auth"), "unknown"
    if http_status == 403:
        return "rejected_product_source_or_environment", str(reason or "rejected_product_source_or_environment"), "unknown"
    if http_status == 409:
        return "replay_nonce", str(reason or "replay_nonce"), "replay"
    return "rejected_or_unavailable", str(reason) if reason else None, "unknown"


def send_rescue_lab_telemetry(
    config: RescueLabTelemetryConfig,
    payload: dict[str, Any],
    *,
    http_post: Callable[..., Any] | None = None,
) -> RescueLabTelemetryResult:
    from core.rescue_lab_telemetry_status import record_last_send_result

    sent_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    base_result = {
        "client_id": config.client_id,
        "product": str(payload.get("product") or RESCUE_LAB_PRODUCT),
        "source": str(payload.get("source") or RESCUE_LAB_SOURCE),
        "environment": str(payload.get("environment") or RESCUE_LAB_ENVIRONMENT),
        "payload_kind": str(payload.get("payload_kind") or RESCUE_LAB_PAYLOAD_KIND),
        "http_status": None,
        "server_status": None,
        "nonce_status": "unknown",
        "sent_at": sent_at,
        "production_ready": False,
    }

    ok, violations = validate_rescue_lab_payload_no_pii(payload)
    if not ok:
        result = RescueLabTelemetryResult(
            status="blocked_pii_violation",
            errors=[f"payload_blocked:{v}" for v in violations],
            **base_result,
        )
        record_last_send_result(result)
        return result

    if not config.secret:
        result = RescueLabTelemetryResult(
            status="blocked_missing_secret",
            errors=["SETUPHELPER_LAB_CLIENT_FAKE_RESCUE_STICK_SECRET not configured — lab send blocked."],
            **base_result,
        )
        record_last_send_result(result)
        return result

    if not config.lab_base_url:
        result = RescueLabTelemetryResult(
            status="blocked_missing_lab_url",
            errors=["SETUPHELPER_TELEMETRY_LAB_BASE_URL not configured — lab send blocked."],
            **base_result,
        )
        record_last_send_result(result)
        return result

    try:
        envelope = build_rescue_lab_envelope(config=config, payload=payload, secret=config.secret)
    except ValueError as exc:
        result = RescueLabTelemetryResult(
            status="blocked_invalid_payload",
            errors=[str(exc)],
            **base_result,
        )
        record_last_send_result(result)
        return result

    try:
        if http_post is not None:
            http_status, response_body = http_post(envelope)
        else:
            http_status, response_body = _default_http_post(envelope)
    except urllib.error.URLError as exc:
        result = RescueLabTelemetryResult(
            status="rejected_or_unavailable",
            errors=[f"transport_error:{type(exc).__name__}"],
            **base_result,
        )
        record_last_send_result(result)
        return result
    except Exception as exc:  # noqa: BLE001
        result = RescueLabTelemetryResult(
            status="rejected_or_unavailable",
            errors=[f"unexpected_error:{type(exc).__name__}"],
            **base_result,
        )
        record_last_send_result(result)
        return result

    server_status, server_reason, nonce_status = _map_http_status(http_status, response_body)
    status = server_status if http_status in {202, 401, 403, 409} else "rejected_or_unavailable"
    result = RescueLabTelemetryResult(
        status=status,
        client_id=base_result["client_id"],
        product=base_result["product"],
        source=base_result["source"],
        environment=base_result["environment"],
        payload_kind=base_result["payload_kind"],
        http_status=http_status,
        server_status=server_reason,
        nonce_status=nonce_status,
        sent_at=base_result["sent_at"],
        production_ready=False,
        warnings=[] if http_status == 202 else [f"http_status:{http_status}"],
    )
    record_last_send_result(result)
    return result


def _default_http_post(envelope: Any) -> tuple[int, dict[str, Any] | None]:
    req = urllib.request.Request(
        envelope.ingest_url,
        data=envelope.body_bytes,
        headers=envelope.headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            body = json.loads(raw) if raw.strip() else {}
            return int(resp.status), body if isinstance(body, dict) else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            body = {}
        return int(exc.code), body if isinstance(body, dict) else None
