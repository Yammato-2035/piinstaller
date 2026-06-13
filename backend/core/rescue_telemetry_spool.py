"""
Rescue telemetry spool — persist failed/pending ingest on stick (Phase R.3).

No secrets, passwords, or full tokens stored.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_persistence import Runner, build_rescue_evidence_root, ensure_rescue_evidence_tree

RESCUE_TELEMETRY_SPOOL_VERSION = 3

_SECRET_KEYS = frozenset(
    {
        "password",
        "passwd",
        "psk",
        "wifi_psk",
        "sudo_password",
        "token",
        "api_key",
        "secret",
        "authorization",
    }
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _spool_dir(*, runner: Runner = None) -> Path:
    meta = ensure_rescue_evidence_tree(runner=runner)
    return Path(meta["evidence_root"]) / "telemetry" / "spool"


def _redact_value(key: str, value: Any) -> Any:
    k = (key or "").lower()
    if k in _SECRET_KEYS or "password" in k or "psk" in k or "token" in k:
        if isinstance(value, str) and value:
            if len(value) <= 4:
                return "***"
            return value[:2] + "***" + value[-1:]
        return "***"
    if isinstance(value, dict):
        return _redact_payload(value)
    if isinstance(value, list):
        return [_redact_value("", item) if isinstance(item, dict) else item for item in value]
    return value


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, val in payload.items():
        out[key] = _redact_value(str(key), val)
    return out


def write_telemetry_event(
    event: dict[str, Any],
    *,
    runner: Runner = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    """Write one telemetry event JSON to spool (redacted)."""
    spool = _spool_dir(runner=runner)
    spool.mkdir(parents=True, exist_ok=True)
    eid = (event_id or "").strip() or uuid.uuid4().hex
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", eid)[:80]
    path = spool / f"{safe_id}.json"
    body = {
        "schema_version": 1,
        "event_id": eid,
        "spooled_at": _utc_now(),
        "sent": False,
        "send_attempts": 0,
        "last_error": None,
        "event": _redact_payload(event if isinstance(event, dict) else {"payload": event}),
    }
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    persist = build_rescue_evidence_root(runner=runner)
    return {
        "status": "ok",
        "path": str(path),
        "event_id": eid,
        "fallback": persist.get("fallback"),
        "warning": persist.get("warning"),
    }


def list_pending_telemetry_events(*, runner: Runner = None) -> list[dict[str, Any]]:
    spool = _spool_dir(runner=runner)
    if not spool.is_dir():
        return []
    pending: list[dict[str, Any]] = []
    for path in sorted(spool.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            if data.get("sent") is True:
                continue
            pending.append(
                {
                    "event_id": data.get("event_id"),
                    "path": str(path),
                    "spooled_at": data.get("spooled_at"),
                    "send_attempts": data.get("send_attempts", 0),
                    "last_error": data.get("last_error"),
                }
            )
        except (OSError, json.JSONDecodeError):
            continue
    return pending


def mark_telemetry_event_sent(event_id: str, *, runner: Runner = None, http_status: int | None = None) -> dict[str, Any]:
    spool = _spool_dir(runner=runner)
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", (event_id or "").strip())[:80]
    path = spool / f"{safe_id}.json"
    if not path.is_file():
        return {"status": "error", "message": "event not found", "event_id": event_id}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"status": "error", "message": "invalid spool file"}
        data["sent"] = True
        data["sent_at"] = _utc_now()
        data["http_status"] = http_status
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return {"status": "ok", "event_id": event_id, "path": str(path)}
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "error", "message": str(exc), "event_id": event_id}


def record_telemetry_send_failure(
    event_id: str,
    error: str,
    *,
    runner: Runner = None,
) -> dict[str, Any]:
    spool = _spool_dir(runner=runner)
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", (event_id or "").strip())[:80]
    path = spool / f"{safe_id}.json"
    if not path.is_file():
        return {"status": "error", "message": "event not found"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"status": "error", "message": "invalid spool file"}
        data["send_attempts"] = int(data.get("send_attempts") or 0) + 1
        data["last_error"] = (error or "")[:500]
        data["last_attempt_at"] = _utc_now()
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return {"status": "ok", "event_id": event_id, "send_attempts": data["send_attempts"]}
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "error", "message": str(exc)}


def build_telemetry_spool_summary(*, runner: Runner = None) -> dict[str, Any]:
    pending = list_pending_telemetry_events(runner=runner)
    spool = _spool_dir(runner=runner)
    sent_count = 0
    if spool.is_dir():
        for path in spool.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data.get("sent") is True:
                    sent_count += 1
            except (OSError, json.JSONDecodeError):
                continue
    persist = build_rescue_evidence_root(runner=runner)
    return {
        "generated_at": _utc_now(),
        "spool_dir": str(spool),
        "pending_count": len(pending),
        "sent_count": sent_count,
        "pending": pending[:50],
        "fallback": persist.get("fallback"),
        "warning": persist.get("warning"),
    }


def build_rescue_telemetry_spool_diagnostics() -> dict[str, Any]:
    return {
        "spool_version": RESCUE_TELEMETRY_SPOOL_VERSION,
        "module": "core.rescue_telemetry_spool",
        "public_functions": [
            "write_telemetry_event",
            "list_pending_telemetry_events",
            "mark_telemetry_event_sent",
            "record_telemetry_send_failure",
            "build_telemetry_spool_summary",
            "build_rescue_telemetry_spool_diagnostics",
        ],
        "stores_secrets": False,
        "redacts_tokens": True,
    }
