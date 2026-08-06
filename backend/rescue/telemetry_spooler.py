"""
Offline-first telemetry spooler for ASUS emergency boot campaigns.

PI-RS-ASUS-EMERGENCY-LINUX-TELEMETRY-003 Phase 9/10.

Persists events locally (SETUP_LOGS / evidence spool) before any network send.
Never marks offline queue as ``sent``.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from rescue.rescue_evidence_spool import sanitize_rescue_log

DEFAULT_SPOOL_FILES = (
    "boot_events.jsonl",
    "hardware_events.jsonl",
    "driver_findings.json",
    "baseline_result.json",
    "kernel_excerpt.jsonl",
    "telemetry_queue.jsonl",
    "telemetry_delivery_state.json",
    "diagnostics_delivery_state.json",
    "run_manifest.json",
    "checksums.json",
)

EVENT_TYPES = (
    "rescue_boot_started",
    "rescue_boot_stage_reached",
    "rescue_boot_stage_failed",
    "hardware_detected",
    "hardware_driver_bound",
    "hardware_driver_missing",
    "hardware_driver_bind_failed",
    "hardware_firmware_missing",
    "hardware_firmware_load_failed",
    "hardware_operational_probe_failed",
    "hardware_device_removed",
    "hardware_device_reset",
    "memory_baseline_completed",
    "cpu_baseline_completed",
    "gpu_baseline_completed",
    "storage_baseline_completed",
    "network_connectivity_completed",
    "telemetry_delivery_completed",
    "diagnostics_delivery_completed",
    "rescue_boot_completed",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_campaign_spool_dir(
    *,
    setup_logs: Path | None = None,
    run_id: str,
) -> Path:
    base = setup_logs or Path("/media/SETUP_LOGS")
    if not base.is_dir():
        base = Path("/run/setuphelfer/asus-emergency")
    path = base / "asus-emergency-linux-003" / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def init_spool_layout(spool_dir: Path) -> dict[str, str]:
    spool_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for name in DEFAULT_SPOOL_FILES:
        target = spool_dir / name
        if not target.exists():
            if name.endswith(".json"):
                target.write_text("{}\n", encoding="utf-8")
            else:
                target.write_text("", encoding="utf-8")
        paths[name] = str(target)
    return paths


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    data = json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n"
    with tmp.open("w", encoding="utf-8") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    tmp.replace(path)


def _append_jsonl(path: Path, event: Mapping[str, Any], *, max_bytes: int = 8_000_000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > max_bytes:
        rotated = path.with_suffix(path.suffix + ".1")
        if rotated.exists():
            rotated.unlink()
        path.replace(rotated)
    line = json.dumps(dict(event), ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())


def enqueue_telemetry_event(
    spool_dir: Path,
    event: Mapping[str, Any],
    *,
    consent_granted: bool,
) -> dict[str, Any]:
    """Queue event for later delivery. Offline status is queued_offline, never sent."""
    body = dict(event)
    body.setdefault("event_id", str(uuid.uuid4()))
    body.setdefault("queued_at", _now_iso())
    if "technical_summary" in body and isinstance(body["technical_summary"], str):
        body["technical_summary"] = sanitize_rescue_log(body["technical_summary"])
    # Strip serial-like keys.
    for key in list(body.keys()):
        if "serial" in key.lower():
            body.pop(key, None)

    if not consent_granted:
        body["telemetry_status"] = "blocked_no_consent"
        _append_jsonl(spool_dir / "telemetry_queue.jsonl", body)
        return {"queued": False, "telemetry_status": "blocked_no_consent", "event_id": body["event_id"]}

    body["telemetry_status"] = "queued_offline"
    _append_jsonl(spool_dir / "telemetry_queue.jsonl", body)
    state = {
        "status": "queued_offline",
        "updated_at": _now_iso(),
        "last_event_id": body["event_id"],
        "retry_count": 0,
    }
    _atomic_write_json(spool_dir / "telemetry_delivery_state.json", state)
    return {"queued": True, "telemetry_status": "queued_offline", "event_id": body["event_id"]}


def record_ingest_response(
    spool_dir: Path,
    response: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist server ingest response. HTTP 200 alone is not success."""
    ingest_status = str(response.get("ingest_status") or "review_required")
    ok = ingest_status in {"accepted", "duplicate"}
    state = {
        "status": "delivered_confirmed" if ok else "delivery_failed_or_review",
        "ingest_status": ingest_status,
        "correlation_id": response.get("correlation_id"),
        "received_events": response.get("received_events"),
        "rejected_events": response.get("rejected_events"),
        "redaction_status": response.get("redaction_status"),
        "diagnostics_forwarding_status": response.get("diagnostics_forwarding_status"),
        "retry_required": bool(response.get("retry_required")),
        "updated_at": _now_iso(),
        "http_status_alone_insufficient": True,
    }
    _atomic_write_json(spool_dir / "telemetry_delivery_state.json", state)
    return state


def record_diagnostics_response(spool_dir: Path, response: Mapping[str, Any]) -> dict[str, Any]:
    status = str(response.get("diagnostic_status") or "insufficient_evidence")
    state = {
        "status": status,
        "correlation_id": response.get("correlation_id"),
        "run_id": response.get("run_id"),
        "primary_failure_area": response.get("primary_failure_area"),
        "primary_issue_code": response.get("primary_issue_code"),
        "root_cause_confidence": response.get("root_cause_confidence"),
        "missing_drivers": list(response.get("missing_drivers") or []),
        "missing_firmware": list(response.get("missing_firmware") or []),
        "recommended_next_boot_profile": response.get("recommended_next_boot_profile"),
        "updated_at": _now_iso(),
    }
    _atomic_write_json(spool_dir / "diagnostics_delivery_state.json", state)
    return state


def write_run_manifest(spool_dir: Path, manifest: Mapping[str, Any]) -> Path:
    path = spool_dir / "run_manifest.json"
    body = dict(manifest)
    body.setdefault("generated_at", _now_iso())
    _atomic_write_json(path, body)
    return path


def update_checksums(spool_dir: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for name in DEFAULT_SPOOL_FILES:
        if name == "checksums.json":
            continue
        path = spool_dir / name
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        checksums[name] = digest
    _atomic_write_json(spool_dir / "checksums.json", {"sha256": checksums, "updated_at": _now_iso()})
    return checksums


def count_queue_events(spool_dir: Path) -> int:
    path = spool_dir / "telemetry_queue.jsonl"
    if not path.is_file():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def reconcile_event_counts(
    *,
    local_total: int,
    accepted: int,
    rejected: int,
    pending_local: int,
) -> dict[str, Any]:
    accounted = accepted + rejected + pending_local
    return {
        "local_total": local_total,
        "accepted": accepted,
        "rejected": rejected,
        "pending_local": pending_local,
        "accounted": accounted,
        "balanced": accounted == local_total,
        "delta": local_total - accounted,
    }
