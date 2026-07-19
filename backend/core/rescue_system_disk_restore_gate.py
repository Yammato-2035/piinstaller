"""Phase C — one-shot consent gate for restore onto Windows system disk."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_physical_e2e_evidence_import import find_setup_logs_mount

GATE_SCHEMA = "setuphelfer.rescue.system-disk-restore-control.v1"
GATE_REL = Path("setuphelfer/e2e-live-001d/system-disk-restore-control.json")
FEATURE_ID = "SETUPHELFER-RESTORE-SYSTEM-DISK-001"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def gate_path(setup_logs_base: Path) -> Path:
    return setup_logs_base / GATE_REL


def build_system_disk_restore_control(
    *,
    expected_payload_version: str,
    expected_vendor: str = "Micro-Star International Co., Ltd.",
    expected_model_contains: str = "GE63 Raider",
    backup_job_id: str = "",
    backup_artifact: str = "",
    operator_consent: str = "explicit",
) -> dict[str, Any]:
    return {
        "schema": GATE_SCHEMA,
        "feature": FEATURE_ID,
        "enabled": True,
        "one_shot": True,
        "consumed": False,
        "production_ready": False,
        "allow_restore_to_system_disk": True,
        "operator_consent": operator_consent,
        "expected_payload_version": expected_payload_version,
        "expected_machine": {
            "vendor": expected_vendor,
            "model_contains": expected_model_contains,
        },
        "backup_job_id": backup_job_id,
        "backup_artifact": backup_artifact,
        "created_at": _utc_now(),
        "run_nonce": secrets.token_hex(16),
    }


def write_system_disk_restore_control(setup_logs_base: Path, control: dict[str, Any]) -> Path:
    path = gate_path(setup_logs_base)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(control, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_system_disk_restore_control(setup_logs_base: Path | None = None) -> dict[str, Any] | None:
    base = setup_logs_base or find_setup_logs_mount()
    if not base:
        return None
    path = gate_path(base)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def evaluate_system_disk_restore_gate(
    *,
    control: dict[str, Any] | None,
    payload_version: str,
    machine_vendor: str = "",
    machine_model: str = "",
    operator_consent: str = "",
) -> dict[str, Any]:
    errors: list[str] = []
    if not control:
        return {"ok": False, "code": "restore_control_missing", "errors": ["missing"], "allowed": False}
    if control.get("schema") != GATE_SCHEMA:
        errors.append("invalid_schema")
    if not control.get("enabled"):
        errors.append("disabled")
    if control.get("consumed"):
        errors.append("already_consumed")
    if not control.get("allow_restore_to_system_disk"):
        errors.append("system_disk_restore_not_allowed")
    # Double consent: control must record explicit intent AND the live request must confirm.
    if control.get("operator_consent") != "explicit":
        errors.append("control_operator_consent_missing")
    if operator_consent != "explicit":
        errors.append("operator_consent_required")
    expected = str(control.get("expected_payload_version") or "")
    if expected and payload_version and expected != payload_version:
        errors.append("payload_version_mismatch")
    expected_machine = control.get("expected_machine") or {}
    vendor_need = str(expected_machine.get("vendor") or "")
    model_need = str(expected_machine.get("model_contains") or "")
    if vendor_need and vendor_need not in machine_vendor:
        errors.append("machine_vendor_mismatch")
    if model_need and model_need not in machine_model:
        errors.append("machine_model_mismatch")
    ok = not errors
    return {
        "ok": ok,
        "allowed": ok,
        "code": "ok" if ok else "restore_control_invalid",
        "errors": errors,
        "production_ready": False,
        "feature": FEATURE_ID,
    }


def consume_system_disk_restore_control(
    setup_logs_base: Path,
    *,
    consumed_by_job_id: str = "",
    terminal_status: str = "",
) -> dict[str, Any]:
    path = gate_path(setup_logs_base)
    control = load_system_disk_restore_control(setup_logs_base) or {}
    control["enabled"] = False
    control["consumed"] = True
    control["consumed_at"] = _utc_now()
    if consumed_by_job_id:
        control["consumed_by_job_id"] = consumed_by_job_id
    if terminal_status:
        control["terminal_status"] = terminal_status
    path.write_text(json.dumps(control, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return control
