"""
Public-safe telemetry client contract — opt-in, redaction-before-send, no server internals.

Server implementation remains private-only. Endpoints use example domains only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

CONTRACT_VERSION = 1

# Example domain only — never a real internal endpoint
EXAMPLE_TELEMETRY_ENDPOINT = "https://telemetry.internal.setuphelfer.example/v1/report"


class TelemetryOptInState(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    PENDING_CONSENT = "pending_consent"


class TelemetryDataCategory(str, Enum):
    """Categories that may be described in client consent UI."""

    VERSION = "version"
    RUNTIME_HEALTH = "runtime_health"
    ERROR_SUMMARY = "error_summary"
    HARDWARE_CLASS = "hardware_class"
    RESCUE_SESSION_META = "rescue_session_meta"


@dataclass(frozen=True)
class TelemetryClientEnvelope:
    """Shape for optional client-side telemetry report (after redaction)."""

    schema_version: int
    opt_in_state: TelemetryOptInState
    data_categories: tuple[TelemetryDataCategory, ...]
    redaction_applied: bool
    local_preview_ok: bool
    payload: dict[str, Any] = field(default_factory=dict)
    contract_version: int = CONTRACT_VERSION

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "opt_in_state": self.opt_in_state.value,
            "data_categories": [c.value for c in self.data_categories],
            "redaction_applied": self.redaction_applied,
            "local_preview_ok": self.local_preview_ok,
            "payload": self.payload,
            "contract_version": self.contract_version,
            # No server URL in serialized client preview
            "endpoint_configured": False,
        }


def validate_client_envelope(envelope: TelemetryClientEnvelope) -> list[str]:
    """Local validation before any send attempt."""
    errors: list[str] = []
    if envelope.opt_in_state != TelemetryOptInState.ENABLED:
        errors.append("opt_in_required")
    if not envelope.redaction_applied:
        errors.append("redaction_required")
    if not envelope.local_preview_ok:
        errors.append("local_preview_failed")
    # Never allow real internal domains in public contract tests
    for _k, v in envelope.payload.items():
        if isinstance(v, str) and ".setuphelfer." in v and ".example" not in v:
            errors.append("internal_domain_in_payload")
    return errors
