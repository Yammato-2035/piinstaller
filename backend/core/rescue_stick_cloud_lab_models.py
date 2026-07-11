"""PI-RS-TEL-SEND-001 — Rescue Stick cloud lab send models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

DEFAULT_CLOUD_INGEST_URL = "https://telemetrie.setuphelfer.de/v1/telemetry/ingest"
LAB_PAYLOAD_SCHEMA_VERSION = "rs.telemetry.lab.v1"
LAB_EVENT_TYPE = "rescue_stick.health_probe"
LAB_SOURCE = "rescue_stick"
LAB_CLIENT_ID = "rescue_stick_lab"
CONSENT_STATUS_GRANTED_LAB = "granted_lab"
OPERATOR_APPROVAL_EXPLICIT = "explicit"


class RescueStickLabSendStatus(str, Enum):
    BLOCKED_HEALTH_NOT_OK = "blocked_health_not_ok"
    BLOCKED_MISSING_CONSENT = "blocked_missing_consent"
    BLOCKED_MISSING_OPERATOR_APPROVAL = "blocked_missing_operator_approval"
    BLOCKED_LAB_SEND_DISABLED = "blocked_lab_send_disabled"
    BLOCKED_MISSING_AUTH = "blocked_missing_auth"
    DRY_RUN_READY = "dry_run_ready"
    LAB_SEND_READY = "lab_send_ready"
    LAB_SEND_ACCEPTED = "lab_send_accepted"
    LAB_SEND_REJECTED = "lab_send_rejected"
    LAB_SEND_FAILED = "lab_send_failed"


@dataclass(frozen=True)
class RescueStickLabSendConfig:
    lab_send_enabled: bool = False
    operator_approval: str = ""
    consent_status: str = ""
    ingest_url: str = DEFAULT_CLOUD_INGEST_URL
    token_file: str = ""
    stick_version: str = "1.9.19.5"
    boot_mode: str = "lab"
    timeout_seconds: int = 15


@dataclass(frozen=True)
class RescueStickLabSendResult:
    production_ready: bool = False
    preview_only: bool = True
    lab_only: bool = True
    send_status: RescueStickLabSendStatus = RescueStickLabSendStatus.BLOCKED_LAB_SEND_DISABLED
    health_prerequisite: str = ""
    consent_status: str = ""
    operator_approval: str = ""
    auth_present: bool = False
    lab_send_enabled: bool = False
    real_send_executed: bool = False
    contains_pii: bool = False
    raw_secret_visible: bool = False
    raw_logs_visible: bool = False
    endpoint: str = DEFAULT_CLOUD_INGEST_URL
    payload_preview_redacted: dict[str, Any] = field(default_factory=dict)
    payload_hash: str = ""
    request_id: str = ""
    response_status_code: int | None = None
    response_classification: str = ""
    source: str = LAB_SOURCE
    client_id: str = LAB_CLIENT_ID

    def to_dict(self) -> dict[str, Any]:
        return {
            "production_ready": self.production_ready,
            "preview_only": self.preview_only,
            "lab_only": self.lab_only,
            "send_status": self.send_status.value,
            "health_prerequisite": self.health_prerequisite,
            "consent_status": self.consent_status,
            "operator_approval": self.operator_approval,
            "auth_present": self.auth_present,
            "lab_send_enabled": self.lab_send_enabled,
            "real_send_executed": self.real_send_executed,
            "contains_pii": self.contains_pii,
            "raw_secret_visible": self.raw_secret_visible,
            "raw_logs_visible": self.raw_logs_visible,
            "endpoint": self.endpoint,
            "payload_preview_redacted": self.payload_preview_redacted,
            "payload_hash": self.payload_hash,
            "request_id": self.request_id,
            "response_status_code": self.response_status_code,
            "response_classification": self.response_classification,
            "source": self.source,
            "client_id": self.client_id,
        }
