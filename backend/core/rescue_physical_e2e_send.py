"""HTTPS send and offline queue for physical E2E telemetry."""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from core.rescue_physical_e2e_journal import append_event_journal, store_receipt, update_send_status
from core.rescue_physical_e2e_models import DEFAULT_INGEST_URL
from core.rescue_physical_e2e_telemetry_payload import canonical_payload_bytes
from core.rescue_stick_cloud_lab_send import redact_secret_material

HttpTransportFn = Callable[[str, bytes, dict[str, str], int], tuple[int, str, dict[str, str]]]

MAX_RETRIES = 8
DEFAULT_TIMEOUT_SECONDS = 30


def _read_bearer_token(token_file: str) -> str:
    path = Path(token_file).expanduser()
    return path.read_text(encoding="utf-8").strip()


def _token_present(token_file: str) -> bool:
    if not token_file:
        return False
    path = Path(token_file).expanduser()
    return path.is_file() and path.stat().st_size > 0


def _default_http_transport(
    url: str, body: bytes, headers: dict[str, str], timeout_seconds: int
) -> tuple[int, str, dict[str, str]]:
    context = ssl.create_default_context()
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds, context=context) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            return response.status, response_body, dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        return exc.code, body_text, dict(exc.headers.items()) if exc.headers else {}
    except urllib.error.URLError as exc:
        return 0, str(exc.reason), {}


def build_auth_headers(*, token_file: str, raw_body: bytes) -> dict[str, str]:
    if not _token_present(token_file):
        raise ValueError("missing_lab_token")
    token = _read_bearer_token(token_file)
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


def send_telemetry_event(
    *,
    payload: dict[str, Any],
    e2e_run_id: str,
    journal_dir: Path,
    ingest_url: str | None = None,
    token_file: str | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    http_transport: HttpTransportFn | None = None,
) -> dict[str, Any]:
    transport = http_transport or _default_http_transport
    url = (ingest_url or os.getenv("SETUPHELFER_RS_TELEMETRY_ENDPOINT", DEFAULT_INGEST_URL)).strip()
    token_path = (
        token_file
        or os.getenv("SETUPHELFER_RS_TELEMETRY_LAB_TOKEN_FILE", "").strip()
        or os.getenv("SETUPHELFER_RS_LAB_TOKEN_FILE", "~/.config/setuphelfer/rescue/telemetry-lab-token")
    )
    event_id = str(payload.get("event_id") or "")
    raw = canonical_payload_bytes(payload)

    record_base = {
        "event_id": event_id,
        "operation_event": (payload.get("system_assessment") or {}).get("operation_event"),
        "e2e_run_id": e2e_run_id,
        "state": "sending",
    }
    append_event_journal(journal_dir, record_base)
    update_send_status(journal_dir, {"last_event_id": event_id, "send_status": "sending"})

    try:
        headers = build_auth_headers(token_file=token_path, raw_body=raw)
    except ValueError as exc:
        result = {
            "accepted": False,
            "send_status": "blocked_missing_auth",
            "error": str(exc),
            "event_id": event_id,
        }
        append_event_journal(journal_dir, {**record_base, "state": "send_failed", "error": str(exc)})
        update_send_status(journal_dir, {"send_status": "blocked_missing_auth"})
        return result

    headers["X-E2E-Run-Id"] = e2e_run_id
    headers["X-Request-Id"] = event_id

    last_status = 0
    last_body = ""
    last_headers: dict[str, str] = {}
    for attempt in range(MAX_RETRIES):
        last_status, last_body, last_headers = transport(url, raw, headers, timeout_seconds)
        if last_status in {200, 202}:
            break
        if last_status == 0:
            update_send_status(journal_dir, {"send_status": "queued_offline", "retry_attempt": attempt + 1})
            if attempt + 1 >= MAX_RETRIES:
                append_event_journal(
                    journal_dir,
                    {**record_base, "state": "queued_offline", "attempts": attempt + 1},
                )
                return {
                    "accepted": False,
                    "send_status": "queued_offline",
                    "event_id": event_id,
                    "queued": True,
                }

    try:
        parsed = json.loads(last_body) if last_body else {}
    except json.JSONDecodeError:
        parsed = {"raw_error": redact_secret_material(last_body[:200])}

    accepted = last_status == 200 and bool(parsed.get("accepted"))
    receipt = {
        "event_id": event_id,
        "receipt_id": parsed.get("receipt_id") or parsed.get("ingest_id"),
        "accepted": accepted,
        "diagnostics_forwarding_status": parsed.get("forward_outbox_status")
        or ("forwarded" if parsed.get("diagnostics_forwarded") else "pending"),
        "received_at": parsed.get("received_at"),
        "http_status": last_status,
        "e2e_run_id": parsed.get("e2e_run_id") or e2e_run_id,
    }

    if accepted:
        store_receipt(journal_dir, receipt)
        append_event_journal(journal_dir, {**record_base, "state": "receipt_stored", "receipt_id": receipt["receipt_id"]})
        update_send_status(journal_dir, {"send_status": "accepted", "last_receipt_id": receipt["receipt_id"]})
        return {**receipt, "send_status": "accepted"}

    append_event_journal(
        journal_dir,
        {
            **record_base,
            "state": "send_failed",
            "http_status": last_status,
            "error": redact_secret_material(str(parsed)),
        },
    )
    update_send_status(journal_dir, {"send_status": "send_failed", "http_status": last_status})
    return {**receipt, "send_status": "send_failed", "accepted": False}
