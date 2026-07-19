"""PI-RS-TEL-SEND-001 — gated Rescue Stick cloud lab telemetry send."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

from core.rescue_stick_cloud_lab_config import rescue_stick_lab_send_config_from_env
from core.rescue_stick_cloud_lab_models import (
    CONSENT_STATUS_GRANTED_LAB,
    DEFAULT_CLOUD_INGEST_URL,
    LAB_CLIENT_ID,
    LAB_SOURCE,
    OPERATOR_APPROVAL_EXPLICIT,
    RescueStickLabSendConfig,
    RescueStickLabSendResult,
    RescueStickLabSendStatus,
)
from core.rescue_stick_cloud_lab_payload import (
    assert_no_pii_in_payload,
    build_rescue_stick_lab_payload,
    redact_payload_for_preview,
)

HttpTransportFn = Callable[[str, bytes, dict[str, str], int], tuple[int, str, dict[str, str]]]
HealthCheckFn = Callable[[str, int], str]

_SECRET_RE = re.compile(
    r"(Authorization:\s*Bearer\s+\S+|(?:Authorization|X-API-Key|api_key|\bsecret\b|\btoken\b|hmac|signature)(?:[=:]\S+)?)",
    re.IGNORECASE,
)


def _default_http_transport(
    url: str, body: bytes, headers: dict[str, str], timeout_seconds: int
) -> tuple[int, str, dict[str, str]]:
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            return response.status, response_body, dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        return exc.code, body_text, dict(exc.headers.items()) if exc.headers else {}
    except urllib.error.URLError as exc:
        return 0, str(exc.reason), {}


def _default_health_check(ingest_url: str, timeout_seconds: int) -> str:
    health_url = ingest_url.replace("/v1/telemetry/ingest", "/v1/telemetry/health")
    req = urllib.request.Request(health_url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            if response.status != 200:
                return "health_not_ok"
            body = response.read().decode("utf-8", errors="replace")
            data = json.loads(body)
            if str(data.get("status", "")).lower() == "ok":
                return "health_ok"
            return "health_not_ok"
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TypeError, ValueError):
        return "health_not_ok"


def _token_present(token_file: str) -> bool:
    if not token_file:
        return False
    path = Path(token_file)
    return path.is_file() and path.stat().st_size > 0


def _read_bearer_token(token_file: str) -> str:
    return Path(token_file).read_text(encoding="utf-8").strip()


def _classify_http_response(status_code: int, body: str) -> str:
    if status_code == 200:
        try:
            data = json.loads(body)
            if data.get("accepted") is True or data.get("status") in {"accepted", "lab_send_accepted"}:
                return "lab_send_accepted"
        except json.JSONDecodeError:
            pass
        return "lab_send_accepted"
    if status_code in {401, 403}:
        return "lab_send_rejected_auth"
    if status_code == 422:
        return "lab_send_rejected_schema"
    if status_code == 0:
        return "lab_send_failed_transport"
    return "lab_send_rejected"


def _extract_request_id(body: str, response_headers: Mapping[str, str]) -> str:
    for header_name in ("X-Request-Id", "x-request-id"):
        if header_name in response_headers and response_headers[header_name]:
            return str(response_headers[header_name])
    try:
        data = json.loads(body)
        for key in ("request_id", "requestId", "id"):
            if data.get(key):
                return str(data[key])
    except json.JSONDecodeError:
        pass
    return ""


def redact_secret_material(text: str) -> str:
    redacted = _SECRET_RE.sub("[redacted]", text)
    return re.sub(r"Bearer\s+\S+", "Bearer [redacted]", redacted, flags=re.IGNORECASE)


def evaluate_rescue_stick_lab_preconditions(
    config: RescueStickLabSendConfig,
    *,
    health_check: HealthCheckFn | None = None,
) -> RescueStickLabSendResult:
    health_fn = health_check or _default_health_check
    health_prerequisite = health_fn(config.ingest_url, config.timeout_seconds)
    auth_present = _token_present(config.token_file)

    if health_prerequisite != "health_ok":
        return RescueStickLabSendResult(
            send_status=RescueStickLabSendStatus.BLOCKED_HEALTH_NOT_OK,
            health_prerequisite=health_prerequisite,
            consent_status=config.consent_status,
            operator_approval=config.operator_approval,
            auth_present=auth_present,
            lab_send_enabled=config.lab_send_enabled,
            endpoint=config.ingest_url,
            source=LAB_SOURCE,
            client_id=LAB_CLIENT_ID,
        )
    if config.consent_status != CONSENT_STATUS_GRANTED_LAB:
        return RescueStickLabSendResult(
            send_status=RescueStickLabSendStatus.BLOCKED_MISSING_CONSENT,
            health_prerequisite=health_prerequisite,
            consent_status=config.consent_status,
            operator_approval=config.operator_approval,
            auth_present=auth_present,
            lab_send_enabled=config.lab_send_enabled,
            endpoint=config.ingest_url,
            source=LAB_SOURCE,
            client_id=LAB_CLIENT_ID,
        )
    if config.operator_approval != OPERATOR_APPROVAL_EXPLICIT:
        return RescueStickLabSendResult(
            send_status=RescueStickLabSendStatus.BLOCKED_MISSING_OPERATOR_APPROVAL,
            health_prerequisite=health_prerequisite,
            consent_status=config.consent_status,
            operator_approval=config.operator_approval,
            auth_present=auth_present,
            lab_send_enabled=config.lab_send_enabled,
            endpoint=config.ingest_url,
            source=LAB_SOURCE,
            client_id=LAB_CLIENT_ID,
        )
    if not config.lab_send_enabled:
        return RescueStickLabSendResult(
            send_status=RescueStickLabSendStatus.BLOCKED_LAB_SEND_DISABLED,
            health_prerequisite=health_prerequisite,
            consent_status=config.consent_status,
            operator_approval=config.operator_approval,
            auth_present=auth_present,
            lab_send_enabled=config.lab_send_enabled,
            endpoint=config.ingest_url,
            source=LAB_SOURCE,
            client_id=LAB_CLIENT_ID,
        )
    if not auth_present:
        return RescueStickLabSendResult(
            send_status=RescueStickLabSendStatus.BLOCKED_MISSING_AUTH,
            health_prerequisite=health_prerequisite,
            consent_status=config.consent_status,
            operator_approval=config.operator_approval,
            auth_present=auth_present,
            lab_send_enabled=config.lab_send_enabled,
            endpoint=config.ingest_url,
            source=LAB_SOURCE,
            client_id=LAB_CLIENT_ID,
        )

    payload = build_rescue_stick_lab_payload(
        stick_version=config.stick_version,
        boot_mode=config.boot_mode,
    )
    assert_no_pii_in_payload(payload)
    preview = redact_payload_for_preview(payload)

    return RescueStickLabSendResult(
        send_status=RescueStickLabSendStatus.LAB_SEND_READY,
        health_prerequisite=health_prerequisite,
        consent_status=config.consent_status,
        operator_approval=config.operator_approval,
        auth_present=auth_present,
        lab_send_enabled=config.lab_send_enabled,
        endpoint=config.ingest_url,
        payload_preview_redacted=preview,
        payload_hash=str(preview.get("payload_hash", "")),
        source=LAB_SOURCE,
        client_id=LAB_CLIENT_ID,
        contains_pii=False,
        raw_logs_visible=False,
    )


def _build_send_payload(
    config: RescueStickLabSendConfig,
    *,
    discovery_summary: Mapping[str, Any] | None = None,
    host_id_hash: str | None = None,
) -> dict[str, Any]:
    payload = build_rescue_stick_lab_payload(
        stick_version=config.stick_version,
        boot_mode=config.boot_mode,
        host_id_hash=host_id_hash,
        discovery_summary=discovery_summary,
    )
    assert_no_pii_in_payload(payload)
    return payload


def preview_rescue_stick_lab_send(
    config: RescueStickLabSendConfig | None = None,
    *,
    health_check: HealthCheckFn | None = None,
) -> RescueStickLabSendResult:
    cfg = config or rescue_stick_lab_send_config_from_env()
    result = evaluate_rescue_stick_lab_preconditions(cfg, health_check=health_check)
    if result.send_status == RescueStickLabSendStatus.LAB_SEND_READY:
        return RescueStickLabSendResult(
            send_status=RescueStickLabSendStatus.DRY_RUN_READY,
            health_prerequisite=result.health_prerequisite,
            consent_status=result.consent_status,
            operator_approval=result.operator_approval,
            auth_present=result.auth_present,
            lab_send_enabled=result.lab_send_enabled,
            endpoint=result.endpoint,
            payload_preview_redacted=result.payload_preview_redacted,
            payload_hash=result.payload_hash,
            source=result.source,
            client_id=result.client_id,
            contains_pii=False,
            raw_logs_visible=False,
            real_send_executed=False,
        )
    return result


def execute_rescue_stick_lab_send(
    config: RescueStickLabSendConfig | None = None,
    *,
    health_check: HealthCheckFn | None = None,
    http_transport: HttpTransportFn | None = None,
    request_id_factory: Callable[[], str] | None = None,
    discovery_summary: Mapping[str, Any] | None = None,
    host_id_hash: str | None = None,
) -> RescueStickLabSendResult:
    cfg = config or rescue_stick_lab_send_config_from_env()
    preview = evaluate_rescue_stick_lab_preconditions(cfg, health_check=health_check)
    if preview.send_status != RescueStickLabSendStatus.LAB_SEND_READY:
        return preview

    transport = http_transport or _default_http_transport
    request_id = (request_id_factory or (lambda: f"req-{uuid4()}"))()

    payload = _build_send_payload(
        cfg,
        discovery_summary=discovery_summary,
        host_id_hash=host_id_hash,
    )
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    token = _read_bearer_token(cfg.token_file)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-Request-Id": request_id,
        "X-Client-Id": LAB_CLIENT_ID,
    }

    status_code, response_body, response_headers = transport(
        cfg.ingest_url,
        body,
        headers,
        cfg.timeout_seconds,
    )
    classification = _classify_http_response(status_code, response_body)
    resolved_request_id = _extract_request_id(response_body, response_headers) or request_id

    if classification == "lab_send_accepted":
        send_status = RescueStickLabSendStatus.LAB_SEND_ACCEPTED
    elif classification.startswith("lab_send_rejected"):
        send_status = RescueStickLabSendStatus.LAB_SEND_REJECTED
    else:
        send_status = RescueStickLabSendStatus.LAB_SEND_FAILED

    return RescueStickLabSendResult(
        send_status=send_status,
        health_prerequisite=preview.health_prerequisite,
        consent_status=preview.consent_status,
        operator_approval=preview.operator_approval,
        auth_present=True,
        lab_send_enabled=True,
        real_send_executed=True,
        contains_pii=False,
        raw_secret_visible=False,
        raw_logs_visible=False,
        endpoint=cfg.ingest_url or DEFAULT_CLOUD_INGEST_URL,
        payload_preview_redacted=redact_payload_for_preview(payload),
        payload_hash=str(payload.get("payload_hash", "")),
        request_id=resolved_request_id,
        response_status_code=status_code,
        response_classification=classification,
        source=LAB_SOURCE,
        client_id=LAB_CLIENT_ID,
        preview_only=False,
    )
