"""
PI-RS-TEL-004 — Operator auth/HMAC gate for cloud telemetry (no secrets in repo).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.rescue_telemetry_signing_v1 import sign_payload_hmac

ENV_BASE_URL = "SETUPHELFER_RESCUE_TELEMETRY_BASE_URL"
ENV_SERVER = "SETUPHELFER_RESCUE_TELEMETRY_SERVER"
ENV_PATH_STYLE = "SETUPHELFER_RESCUE_TELEMETRY_PATH_STYLE"
ENV_AUTH_MODE = "SETUPHELFER_RESCUE_TELEMETRY_AUTH_MODE"
ENV_KEY_ID = "SETUPHELFER_RESCUE_TELEMETRY_KEY_ID"
ENV_SECRET_FILE = "SETUPHELFER_RESCUE_TELEMETRY_SECRET_FILE"
ENV_OPERATOR_CONSENT = "SETUPHELFER_RESCUE_TELEMETRY_OPERATOR_CONSENT"
ENV_CLOUD_SEND_ENABLED = "SETUPHELFER_RESCUE_TELEMETRY_CLOUD_SEND_ENABLED"


@dataclass(frozen=True)
class RescueTelemetryAuthConfig:
    auth_mode: str | None
    key_id: str | None
    secret_configured: bool
    operator_consent: str | None
    cloud_send_enabled: bool


def _read_secret_file(path: str) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    try:
        value = p.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def load_rescue_telemetry_auth_config(
    environ: dict[str, str] | None = None,
) -> RescueTelemetryAuthConfig:
    env = environ if environ is not None else os.environ
    secret_file = (env.get(ENV_SECRET_FILE) or "").strip()
    secret_present = bool(_read_secret_file(secret_file)) if secret_file else False
    return RescueTelemetryAuthConfig(
        auth_mode=(env.get(ENV_AUTH_MODE) or "").strip() or None,
        key_id=(env.get(ENV_KEY_ID) or "").strip() or None,
        secret_configured=secret_present,
        operator_consent=(env.get(ENV_OPERATOR_CONSENT) or "").strip() or None,
        cloud_send_enabled=(env.get(ENV_CLOUD_SEND_ENABLED) or "").strip().lower() in {"1", "true", "yes"},
    )


def evaluate_cloud_send_gate(
    *,
    auth: RescueTelemetryAuthConfig | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = auth or load_rescue_telemetry_auth_config()
    reasons: list[str] = []
    if payload is not None and payload.get("preview_only") is not True:
        reasons.append("preview_only_required")
    if payload is not None and payload.get("production_ready") is True:
        reasons.append("production_ready_forbidden")
    if not cfg.cloud_send_enabled:
        reasons.append("cloud_send_disabled")
    if cfg.operator_consent != "explicit":
        reasons.append("operator_consent_missing")
    if not cfg.auth_mode:
        reasons.append("auth_mode_missing")
    elif cfg.auth_mode not in {"hmac", "api_key"}:
        reasons.append("auth_mode_unsupported")
    if cfg.auth_mode == "hmac":
        if not cfg.key_id:
            reasons.append("key_id_missing")
        if not cfg.secret_configured:
            reasons.append("secret_missing")
    allowed = not reasons
    return {
        "allowed": allowed,
        "preview_only": True,
        "production_ready": False,
        "operator_approval_required": True,
        "cloud_send_requires_operator_consent": True,
        "reasons": reasons,
    }


def build_hmac_signature_preview(
    payload: dict[str, Any],
    *,
    secret: str,
    key_id: str = "test-preview-key",
) -> dict[str, Any]:
    return sign_payload_hmac(payload, secret=secret, key_id=key_id)
