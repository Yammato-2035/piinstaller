"""
Rescue-stick telemetry client — bridges windows_rescue_inspect with public telemetry_client_contract.

Opt-in, redaction-before-send, no server URL in preview. Server implementation stays private.
"""

from __future__ import annotations

import json
from typing import Any

from core.redaction_contract import redact_text
from core.telemetry_client_contract import (
    TelemetryClientEnvelope,
    TelemetryDataCategory,
    TelemetryOptInState,
    validate_client_envelope,
)
from core.windows_rescue_inspect import build_telemetry_envelope


def map_operator_consent_to_opt_in(consent_state: str | None) -> TelemetryOptInState:
    """Map rescue envelope consent strings to public opt-in states."""
    raw = (consent_state or "").strip().lower()
    if raw in {"granted", "enabled", "opt_in"}:
        return TelemetryOptInState.ENABLED
    if raw in {"pending", "pending_consent", "unknown"}:
        return TelemetryOptInState.PENDING_CONSENT
    return TelemetryOptInState.DISABLED


def infer_data_categories(rescue_envelope: dict[str, Any]) -> tuple[TelemetryDataCategory, ...]:
    """Derive public data categories from a rescue telemetry envelope."""
    cats: list[TelemetryDataCategory] = [TelemetryDataCategory.RESCUE_SESSION_META]
    if rescue_envelope.get("schema_version"):
        cats.append(TelemetryDataCategory.VERSION)
    hw = rescue_envelope.get("hardware")
    if isinstance(hw, dict) and hw:
        cats.append(TelemetryDataCategory.HARDWARE_CLASS)
    diag = rescue_envelope.get("diagnostics")
    if isinstance(diag, dict) and (diag.get("codes") or diag.get("severity")):
        cats.append(TelemetryDataCategory.ERROR_SUMMARY)
    transport = rescue_envelope.get("telemetry_transport")
    if isinstance(transport, dict) and transport.get("status"):
        cats.append(TelemetryDataCategory.RUNTIME_HEALTH)
    # stable order
    order = (
        TelemetryDataCategory.VERSION,
        TelemetryDataCategory.RUNTIME_HEALTH,
        TelemetryDataCategory.ERROR_SUMMARY,
        TelemetryDataCategory.HARDWARE_CLASS,
        TelemetryDataCategory.RESCUE_SESSION_META,
    )
    return tuple(c for c in order if c in cats)


def _redact_payload_dict(payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Apply redaction_contract to JSON-serialized payload (local preview only)."""
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    result = redact_text(raw)
    try:
        redacted = json.loads(result.redacted_text)
    except json.JSONDecodeError:
        redacted = {"redacted_preview": result.redacted_text}
    return redacted if isinstance(redacted, dict) else {"preview": redacted}, bool(result.categories_matched)


def build_rescue_stick_client_envelope(
    report: dict[str, Any],
    *,
    run_id: str,
    device_session_id: str | None = None,
    opt_in_state: TelemetryOptInState | None = None,
    local_preview_ok: bool = True,
    ack_status: str = "not_created",
    server_ack_id: str | None = None,
    server_confirmed_hash_sha256: str | None = None,
) -> TelemetryClientEnvelope:
    """
    Build a public TelemetryClientEnvelope from a rescue inspect report.

    Uses windows_rescue_inspect for transport envelope, then redaction_contract
    before exposing payload via telemetry_client_contract.
    """
    dsid = (device_session_id or "").strip() or f"devsess-{run_id[-12:]}"
    rescue_env = build_telemetry_envelope(
        report,
        run_id=run_id,
        device_session_id=dsid,
        ack_status=ack_status,
        server_ack_id=server_ack_id,
        server_confirmed_hash_sha256=server_confirmed_hash_sha256,
    )
    consent = str(rescue_env.get("operator_consent_state") or "")
    resolved_opt_in = opt_in_state if opt_in_state is not None else map_operator_consent_to_opt_in(consent)
    redacted_payload, redaction_applied = _redact_payload_dict(rescue_env)
    return TelemetryClientEnvelope(
        schema_version=1,
        opt_in_state=resolved_opt_in,
        data_categories=infer_data_categories(rescue_env),
        redaction_applied=redaction_applied,
        local_preview_ok=local_preview_ok,
        payload=redacted_payload,
    )


def build_rescue_stick_telemetry_client_preview(
    report: dict[str, Any],
    *,
    run_id: str,
    opt_in_state: TelemetryOptInState = TelemetryOptInState.DISABLED,
    local_preview_ok: bool = True,
) -> dict[str, Any]:
    """
    Public-safe preview for rescue-stick UI (no send, no server URL).

    Returns envelope dict plus validation_errors list.
    """
    envelope = build_rescue_stick_client_envelope(
        report,
        run_id=run_id,
        opt_in_state=opt_in_state,
        local_preview_ok=local_preview_ok,
    )
    errors = validate_client_envelope(envelope)
    return {
        "status": "ok" if not errors else "blocked",
        "validation_errors": errors,
        "client_envelope": envelope.to_public_dict(),
        "rescue_payload_kind": envelope.payload.get("payload_kind"),
        "send_allowed": not errors and opt_in_state == TelemetryOptInState.ENABLED,
    }
