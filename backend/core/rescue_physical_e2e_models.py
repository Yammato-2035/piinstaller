"""SETUPHELFER-E2E-LIVE-001D — physical rescue E2E constants and types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

FEATURE_ID = "SETUPHELFER-E2E-LIVE-001D"
PRODUCTION_READY = False

OPERATION_EVENTS: tuple[str, ...] = (
    "rescue_session_started",
    "backup_started",
    "backup_completed",
    "verify_started",
    "verify_completed",
    "restore_started",
    "restore_completed",
    "rescue_session_completed",
)

CONSENT_GRANTED = "granted"
CONSENT_LOCAL_ONLY = "local_only"
CONSENT_ABORTED = "aborted"

TELEMETRY_SCHEMA = "telemetry.rescue.beta.v2"
DEFAULT_INGEST_URL = "https://telemetrie.setuphelfer.de/v1/telemetry/ingest"
DEFAULT_DIAGNOSTICS_CASE_URL_TEMPLATE = (
    "https://telemetrie.setuphelfer.de/api/diagnostics/lab/cases/by-e2e-run/{e2e_run_id}"
)

EventSendState = Literal[
    "locally_recorded",
    "consent_blocked",
    "queued_offline",
    "sending",
    "accepted",
    "receipt_stored",
    "send_failed",
]

ConsentChoice = Literal["granted", "local_only", "aborted"]


@dataclass
class PhysicalE2EPaths:
    e2e_run_id: str
    evidence_root: str
    source_dir: str
    backup_archive: str
    restore_dir: str
    journal_dir: str


@dataclass
class PhysicalE2ESession:
    e2e_run_id: str
    rescue_session_id: str
    backup_job_id: str
    restore_job_id: str
    device_id_hash: str
    payload_version: str
    payload_sha256: str
    consent: ConsentChoice = CONSENT_ABORTED
    operator_approved: bool = False
    paths: PhysicalE2EPaths | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
