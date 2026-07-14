"""Run-control file for one-shot unattended physical E2E (001D4)."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUN_CONTROL_SCHEMA = "setuphelfer.rescue.physical-e2e-control.v1"
RUN_CONTROL_REL = Path("setuphelfer/e2e-live-001d/run-control.json")
TARGET_MARKER_SCHEMA = "setuphelfer.rescue.e2e-target.v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_control_path(setup_logs_base: Path) -> Path:
    return setup_logs_base / RUN_CONTROL_REL


def build_run_control(
    *,
    expected_payload_version: str = "1.10.0.22",
    vendor: str = "Micro-Star International Co., Ltd.",
    model_contains: str = "GE63 Raider",
    telemetry_required: bool = True,
    diagnostics_required: bool = True,
    expected_event_count: int = 8,
    auto_shutdown: bool = True,
) -> dict[str, Any]:
    return {
        "schema": RUN_CONTROL_SCHEMA,
        "enabled": True,
        "one_shot": True,
        "expected_payload_version": expected_payload_version,
        "expected_machine": {
            "vendor": vendor,
            "model_contains": model_contains,
        },
        "target_marker_schema": TARGET_MARKER_SCHEMA,
        "telemetry_required": telemetry_required,
        "diagnostics_required": diagnostics_required,
        "expected_event_count": expected_event_count,
        "auto_shutdown": auto_shutdown,
        "created_at": _utc_now(),
        "run_nonce": secrets.token_hex(16),
    }


def load_run_control(setup_logs_base: Path) -> dict[str, Any] | None:
    path = run_control_path(setup_logs_base)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def write_run_control(setup_logs_base: Path, control: dict[str, Any]) -> Path:
    path = run_control_path(setup_logs_base)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(control, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def validate_run_control(control: dict[str, Any] | None) -> dict[str, Any]:
    errors: list[str] = []
    if not control:
        return {"ok": False, "code": "run_control_missing", "errors": ["missing"]}
    if control.get("schema") != RUN_CONTROL_SCHEMA:
        errors.append("invalid_schema")
    if not control.get("enabled"):
        errors.append("disabled")
    if control.get("consumed"):
        errors.append("already_consumed")
    if not control.get("expected_payload_version"):
        errors.append("missing_payload_version")
    expected = control.get("expected_machine") or {}
    if not expected.get("vendor") or not expected.get("model_contains"):
        errors.append("missing_expected_machine")
    return {"ok": not errors, "code": "ok" if not errors else "run_control_invalid", "errors": errors}


def consume_run_control(setup_logs_base: Path) -> dict[str, Any]:
    path = run_control_path(setup_logs_base)
    control = load_run_control(setup_logs_base) or {}
    control["enabled"] = False
    control["consumed"] = True
    control["consumed_at"] = _utc_now()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(control, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return control
