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
FEATURE_ID_001D5 = "SETUPHELFER-E2E-LIVE-001D5"


def build_destructive_lab_target(
    *,
    expected_existing_partition_uuid: str = "44ce6f76-7896-4623-87b0-d81aedbed6d5",
    expected_existing_label: str = "Backup",
) -> dict[str, Any]:
    return {
        "enabled": True,
        "operator_authorized": True,
        "purpose": "setuphelfer_msi_physical_e2e_only",
        "expected_transport": "usb",
        "expected_model_contains": "SABRENT",
        "expected_size_bytes_min": 900_000_000_000,
        "expected_size_bytes_max": 1_100_000_000_000,
        "expected_existing_partition_uuid": expected_existing_partition_uuid,
        "expected_existing_label": expected_existing_label,
        "expected_role": "external_backup_hdd",
        "allow_wipefs": True,
        "allow_new_gpt": True,
        "allow_partitioning": True,
        "allow_format": True,
        "allow_backup": True,
        "allow_restore": True,
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_control_path(setup_logs_base: Path) -> Path:
    return setup_logs_base / RUN_CONTROL_REL


def build_run_control(
    *,
    expected_payload_version: str = "1.10.0.24",
    vendor: str = "Micro-Star International Co., Ltd.",
    model_contains: str = "GE63 Raider",
    telemetry_required: bool = True,
    diagnostics_required: bool = True,
    expected_event_count: int = 8,
    auto_shutdown: bool = True,
    destructive_lab_target: dict[str, Any] | None = None,
) -> dict[str, Any]:
    control: dict[str, Any] = {
        "schema": RUN_CONTROL_SCHEMA,
        "feature": FEATURE_ID_001D5,
        "enabled": True,
        "one_shot": True,
        "consumed": False,
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
    if destructive_lab_target is not None:
        control["destructive_lab_target"] = destructive_lab_target
    else:
        control["destructive_lab_target"] = build_destructive_lab_target()
    return control


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


def consume_run_control(
    setup_logs_base: Path,
    *,
    consumed_by_run_id: str = "",
    terminal_status: str = "",
) -> dict[str, Any]:
    path = run_control_path(setup_logs_base)
    control = load_run_control(setup_logs_base) or {}
    control["enabled"] = False
    control["consumed"] = True
    control["consumed_at"] = _utc_now()
    if consumed_by_run_id:
        control["consumed_by_run_id"] = consumed_by_run_id
    if terminal_status:
        control["terminal_status"] = terminal_status
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(control, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return control
