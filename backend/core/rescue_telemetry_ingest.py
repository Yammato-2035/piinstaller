"""Rescue / Windows inspect telemetry ingest (not DCC, not dev-server)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.windows_rescue_inspect import privacy_guard_blocks, sha256_canonical_json

TELEMETRY_ERROR_CODES = {
    "disabled": "TELEMETRY-DISABLED-001",
    "auth_missing": "TELEMETRY-AUTH-001",
    "auth_invalid": "TELEMETRY-AUTH-001",
    "schema_invalid": "TELEMETRY-SCHEMA-001",
    "hash_mismatch": "TELEMETRY-HASH-001",
    "queue_local": "TELEMETRY-QUEUE-001",
    "privacy": "TELEMETRY-PRIVACY-001",
    "consent": "TELEMETRY-CONSENT-001",
}

REQUIRED_ENVELOPE_KEYS = (
    "schema_version",
    "run_id",
    "device_session_id",
    "created_at",
    "source",
    "payload_kind",
    "privacy_level",
    "contains_personal_data",
    "operator_consent_state",
)


@dataclass(frozen=True)
class RescueTelemetryIngestConfig:
    enabled: bool
    ingest_token_configured: bool
    hmac_required: bool
    storage_root: Path
    queue_dir: Path
    ingest_dir: Path
    ack_dir: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_rescue_telemetry_ingest_config() -> RescueTelemetryIngestConfig:
    enabled = (os.environ.get("RESCUE_TELEMETRY_INGEST_ENABLED") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    token = (os.environ.get("RESCUE_TELEMETRY_INGEST_TOKEN") or "").strip()
    hmac_required = (os.environ.get("RESCUE_TELEMETRY_INGEST_REQUIRE_HMAC") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    rel = (
        os.environ.get("RESCUE_TELEMETRY_INGEST_STORAGE_ROOT")
        or "docs/evidence/runtime-results/rescue/telemetry-ingest"
    ).strip()
    root = Path(rel)
    if not root.is_absolute():
        root = _repo_root() / rel
    queue = root / "queue"
    ingest = root / "received"
    ack = root / "acks"
    return RescueTelemetryIngestConfig(
        enabled=enabled,
        ingest_token_configured=bool(token),
        hmac_required=hmac_required or bool(token),
        storage_root=root,
        queue_dir=queue,
        ingest_dir=ingest,
        ack_dir=ack,
    )


def is_rescue_telemetry_ingest_enabled() -> bool:
    return load_rescue_telemetry_ingest_config().enabled


def _runtime_status_path(cfg: RescueTelemetryIngestConfig) -> Path:
    return cfg.storage_root / "runtime_status.json"


def _read_runtime_status(cfg: RescueTelemetryIngestConfig) -> dict[str, Any]:
    path = _runtime_status_path(cfg)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_runtime_status(cfg: RescueTelemetryIngestConfig, patch: dict[str, Any]) -> None:
    current = _read_runtime_status(cfg)
    current.update(patch)
    _write_json_atomic(_runtime_status_path(cfg), current)


def _scan_latest_ack(cfg: RescueTelemetryIngestConfig) -> tuple[str | None, str | None]:
    if not cfg.ack_dir.is_dir():
        return None, None
    latest_path: Path | None = None
    latest_mtime = 0.0
    for path in cfg.ack_dir.glob("*.json"):
        if not path.is_file():
            continue
        mtime = path.stat().st_mtime
        if mtime >= latest_mtime:
            latest_mtime = mtime
            latest_path = path
    if latest_path is None:
        return None, None
    try:
        body = json.loads(latest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return latest_path.stem, None
    if isinstance(body, dict):
        return str(body.get("ack_id") or latest_path.stem), str(body.get("received_at") or "") or None
    return latest_path.stem, None


def build_health_payload(*, config: RescueTelemetryIngestConfig | None = None) -> dict[str, Any]:
    cfg = config or load_rescue_telemetry_ingest_config()
    storage_ok = False
    queue_depth = 0
    queue_available = False
    if cfg.storage_root.exists() or _ensure_storage_dirs(cfg):
        storage_ok = cfg.storage_root.is_dir()
        queue_available = cfg.queue_dir.is_dir() or storage_ok
        if cfg.queue_dir.is_dir():
            queue_depth = sum(1 for p in cfg.queue_dir.glob("*.json") if p.is_file())
    runtime = _read_runtime_status(cfg)
    last_ack_id, scanned_at = _scan_latest_ack(cfg)
    last_ingest_at = runtime.get("last_ingest_at") or scanned_at
    last_ack_id = runtime.get("last_ack_id") or last_ack_id
    last_error_code = runtime.get("last_error_code")
    if not cfg.enabled and not last_error_code:
        last_error_code = TELEMETRY_ERROR_CODES["disabled"]
    warnings: list[str] = []
    if cfg.enabled and cfg.hmac_required and not cfg.ingest_token_configured:
        warnings.append("token_required_for_hmac_but_not_configured")
    return {
        "status": "ok",
        "service": "rescue_telemetry_ingest",
        "enabled": cfg.enabled,
        "ingest_enabled": cfg.enabled,
        "ingest_path": "/api/rescue/telemetry/v1/ingest",
        "health_path": "/api/rescue/telemetry/health",
        "profile_gate_independent": True,
        "dcc_required": False,
        "profile_route_blocked_for_dcc_only": True,
        "auth_modes": ["bearer_token", "hmac_sha256_optional"],
        "mtls_documented": True,
        "storage_ok": storage_ok,
        "queue_available": queue_available,
        "queue_path_configured": bool(str(cfg.queue_dir)),
        "queue_depth": queue_depth,
        "last_ingest_at": last_ingest_at,
        "last_ack_id": last_ack_id,
        "last_error_code": last_error_code,
        "secrets_exposed": False,
        "warnings": warnings,
        "checked_at": utc_now_iso(),
    }


def _ensure_storage_dirs(cfg: RescueTelemetryIngestConfig) -> bool:
    try:
        cfg.queue_dir.mkdir(parents=True, exist_ok=True)
        cfg.ingest_dir.mkdir(parents=True, exist_ok=True)
        cfg.ack_dir.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


def _constant_time_equal(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def verify_ingest_auth(
    *,
    headers: dict[str, str],
    body_bytes: bytes,
    config: RescueTelemetryIngestConfig | None = None,
) -> tuple[bool, str | None]:
    cfg = config or load_rescue_telemetry_ingest_config()
    token_env = (os.environ.get("RESCUE_TELEMETRY_INGEST_TOKEN") or "").strip()
    if not token_env:
        if cfg.hmac_required:
            return False, TELEMETRY_ERROR_CODES["auth_missing"]
        return True, None

    auth = headers.get("authorization") or headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        supplied = auth[7:].strip()
        if _constant_time_equal(supplied, token_env):
            return True, None
        return False, TELEMETRY_ERROR_CODES["auth_invalid"]

    header_token = headers.get("x-setuphelfer-telemetry-token") or headers.get("X-Setuphelfer-Telemetry-Token") or ""
    if header_token and _constant_time_equal(header_token.strip(), token_env):
        return True, None

    payload_hash_header = headers.get("x-setuphelfer-payload-hash") or headers.get("X-Setuphelfer-Payload-Hash") or ""
    if payload_hash_header:
        expected = hmac.new(token_env.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
        if _constant_time_equal(payload_hash_header.strip().lower(), expected.lower()):
            return True, None

    return False, TELEMETRY_ERROR_CODES["auth_invalid"]


def validate_envelope(payload: dict[str, Any]) -> tuple[bool, str | None]:
    if not isinstance(payload, dict):
        return False, TELEMETRY_ERROR_CODES["schema_invalid"]
    for key in REQUIRED_ENVELOPE_KEYS:
        if key not in payload:
            return False, TELEMETRY_ERROR_CODES["schema_invalid"]
    if payload.get("source") != "rescue_stick":
        return False, TELEMETRY_ERROR_CODES["schema_invalid"]
    if payload.get("payload_kind") != "windows_rescue_inspect":
        return False, TELEMETRY_ERROR_CODES["schema_invalid"]
    if payload.get("privacy_level") != "diagnostic_metadata":
        return False, TELEMETRY_ERROR_CODES["schema_invalid"]
    blocked, err = privacy_guard_blocks(payload)
    if blocked:
        return False, err or TELEMETRY_ERROR_CODES["privacy"]
    return True, None


def compute_payload_hash(payload: dict[str, Any]) -> str:
    """Canonical SHA-256 over envelope JSON excluding the self-referential hash field."""
    body = {k: v for k, v in payload.items() if k != "payload_hash_sha256"}
    return sha256_canonical_json(body)


def _write_json_atomic(path: Path, obj: dict[str, Any]) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(path)
        return True
    except OSError:
        return False


def enqueue_payload(
    payload: dict[str, Any],
    *,
    run_id: str,
    reason: str,
    config: RescueTelemetryIngestConfig | None = None,
) -> dict[str, Any]:
    cfg = config or load_rescue_telemetry_ingest_config()
    entry = {
        "queued_at": utc_now_iso(),
        "run_id": run_id,
        "reason": reason,
        "payload_kind": payload.get("payload_kind"),
        "payload_hash_sha256": compute_payload_hash(payload),
        "retry_plan": "operator_or_rescue_agent_resend",
    }
    name = f"{run_id}_{uuid.uuid4().hex[:8]}.json"
    ok = _write_json_atomic(cfg.queue_dir / name, entry)
    return {
        "status": "queued_local" if ok else "queue_write_failed",
        "code": TELEMETRY_ERROR_CODES["queue_local"] if ok else "TELEMETRY-QUEUE-002",
        "queue_entry": name if ok else None,
    }


def process_telemetry_ingest(
    payload: dict[str, Any],
    *,
    headers: dict[str, str],
    body_bytes: bytes,
    config: RescueTelemetryIngestConfig | None = None,
) -> dict[str, Any]:
    cfg = config or load_rescue_telemetry_ingest_config()
    if not cfg.enabled:
        _write_runtime_status(cfg, {"last_error_code": TELEMETRY_ERROR_CODES["disabled"]})
        return {
            "http_status": 503,
            "body": {
                "status": "disabled",
                "code": TELEMETRY_ERROR_CODES["disabled"],
                "message": "Set RESCUE_TELEMETRY_INGEST_ENABLED=1 to accept rescue telemetry.",
            },
        }

    ok_auth, auth_code = verify_ingest_auth(headers=headers, body_bytes=body_bytes, config=cfg)
    if not ok_auth:
        _write_runtime_status(cfg, {"last_error_code": auth_code})
        return {
            "http_status": 401,
            "body": {"status": "error", "code": auth_code, "message": "Telemetry ingest authentication failed."},
        }

    valid, schema_code = validate_envelope(payload)
    if not valid:
        _write_runtime_status(cfg, {"last_error_code": schema_code})
        return {
            "http_status": 422,
            "body": {"status": "error", "code": schema_code, "message": "Invalid telemetry envelope."},
        }

    server_hash = compute_payload_hash(payload)
    declared_hash = str(payload.get("payload_hash_sha256") or "").strip().lower()
    client_hash = (
        headers.get("x-setuphelfer-payload-hash") or headers.get("X-Setuphelfer-Payload-Hash") or ""
    ).strip().lower()
    if not declared_hash or declared_hash != server_hash:
        _write_runtime_status(cfg, {"last_error_code": TELEMETRY_ERROR_CODES["hash_mismatch"]})
        return {
            "http_status": 409,
            "body": {
                "status": "error",
                "code": TELEMETRY_ERROR_CODES["hash_mismatch"],
                "payload_hash_sha256": server_hash,
                "declared_hash_sha256": declared_hash or None,
            },
        }
    if client_hash and client_hash != server_hash:
        _write_runtime_status(cfg, {"last_error_code": TELEMETRY_ERROR_CODES["hash_mismatch"]})
        return {
            "http_status": 409,
            "body": {
                "status": "error",
                "code": TELEMETRY_ERROR_CODES["hash_mismatch"],
                "payload_hash_sha256": server_hash,
                "client_hash_sha256": client_hash,
            },
        }

    run_id = str(payload.get("run_id") or "unknown")
    ack_id = f"rti-{uuid.uuid4().hex[:16]}"
    received_at = utc_now_iso()
    stored = {
        "ack_id": ack_id,
        "received_at": received_at,
        "run_id": run_id,
        "device_session_id": payload.get("device_session_id"),
        "payload_kind": payload.get("payload_kind"),
        "payload_hash_sha256": server_hash,
        "privacy_level": payload.get("privacy_level"),
        "diagnostics_codes": (payload.get("diagnostics") or {}).get("codes")
        if isinstance(payload.get("diagnostics"), dict)
        else [],
    }

    if not _ensure_storage_dirs(cfg):
        q = enqueue_payload(payload, run_id=run_id, reason="storage_not_writable", config=cfg)
        return {
            "http_status": 202,
            "body": {
                "status": q["status"],
                "code": q["code"],
                "ack_id": None,
                "received_at": received_at,
                "payload_hash_sha256": server_hash,
                "schema_version": payload.get("schema_version"),
                "queue_entry": q.get("queue_entry"),
            },
        }

    ingest_path = cfg.ingest_dir / f"{run_id}_{ack_id}.json"
    ack_path = cfg.ack_dir / f"{ack_id}.json"
    if not _write_json_atomic(ingest_path, {**stored, "envelope": payload}):
        q = enqueue_payload(payload, run_id=run_id, reason="ingest_write_failed", config=cfg)
        return {
            "http_status": 202,
            "body": {
                "status": q["status"],
                "code": q["code"],
                "ack_id": None,
                "received_at": received_at,
                "payload_hash_sha256": server_hash,
                "schema_version": payload.get("schema_version"),
            },
        }

    ack_body = {
        "status": "acknowledged",
        "ack_id": ack_id,
        "received_at": received_at,
        "payload_hash_sha256": server_hash,
        "schema_version": str(payload.get("schema_version") or "1.0.0"),
        "hash_match": True,
    }
    _write_json_atomic(ack_path, ack_body)
    _write_runtime_status(
        cfg,
        {
            "last_ingest_at": received_at,
            "last_ack_id": ack_id,
            "last_error_code": None,
        },
    )
    return {"http_status": 200, "body": ack_body}
