"""
Rescue telemetry payload redaction V2 — pre-sign redaction for telemetry.rescue.beta.v2.
"""

from __future__ import annotations

from typing import Any

from core.rescue_assessment_redaction import redact_assessment_payload, scan_forbidden_fields
from core.telemetry_redaction_contract import redact_telemetry_payload

REDACTION_VERSION = "telemetry.payload.redaction.v2"


def redact_telemetry_payload_v2(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
  base = redact_telemetry_payload(dict(payload))
  assessment = base.get("system_assessment")
  if isinstance(assessment, dict):
    redacted_assessment, report = redact_assessment_payload(assessment)
    base["system_assessment"] = redacted_assessment
  else:
    report = {"redaction_version": REDACTION_VERSION}
  forbidden = scan_forbidden_fields(base)
  privacy = dict(base.get("privacy") or {})
  privacy.update(
    {
      "redaction_version": REDACTION_VERSION,
      "contains_mac": "contains_mac" in forbidden,
      "contains_ip": "contains_ip" in forbidden,
      "contains_email": "contains_email" in forbidden,
      "contains_serial_plaintext": "contains_serial_plaintext" in forbidden,
      "contains_file_list": "contains_file_list" in forbidden,
      "contains_user_files": False,
      "contains_secrets": False,
    }
  )
  base["privacy"] = privacy
  return base, {"forbidden_fields": forbidden, "assessment_report": report}
