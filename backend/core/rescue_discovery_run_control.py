"""One-shot discovery run-control (SETUPHELFER-E2E-LIVE-001D7 / 001D7B)."""

from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DISCOVERY_CONTROL_SCHEMA = "setuphelfer.rescue.discovery-control.v1"
DISCOVERY_CONTROL_REL = Path("setuphelfer/e2e-live-001d/discovery-run-control.json")
FEATURE_ID = "SETUPHELFER-E2E-LIVE-001D7"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def discovery_run_control_path(setup_logs_base: Path) -> Path:
    return setup_logs_base / DISCOVERY_CONTROL_REL


def build_discovery_run_control(
    *,
    expected_payload_version: str,
    expected_machine_family: str = "GE63 Raider",
    run_mode: str = "auto_discovery_only",
    auto_shutdown: bool = True,
) -> dict[str, Any]:
    return {
        "schema": DISCOVERY_CONTROL_SCHEMA,
        "feature": FEATURE_ID,
        "enabled": True,
        "one_shot": True,
        "expected_payload_version": expected_payload_version,
        "expected_machine_family": expected_machine_family,
        "run_mode": run_mode,
        "allow_destructive_storage_actions": False,
        "allow_backup": False,
        "allow_restore": False,
        "allow_partitioning": False,
        "allow_format": False,
        "telemetry_required": False,
        "diagnostics_requested": True,
        "auto_shutdown": auto_shutdown,
        "consumed": False,
        "run_nonce": secrets.token_hex(16),
        "created_at": _utc_now(),
    }


def load_discovery_run_control(setup_logs_base: Path) -> dict[str, Any] | None:
    path = discovery_run_control_path(setup_logs_base)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_discovery_run_control(setup_logs_base: Path, control: dict[str, Any]) -> Path:
    path = discovery_run_control_path(setup_logs_base)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(control, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with tmp.open("rb") as handle:
        os.fsync(handle.fileno())
    tmp.replace(path)
    try:
        fd = os.open(str(path.parent), os.O_DIRECTORY)
        os.fsync(fd)
        os.close(fd)
    except OSError:
        pass
    return path


def validate_discovery_run_control(control: dict[str, Any] | None) -> dict[str, Any]:
    errors: list[str] = []
    if not control:
        return {"ok": False, "code": "discovery_run_control_missing", "errors": ["missing"]}
    if control.get("schema") != DISCOVERY_CONTROL_SCHEMA:
        errors.append("invalid_schema")
    if not control.get("enabled"):
        errors.append("disabled")
    if control.get("consumed"):
        errors.append("already_consumed")
    if control.get("one_shot") is not True:
        errors.append("one_shot_required")
    if control.get("run_mode") != "auto_discovery_only":
        errors.append("run_mode_not_auto_discovery_only")
    if control.get("allow_destructive_storage_actions"):
        errors.append("destructive_not_allowed")
    if control.get("allow_backup"):
        errors.append("backup_not_allowed")
    if control.get("allow_restore"):
        errors.append("restore_not_allowed")
    if not control.get("expected_payload_version"):
        errors.append("missing_payload_version")
    return {
        "ok": not errors,
        "code": "ok" if not errors else "discovery_run_control_invalid",
        "errors": errors,
    }


def consume_discovery_run_control(
    setup_logs_base: Path,
    *,
    consumed_by_session_id: str = "",
    terminal_status: str = "",
) -> dict[str, Any]:
    path = discovery_run_control_path(setup_logs_base)
    control = load_discovery_run_control(setup_logs_base) or {}
    control["enabled"] = False
    control["consumed"] = True
    control["consumed_at"] = _utc_now()
    if consumed_by_session_id:
        control["consumed_by_session_id"] = consumed_by_session_id
    if terminal_status:
        control["terminal_status"] = terminal_status
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(control, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with tmp.open("rb") as handle:
        os.fsync(handle.fileno())
    tmp.replace(path)
    return control
