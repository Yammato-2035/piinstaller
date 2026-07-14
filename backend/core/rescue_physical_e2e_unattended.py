"""Unattended MSI physical E2E with run-control, state machine, and registered targets."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.backup_target_auto_prepare import discover_external_backup_candidates
from core.rescue_backup_target_policy import RESCUE_STICK_LABELS
from core.rescue_physical_e2e_dev_automation import create_test_data, resolve_token_file
from core.rescue_physical_e2e_evidence_import import find_setup_logs_mount
from core.rescue_physical_e2e_journal import write_json
from core.rescue_physical_e2e_machine_gate import (
    verify_boot_parameters,
    verify_machine_identity,
    verify_payload_version_gate,
)
from core.rescue_physical_e2e_models import FEATURE_ID, OPERATION_EVENTS, PRODUCTION_READY
from core.rescue_physical_e2e_orchestrator import run_physical_e2e_workflow
from core.rescue_physical_e2e_run_control import (
    consume_run_control,
    load_run_control,
    validate_run_control,
)
from core.rescue_physical_e2e_state_machine import PhysicalE2EStateMachine
from core.rescue_physical_e2e_test_target import (
    discover_registered_test_targets,
    prepare_run_paths,
)
from core.rescue_payload_version import rescue_payload_version

FEATURE_ID_UNATTENDED = "SETUPHELFER-E2E-LIVE-001D4"
AUTO_RESULT = "auto-physical-e2e-result.json"
DEV_LAB_RUN_PREFIX = "e2e-rescue-physical-20260714-153401"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_msi_physical_e2e_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"e2e-rescue-msi-{stamp}-{uuid.uuid4().hex[:8]}"


def _is_rescue_stick_label(label: str | None) -> bool:
    if not label:
        return False
    upper = label.upper()
    return upper in {x.upper() for x in RESCUE_STICK_LABELS} or "SETUPHELFER" in upper


def _collect_external_candidates() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for cand in discover_external_backup_candidates():
        label = cand.label or ""
        if _is_rescue_stick_label(label):
            continue
        mount = cand.existing_mount
        if not mount:
            continue
        out.append(
            {
                "partition_id": cand.partition_id,
                "disk_id": cand.disk_id,
                "mount": mount,
                "uuid": "",
                "fstype": cand.fstype,
                "transport": cand.transport,
                "label": label,
                "removable": cand.transport == "usb",
            }
        )
    return out


def _resolve_token() -> str | None:
    explicit = resolve_token_file(None)
    if explicit:
        return explicit
    for pattern in ("/media/*/SETUP_LOGS", "/run/media/*/SETUP_LOGS", "/run/setuphelfer/esp-rw"):
        for base in Path("/").glob(pattern.lstrip("/")):
            path = base / "setuphelfer/lab/telemetry-lab-token"
            if path.is_file() and path.stat().st_size > 0:
                return str(path)
    return None


def _write_shutdown_evidence(journal_dir: Path, *, state: str, evidence_complete: bool) -> None:
    write_json(
        journal_dir / "shutdown-evidence.json",
        {
            "shutdown_reason": "e2e_complete",
            "evidence_complete": evidence_complete,
            "state": state,
            "recorded_at": _utc_now(),
        },
    )


def _sync_journal(journal_dir: Path) -> None:
    for path in journal_dir.rglob("*"):
        if path.is_file():
            with path.open("rb") as handle:
                os.fsync(handle.fileno())
    try:
        fd = os.open(str(journal_dir), os.O_DIRECTORY)
        os.fsync(fd)
        os.close(fd)
    except OSError:
        pass
    os.sync()


def run_unattended_msi_physical_e2e(
    *,
    repo_root: Path | None = None,
    setup_logs_base: Path | None = None,
    create_data_script: Path | None = None,
    target_bytes: int = 64 * 1024 * 1024,
) -> dict[str, Any]:
    started = _utc_now()
    logs = setup_logs_base or find_setup_logs_mount()
    repo = repo_root or Path("/opt/setuphelfer-rescue")

    run_control = load_run_control(logs) if logs else None
    rc_gate = validate_run_control(run_control)
    if not rc_gate.get("ok"):
        return {
            "feature": FEATURE_ID_UNATTENDED,
            "status": "blocked",
            "code": rc_gate.get("code"),
            "errors": rc_gate.get("errors"),
            "automation_class": "blocked",
            "production_ready": PRODUCTION_READY,
        }

    e2e_run_id = new_msi_physical_e2e_run_id()
    correlation_id = str(uuid.uuid4())
    journal_dir = (logs or Path("/run/setuphelfer/esp-rw")) / "setuphelfer/evidence/e2e" / e2e_run_id
    sm = PhysicalE2EStateMachine(journal_dir, e2e_run_id=e2e_run_id, correlation_id=correlation_id)
    sm.transition("initialized")

    boot_gate = verify_boot_parameters()
    if not boot_gate.get("ok"):
        sm.transition("blocked", detail={"reason": "boot_parameters", "missing": boot_gate.get("missing")})
        return {"feature": FEATURE_ID_UNATTENDED, "status": "blocked", "code": "boot_parameters_missing", "e2e_run_id": e2e_run_id}
    sm.transition("boot_verified")

    machine_gate = verify_machine_identity((run_control or {}).get("expected_machine"))
    write_json(journal_dir / "machine-identity.json", machine_gate.get("identity") or {})
    if not machine_gate.get("ok"):
        sm.transition("blocked", detail={"code": machine_gate.get("code")})
        return {"feature": FEATURE_ID_UNATTENDED, "status": "blocked", "code": machine_gate.get("code"), "e2e_run_id": e2e_run_id}
    sm.transition("machine_identity_verified")

    pv_gate = verify_payload_version_gate(str((run_control or {}).get("expected_payload_version") or ""))
    if not pv_gate.get("ok"):
        sm.transition("blocked", detail=pv_gate)
        return {"feature": FEATURE_ID_UNATTENDED, "status": "blocked", "code": pv_gate.get("code"), "e2e_run_id": e2e_run_id}

    if logs is None:
        sm.transition("blocked", detail={"reason": "setup_logs_not_mounted"})
        return {"feature": FEATURE_ID_UNATTENDED, "status": "blocked", "code": "setup_logs_not_mounted", "e2e_run_id": e2e_run_id}
    sm.transition("setup_logs_ready")

    candidates = _collect_external_candidates()
    valid, ambiguity = discover_registered_test_targets(candidates)
    if ambiguity:
        sm.transition("blocked", detail=ambiguity)
        return {"feature": FEATURE_ID_UNATTENDED, "status": "blocked", "code": ambiguity.get("code"), "e2e_run_id": e2e_run_id}

    if not valid:
        # Synthetic smoke fallback — not full physical success
        sm.transition("test_target_discovered", detail={"mode": "automation_smoke_only"})
        result = {
            "feature": FEATURE_ID_UNATTENDED,
            "started_at": started,
            "completed_at": _utc_now(),
            "e2e_run_id": e2e_run_id,
            "correlation_id": correlation_id,
            "status": "physical_automation_smoke_passed_external_target_pending",
            "automation_class": "automation_smoke_only",
            "layout_mode": "msi_lab_synthetic",
            "production_ready": PRODUCTION_READY,
            "source": "physical_msi",
        }
        write_json(journal_dir / AUTO_RESULT, result)
        if logs and run_control and run_control.get("one_shot"):
            consume_run_control(logs)
        return result

    sm.transition("test_target_discovered")
    sm.transition("test_target_verified", detail={"mount": valid[0].get("mount")})
    write_json(journal_dir / "storage-selection.json", {"target": {k: v for k, v in valid[0].items() if k != "marker"}})

    paths = prepare_run_paths(valid[0], e2e_run_id)
    sm.transition("test_data_creating")
    script_candidates = [
        create_data_script,
        repo / "scripts/create-e2e-backup-test-data.sh",
        Path("/usr/local/sbin/create-e2e-backup-test-data.sh"),
    ]
    data_script = next((p for p in script_candidates if p and p.is_file()), None)
    if data_script is None:
        sm.transition("failed", detail={"error": "create_e2e_test_data_script_missing"})
        return {"feature": FEATURE_ID_UNATTENDED, "status": "failed", "error": "create_e2e_test_data_script_missing", "e2e_run_id": e2e_run_id}

    try:
        create_test_data(paths["source"], repo_root=repo, target_bytes=target_bytes)
    except Exception as exc:  # noqa: BLE001
        sm.transition("failed", detail={"error": str(exc)})
        return {"feature": FEATURE_ID_UNATTENDED, "status": "failed", "error": "test_data_creation_failed", "e2e_run_id": e2e_run_id}
    sm.transition("test_data_ready")

    token = _resolve_token()
    telemetry_required = bool((run_control or {}).get("telemetry_required"))
    if telemetry_required and not token:
        sm.transition("blocked", detail={"reason": "live_telemetry_token_unavailable"})
        return {"feature": FEATURE_ID_UNATTENDED, "status": "blocked", "code": "live_telemetry_token_unavailable", "e2e_run_id": e2e_run_id}

    consent = "granted" if token else "local_only"
    work_root = paths["work_root"].resolve()

    sm.transition("backup_running")
    workflow = run_physical_e2e_workflow(
        source_dir=paths["source"],
        backup_archive=paths["backup_archive"],
        restore_dir=paths["restore_dir"],
        consent=consent,
        operator_approved=True,
        allowed_source_prefixes=(work_root,),
        allowed_output_prefixes=(work_root,),
        allowed_restore_prefixes=(work_root,),
        setup_logs_base=logs,
        e2e_run_id=e2e_run_id,
        token_file=token,
        lab_tmpfs_mode=False,
        skip_diagnostics_poll=not bool(token),
    )

    if workflow.get("success"):
        sm.transition("backup_completed")
        sm.transition("verify_completed")
        sm.transition("restore_completed")
        sm.transition("manifest_comparison_completed")
    else:
        sm.transition("failed", detail={"phase": workflow.get("phase")})

    receipts = int((workflow.get("telemetry") or {}).get("receipts_stored") or 0)
    expected = int((run_control or {}).get("expected_event_count") or len(OPERATION_EVENTS))
    if workflow.get("success") and token:
        sm.transition("telemetry_sending")
        if receipts >= expected:
            sm.transition("telemetry_receipts_complete")
            sm.transition("diagnostics_waiting")
            diag = workflow.get("diagnostics") or {}
            if diag.get("data_received"):
                sm.transition("diagnostics_complete")

    final_status = str(workflow.get("status") or "failed")
    if workflow.get("success") and receipts >= expected and (workflow.get("diagnostics") or {}).get("findings_count") == 0:
        final_status = "physical_rescue_telemetry_diagnostics_e2e_passed"
    elif workflow.get("success") and receipts >= expected:
        final_status = "physical_rescue_passed_server_verification_pending"
    elif workflow.get("success") and not token:
        final_status = "physical_backup_restore_passed_telemetry_failed"

    sm.transition("evidence_syncing")
    auto_result = {
        "feature": FEATURE_ID_UNATTENDED,
        "schema_version": 1,
        "started_at": started,
        "completed_at": _utc_now(),
        "e2e_run_id": e2e_run_id,
        "correlation_id": correlation_id,
        "rescue_session_id": workflow.get("rescue_session_id"),
        "payload_version": rescue_payload_version(),
        "layout_mode": paths["layout_mode"],
        "automation_class": paths.get("automation_class", "physical_full"),
        "source": "physical_msi",
        "token_present": bool(token),
        "consent_effective": consent,
        "production_ready": PRODUCTION_READY,
        "workflow": workflow,
        "status": final_status,
    }
    write_json(journal_dir / AUTO_RESULT, auto_result)
    _write_shutdown_evidence(journal_dir, state=final_status, evidence_complete=True)
    _sync_journal(journal_dir)
    sm.transition("evidence_complete")
    if workflow.get("success") and final_status.startswith("physical_rescue"):
        sm.transition("passed", detail={"status": final_status})
    elif final_status == "blocked":
        sm.transition("blocked")
    elif not workflow.get("success"):
        sm.transition("failed")

    if logs and run_control and run_control.get("one_shot"):
        consume_run_control(logs)

    return auto_result
