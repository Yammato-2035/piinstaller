"""
Rescue telemetry upload queue V1 — offline-first, size-limited, no PII.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_assessment_redaction import scan_forbidden_fields
from core.rescue_telemetry_payload_redaction_v2 import redact_telemetry_payload_v2
from core.rescue_telemetry_signing_v1 import sign_payload_hmac

QUEUE_VERSION = 1
MAX_QUEUE_ITEMS = 50
MAX_QUEUE_BYTES = 2 * 1024 * 1024
BACKOFF_SECONDS = (5, 15, 60, 300)


def _utc_now() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


_BLOCKED_KEYS = frozenset({"email", "phone", "password", "api_key", "secret", "mac", "ip"})


def _blocked_keys_present(payload: dict[str, Any]) -> list[str]:
  found: list[str] = []

  def walk(obj: Any, key: str = "") -> None:
    if key.lower() in _BLOCKED_KEYS:
      found.append(key)
    if isinstance(obj, dict):
      for k, v in obj.items():
        walk(v, str(k))
    elif isinstance(obj, list):
      for item in obj:
        walk(item, key)

  walk(payload)
  return found


class TelemetryQueueV1:
  def __init__(self, root: Path) -> None:
    self.root = root
    self.root.mkdir(parents=True, exist_ok=True)

  def _queue_path(self) -> Path:
    return self.root / "telemetry-queue-v1.jsonl"

  def _queue_size(self) -> int:
    path = self._queue_path()
    return path.stat().st_size if path.is_file() else 0

  def enqueue(self, payload: dict[str, Any], *, signing_secret: str | None = None) -> dict[str, Any]:
    blocked = _blocked_keys_present(payload)
    if blocked:
      return {"status": "rejected", "reason": "privacy_forbidden", "fields": blocked}
    redacted, report = redact_telemetry_payload_v2(payload)
    forbidden = list(report.get("forbidden_fields") or []) + scan_forbidden_fields(redacted)
    forbidden = sorted(set(forbidden))
    privacy = redacted.get("privacy") if isinstance(redacted.get("privacy"), dict) else {}
    if privacy.get("contains_email") or privacy.get("contains_ip") or privacy.get("contains_mac"):
      forbidden.extend(
        k for k, v in (
          ("contains_email", privacy.get("contains_email")),
          ("contains_ip", privacy.get("contains_ip")),
          ("contains_mac", privacy.get("contains_mac")),
        ) if v
      )
    if forbidden:
      return {"status": "rejected", "reason": "privacy_forbidden", "fields": forbidden}
    entry: dict[str, Any] = {
      "queued_at": _utc_now(),
      "payload": redacted,
      "attempts": 0,
    }
    if signing_secret:
      entry["signature"] = sign_payload_hmac(redacted, secret=signing_secret)
    path = self._queue_path()
    items = self.list_items()
    if len(items) >= MAX_QUEUE_ITEMS:
      return {"status": "rejected", "reason": "queue_full"}
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    if self._queue_size() + len(line.encode()) > MAX_QUEUE_BYTES:
      return {"status": "rejected", "reason": "queue_size_limit"}
    with path.open("a", encoding="utf-8") as fh:
      fh.write(line)
    return {"status": "queued", "queued_at": entry["queued_at"]}

  def list_items(self) -> list[dict[str, Any]]:
    path = self._queue_path()
    if not path.is_file():
      return []
    items: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
      if line.strip():
        try:
          items.append(json.loads(line))
        except json.JSONDecodeError:
          continue
    return items

  def next_backoff_seconds(self, attempts: int) -> int:
    idx = min(attempts, len(BACKOFF_SECONDS) - 1)
    return BACKOFF_SECONDS[idx]

  def mark_attempt(self, index: int) -> None:
    items = self.list_items()
    if 0 <= index < len(items):
      items[index]["attempts"] = int(items[index].get("attempts") or 0) + 1
      items[index]["last_attempt_at"] = _utc_now()
      path = self._queue_path()
      with path.open("w", encoding="utf-8") as fh:
        for item in items:
          fh.write(json.dumps(item, ensure_ascii=False) + "\n")

  def drain_sent(self, count: int = 1) -> list[dict[str, Any]]:
    items = self.list_items()
    if not items:
      return []
    sent = items[:count]
    remaining = items[count:]
    path = self._queue_path()
    with path.open("w", encoding="utf-8") as fh:
      for item in remaining:
        fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    return sent
