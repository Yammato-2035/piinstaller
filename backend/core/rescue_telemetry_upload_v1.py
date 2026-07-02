"""
Rescue telemetry upload orchestration V1 — dry-run, mock, and lab modes only.
No production beta server URL with secrets in repo.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from core.rescue_telemetry_client_contract_v2 import (
    TelemetryUploadMode,
    upload_allowed_for_mode,
    validate_telemetry_payload_v2,
)
from core.rescue_telemetry_signing_v1 import sign_payload_hmac

MOCK_TELEMETRY_URL = "http://127.0.0.1:8101/v1/telemetry/rescue/dry-run"
MOCK_INGEST_URL = "http://127.0.0.1:8101/v1/telemetry/rescue/ingest"


def _post_json(url: str, body: dict[str, Any], *, timeout: int = 8) -> dict[str, Any]:
  data = json.dumps(body).encode("utf-8")
  req = urllib.request.Request(
    url,
    data=data,
    method="POST",
    headers={"Content-Type": "application/json", "User-Agent": "Setuphelfer-Rescue-Upload/1"},
  )
  try:
    with urllib.request.urlopen(req, timeout=timeout) as resp:
      return {"http_status": resp.status, "body": json.loads(resp.read().decode("utf-8"))}
  except urllib.error.HTTPError as exc:
    raw = exc.read().decode("utf-8", errors="replace")
    try:
      parsed = json.loads(raw)
    except json.JSONDecodeError:
      parsed = {"raw": raw[:300]}
    return {"http_status": exc.code, "body": parsed, "error": "http_error"}
  except (urllib.error.URLError, TimeoutError) as exc:
    return {"http_status": 0, "body": {}, "error": type(exc).__name__}


def upload_telemetry_payload_v1(
  payload: dict[str, Any],
  *,
  mode: str = TelemetryUploadMode.DRY_RUN_LOCAL.value,
  stick_verified: bool = False,
  agreement_valid: bool = False,
  signing_secret: str | None = None,
) -> dict[str, Any]:
  errors = validate_telemetry_payload_v2(payload)
  if errors:
    return {"status": "rejected_schema", "errors": errors, "uploaded": False}

  try:
    upload_mode = TelemetryUploadMode(mode)
  except ValueError:
    return {"status": "rejected", "reason": "unknown_mode", "uploaded": False}

  allowed, reason = upload_allowed_for_mode(
    upload_mode,
    stick_verified=stick_verified,
    agreement_valid=agreement_valid,
  )
  if not allowed:
    return {"status": "blocked", "reason": reason, "uploaded": False}

  envelope = dict(payload)
  if signing_secret:
    envelope["_signature"] = sign_payload_hmac(payload, secret=signing_secret)

  if upload_mode == TelemetryUploadMode.DRY_RUN_LOCAL:
    return {
      "status": "dry_run_ok",
      "uploaded": False,
      "validated": True,
      "mode": mode,
      "event_id": payload.get("event_id"),
    }

  if upload_mode == TelemetryUploadMode.MOCK_SERVER:
    url = MOCK_TELEMETRY_URL if upload_mode == TelemetryUploadMode.MOCK_SERVER else MOCK_INGEST_URL
    result = _post_json(url, envelope)
    body = result.get("body") or {}
    return {
      "status": body.get("status", "mock_response"),
      "uploaded": result.get("http_status") == 200,
      "http_status": result.get("http_status"),
      "mode": mode,
      "event_id": payload.get("event_id"),
      "server_body": body,
      "error": result.get("error"),
    }

  return {"status": "not_implemented_public_repo", "uploaded": False, "mode": mode}
