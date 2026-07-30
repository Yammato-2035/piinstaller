"""
Rescue assessment telemetry V1 — feeds the real (redacted) hardware assessment
into the existing telemetry.rescue.beta.v2 pipeline as early as consent allows.

Unlike rescue_telemetry_payload_v2.build_rescue_telemetry_preview_payload_v2()
(a hashed pipe-test payload with no real hardware data), this module carries the
actual redact_assessment_payload()-cleaned build_master_assessment_bundle_v1()
output. Best-effort only: a failure here must never break the assessment
request that triggered it.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from core.rescue_master_assessment_bundle_v1 import build_master_assessment_bundle_v1
from core.rescue_session_evidence import load_current_session_meta
from core.rescue_telemetry_client_contract_v2 import (
  build_telemetry_payload_v2,
  validate_telemetry_payload_v2,
)
from core.rescue_telemetry_opt_in_state import is_telemetry_opt_in_enabled
from core.rescue_telemetry_payload_v2 import (
  PHYSICAL_STICK_PAYLOAD_SHA256_DEFAULT,
  PHYSICAL_STICK_PAYLOAD_VERSION_DEFAULT,
)
from core.rescue_telemetry_queue_v1 import TelemetryQueueV1

ASSESSMENT_EVENT_KIND = "rescue_assessment_telemetry.v1"
_DEFAULT_QUEUE_ROOT = Path("/run/setuphelfer-rescue/telemetry-queue")


def _hash_token(value: str, *, salt: str) -> str:
  return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()[:32]


def build_assessment_telemetry_payload(*, rescue_version: str | None = None) -> dict[str, Any]:
  """Wrap the real, already-redacted assessment bundle in the beta.v2 envelope."""
  bundle = build_master_assessment_bundle_v1()
  meta = load_current_session_meta() or {}
  boot_token = str(meta.get("boot_id") or "unknown-boot")
  version = rescue_version or bundle.get("rescue_version") or PHYSICAL_STICK_PAYLOAD_VERSION_DEFAULT
  system_assessment = dict(bundle)
  system_assessment["event_kind"] = ASSESSMENT_EVENT_KIND
  return build_telemetry_payload_v2(
    rescue_version=str(version),
    build_id=PHYSICAL_STICK_PAYLOAD_SHA256_DEFAULT[:16],
    boot_session_id=_hash_token(boot_token, salt="boot-session"),
    stick_id=_hash_token(PHYSICAL_STICK_PAYLOAD_SHA256_DEFAULT, salt="stick"),
    stick_type="mock",
    device_public_key_id="preview-not-provisioned",
    attestation_mode="mock",
    system_assessment=system_assessment,
  )


def maybe_send_assessment_telemetry_early(
  *, queue_root: Path | None = None, opt_in_path: Path | None = None
) -> dict[str, Any]:
  """
  If the operator has opted in, queue the real assessment for telemetry send as
  soon as it exists — instead of requiring a separate manual "send" step later.
  Reuses the existing offline-first queue (redaction + forbidden-field checks +
  signing happen inside TelemetryQueueV1.enqueue); a background drain/upload
  worker is responsible for actually delivering queued items when reachable.
  """
  if not is_telemetry_opt_in_enabled(opt_in_path):
    return {"attempted": False, "reason": "opt_in_disabled"}
  try:
    payload = build_assessment_telemetry_payload()
  except Exception as exc:  # best-effort: never break the assessment call itself
    return {"attempted": False, "reason": "payload_build_failed", "error": repr(exc)}
  errors = validate_telemetry_payload_v2(payload)
  if errors:
    return {"attempted": False, "reason": "validation_failed", "errors": errors}
  queue = TelemetryQueueV1(queue_root or _DEFAULT_QUEUE_ROOT)
  result = queue.enqueue(payload)
  return {"attempted": True, **result}
