"""
PI-RS-TEL-002 — offline queue preview only (no worker, no replay, no timer).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_lab_telemetry_model import (
    RESCUE_LAB_CLIENT_ID_DEFAULT,
    RESCUE_LAB_ENVIRONMENT,
    RESCUE_LAB_PAYLOAD_KIND,
    RESCUE_LAB_PRODUCT,
    RESCUE_LAB_SOURCE,
    validate_rescue_lab_payload_no_pii,
)
from core.rescue_lab_telemetry_reachability import redact_lab_url

PREVIEW_ROOT = Path(__file__).resolve().parents[2] / "docs/evidence/runtime-results/rescue-lab-telemetry/offline-queue-preview"
ITEMS_DIR = PREVIEW_ROOT / "queue_preview_items"
LATEST_FILE = PREVIEW_ROOT / "queue_preview_latest.redacted.json"

VALID_REASONS = frozenset(
    {
        "offline",
        "telemetry_unreachable",
        "missing_secret",
        "missing_config",
        "profile_disabled",
        "dry_run",
    }
)


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "product",
        "source",
        "environment",
        "payload_kind",
        "created_for",
        "rescue_preview",
        "safety",
    }
    redacted = {k: payload[k] for k in allowed if k in payload}
    redacted["redaction"] = "preview_only_no_host_data"
    return redacted


def build_offline_queue_preview_item(
    payload: dict[str, Any],
    reason: str,
    reachability_summary: dict[str, Any] | None,
    *,
    would_send_to: str | None = None,
) -> dict[str, Any]:
    ok, violations = validate_rescue_lab_payload_no_pii(payload)
    if not ok:
        raise ValueError(f"queue_preview_pii_violation:{','.join(violations)}")
    if reason not in VALID_REASONS:
        reason = "offline"
    reach = reachability_summary or {}
    return {
        "queue_preview_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reason": reason,
        "would_send_to": redact_lab_url(would_send_to),
        "client_id": RESCUE_LAB_CLIENT_ID_DEFAULT,
        "product": RESCUE_LAB_PRODUCT,
        "source": RESCUE_LAB_SOURCE,
        "environment": RESCUE_LAB_ENVIRONMENT,
        "payload_kind": RESCUE_LAB_PAYLOAD_KIND,
        "payload_redacted": _redact_payload(payload),
        "network_state": reach.get("network_state"),
        "telemetry_reachability": reach.get("telemetry_reachability"),
        "send_allowed_now": False,
        "auto_replay_enabled": False,
        "production_ready": False,
        "warnings": list(reach.get("warnings") or []),
        "errors": list(reach.get("errors") or []),
    }


def validate_offline_queue_preview_item_no_pii(item: dict[str, Any]) -> tuple[bool, list[str]]:
    violations: list[str] = []
    if item.get("auto_replay_enabled") is not False:
        violations.append("auto_replay_must_be_false")
    if item.get("send_allowed_now") is not False:
        violations.append("send_allowed_now_must_be_false")
    if item.get("production_ready") is not False:
        violations.append("production_ready_must_be_false")
    payload = item.get("payload_redacted") or {}
    ok, pii_v = validate_rescue_lab_payload_no_pii(payload if isinstance(payload, dict) else {})
    if not ok:
        violations.extend(pii_v)
    blob = json.dumps(item, ensure_ascii=False).lower()
    private_key_marker = "BEGIN PRIVATE" + " KEY"
    for token in ("password", "token", private_key_marker):
        if token.lower() in blob:
            if token == "token" and "client_id" in blob:
                continue
            violations.append(f"forbidden_token:{token}")
    if "secret" in blob and "contains_secrets" not in blob and "secret_configured" not in blob:
        violations.append("forbidden_token:secret")
    return (len(violations) == 0, violations)


def write_offline_queue_preview_item(item: dict[str, Any], *, repo_root: Path | None = None) -> Path:
    ok, violations = validate_offline_queue_preview_item_no_pii(item)
    if not ok:
        raise ValueError(f"queue_preview_pii_violation:{','.join(violations)}")
    root = repo_root or Path(__file__).resolve().parents[2]
    out_root = root / "docs/evidence/runtime-results/rescue-lab-telemetry/offline-queue-preview"
    items_dir = out_root / "queue_preview_items"
    items_dir.mkdir(parents=True, exist_ok=True)
    latest = out_root / "queue_preview_latest.redacted.json"
    item_path = items_dir / f"{item['queue_preview_id']}.redacted.json"
    text = json.dumps(item, indent=2, ensure_ascii=False) + "\n"
    item_path.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    return item_path


def list_offline_queue_preview_items(limit: int = 20, *, repo_root: Path | None = None) -> list[dict[str, Any]]:
    root = repo_root or Path(__file__).resolve().parents[2]
    items_dir = root / "docs/evidence/runtime-results/rescue-lab-telemetry/offline-queue-preview/queue_preview_items"
    if not items_dir.is_dir():
        return []
    files = sorted(items_dir.glob("*.redacted.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[dict[str, Any]] = []
    for path in files[: max(1, limit)]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                out.append(data)
        except (OSError, json.JSONDecodeError):
            continue
    return out


def build_offline_queue_preview_summary(*, repo_root: Path | None = None) -> dict[str, Any]:
    items = list_offline_queue_preview_items(limit=20, repo_root=repo_root)
    latest = items[0] if items else None
    return {
        "count": len(items),
        "latest_reason": (latest or {}).get("reason"),
        "latest_queue_preview_id": (latest or {}).get("queue_preview_id"),
        "auto_replay_enabled": False,
        "production_ready": False,
        "worker_enabled": False,
    }
