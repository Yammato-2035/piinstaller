"""PI-RS-TEL-SEND-001 — Rescue Stick cloud lab send configuration from environment."""

from __future__ import annotations

import json
import os
from pathlib import Path

from core.rescue_payload_version import rescue_payload_version
from core.rescue_stick_cloud_lab_models import (
    DEFAULT_CLOUD_INGEST_URL,
    RescueStickLabSendConfig,
)


def _read_stick_version() -> str:
    payload_version = rescue_payload_version()
    if payload_version:
        return payload_version
    version_json = Path(__file__).resolve().parents[2] / "config" / "version.json"
    if version_json.is_file():
        try:
            data = json.loads(version_json.read_text(encoding="utf-8"))
            project_version = str(data.get("project_version", "")).strip()
            if project_version:
                return project_version
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    return os.getenv("SETUPHELFER_RS_TELEMETRY_STICK_VERSION", "unknown").strip() or "unknown"


def rescue_stick_lab_send_config_from_env() -> RescueStickLabSendConfig:
    return RescueStickLabSendConfig(
        lab_send_enabled=os.getenv("SETUPHELFER_RS_TELEMETRY_LAB_SEND_ENABLED", "0").strip() == "1",
        operator_approval=os.getenv("SETUPHELFER_RS_TELEMETRY_OPERATOR_APPROVAL", "").strip(),
        consent_status=os.getenv("SETUPHELFER_RS_TELEMETRY_CONSENT_STATUS", "").strip(),
        ingest_url=os.getenv("SETUPHELFER_RS_TELEMETRY_ENDPOINT", DEFAULT_CLOUD_INGEST_URL).strip()
        or DEFAULT_CLOUD_INGEST_URL,
        token_file=os.getenv("SETUPHELFER_RS_TELEMETRY_LAB_TOKEN_FILE", "").strip(),
        stick_version=_read_stick_version(),
        boot_mode=os.getenv("SETUPHELFER_RS_TELEMETRY_BOOT_MODE", "lab").strip() or "lab",
        timeout_seconds=int(os.getenv("SETUPHELFER_RS_TELEMETRY_TIMEOUT_SECONDS", "15").strip() or "15"),
    )
