"""Unattended MSI physical E2E with run-control, state machine, and lab HDD targets."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.backup_target_auto_prepare import discover_external_backup_candidates
from core.rescue_backup_target_policy import RESCUE_STICK_LABELS
from core.rescue_physical_e2e_auto_e2e_state import (
    AUTO_E2E_PHASES,
    append_auto_e2e_event,
    check_abort,
    init_auto_e2e_state,
    mirror_state_to_setup_logs,
    update_auto_e2e_state,
    write_heartbeat,
)
from core.rescue_physical_e2e_destructive_target import (
    load_destructive_lab_config,
    mount_e2e_partitions,
    prepare_destructive_run_paths,
    select_destructive_lab_target,
    unmount_e2e_partitions,
    verify_layout_after_partition,
    wipe_and_partition_disk,
)
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
    FEATURE_ID_001D5,
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

FEATURE_ID_UNATTENDED = FEATURE_ID_001D5
AUTO_RESULT = "auto-physical-e2e-result.json"
DEV_LAB_RUN_PREFIX = "e2e-rescue-physical-20260714-153401"
PHYSICAL_SUCCESS_STATUSES = frozenset(
    {
        "physical_rescue_telemetry_diagnostics_e2e_passed",
        "physical_rescue_passed_server_verification_pending",
        "physical_backup_restore_passed_telemetry_failed",
        "physical_automation_smoke_passed_external_target_pending",
        "msi_e2e_auto_passed",
    }
)


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


def _finalize_terminal(
    *,
    logs: Path,
    run_control: dict[str, Any] | None,
    e2e_run_id: str,
    final_status: str,
) -> None:
    if logs and run_control and run_control.get("one_shot"):
        consume_run_control(
            logs,
            consumed_by_run_id=e2e_run_id,
            terminal_status=final_status,
        )


def _run_destructive_lab_path(
    *,
    logs: Path,
    repo: Path,
    run_control: dict[str, Any],
    e2e_run_id: str,
    correlation_id: str,
    journal_dir: Path,
    sm: PhysicalE2EStateMachine,
    started: str,
    target_bytes: int,
    create_data_script: Path | None,
) -> dict[str, Any]:
    destructive_cfg = load_destructive_lab_config(run_control)
    if not destructive_cfg:
        sm.transition("blocked", detail={"reason": "destructive_lab_target_missing"})
        return {
            "feature": FEATURE_ID_UNATTENDED,
            "status": "blocked",
            "code": "destructive_lab_target_missing",
            "e2e_run_id": e2e_run_id,
        }

    init_auto_e2e_state(mode="auto_physical_e2e_locked", run_id=e2e_run_id)
    update_auto_e2e_state(phase="test_disk_prepare", status="running", run_id=e2e_run_id)
    write_heartbeat(run_id=e2e_run_id, phase="test_disk_prepare")

    abort = check_abort()
    if abort:
        sm.transition("blocked", detail={"reason": abort.get("reason")})
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status="cancelled_by_operator")
        return {"feature": FEATURE_ID_UNATTENDED, "status": "cancelled_by_operator", "e2e_run_id": e2e_run_id}

    candidate, gate = select_destructive_lab_target(destructive_cfg)
    if not gate.get("ok") or candidate is None:
        sm.transition("blocked", detail=gate)
        result = {
            "feature": FEATURE_ID_UNATTENDED,
            "status": "blocked",
            "code": gate.get("code"),
            "e2e_run_id": e2e_run_id,
            "automation_class": "blocked",
            "production_ready": PRODUCTION_READY,
        }
        write_json(journal_dir / AUTO_RESULT, result)
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status="blocked")
        return result

    sm.transition("test_target_discovered", detail={"mode": "destructive_lab_hdd"})
    write_json(
        journal_dir / "storage-selection.json",
        {
            "target_type": "dedicated_external_lab_hdd",
            "target_layout": "three_partition_e2e",
            "target_capacity_class": "large",
            "identity_gate": "passed",
        },
    )
    sm.transition("test_target_verified")

    partition_result = wipe_and_partition_disk(candidate.disk_path, config=destructive_cfg, run_id=e2e_run_id)
    if not partition_result.get("ok"):
        sm.transition("failed", detail=partition_result)
        status = str(partition_result.get("code") or "failed")
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status=status)
        return {"feature": FEATURE_ID_UNATTENDED, "status": status, "e2e_run_id": e2e_run_id, "detail": partition_result}

    layout_gate = verify_layout_after_partition(candidate.disk_path)
    if not layout_gate.get("ok"):
        sm.transition("failed", detail=layout_gate)
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status=layout_gate.get("code", "failed"))
        return {"feature": FEATURE_ID_UNATTENDED, "status": layout_gate.get("code"), "e2e_run_id": e2e_run_id}

    mount_result = mount_e2e_partitions(candidate.disk_path, e2e_run_id)
    if not mount_result.get("ok"):
        sm.transition("failed", detail=mount_result)
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status="failed")
        return {"feature": FEATURE_ID_UNATTENDED, "status": "failed", "e2e_run_id": e2e_run_id, "detail": mount_result}

    mounts = mount_result["mounts"]
    try:
        paths = prepare_destructive_run_paths(mounts, e2e_run_id)
    except ValueError as exc:
        sm.transition("failed", detail={"error": str(exc)})
        unmount_e2e_partitions(mounts)
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status="failed")
        return {"feature": FEATURE_ID_UNATTENDED, "status": "failed", "error": str(exc), "e2e_run_id": e2e_run_id}

    update_auto_e2e_state(phase="test_data_create", status="running")
    write_heartbeat(run_id=e2e_run_id, phase="test_data_create")
    sm.transition("test_data_creating")
    script_candidates = [
        create_data_script,
        repo / "scripts/create-e2e-backup-test-data.sh",
        Path("/usr/local/sbin/create-e2e-backup-test-data.sh"),
        Path("/opt/setuphelfer-rescue/scripts/create-e2e-backup-test-data.sh"),
    ]
    data_script = next((p for p in script_candidates if p and p.is_file()), None)
    if data_script is None:
        sm.transition("failed", detail={"error": "create_e2e_test_data_script_missing"})
        unmount_e2e_partitions(mounts)
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status="failed")
        return {"feature": FEATURE_ID_UNATTENDED, "status": "failed", "error": "create_e2e_test_data_script_missing", "e2e_run_id": e2e_run_id}

    try:
        create_test_data(paths["source"], repo_root=repo, target_bytes=max(target_bytes, 128 * 1024 * 1024))
    except Exception as exc:  # noqa: BLE001
        sm.transition("failed", detail={"error": str(exc)})
        unmount_e2e_partitions(mounts)
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status="failed")
        return {"feature": FEATURE_ID_UNATTENDED, "status": "failed", "error": "test_data_creation_failed", "e2e_run_id": e2e_run_id}
    sm.transition("test_data_ready")

    token = _resolve_token()
    telemetry_required = bool(run_control.get("telemetry_required"))
    if telemetry_required and not token:
        sm.transition("blocked", detail={"reason": "live_telemetry_token_unavailable"})
        unmount_e2e_partitions(mounts)
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status="blocked")
        return {"feature": FEATURE_ID_UNATTENDED, "status": "blocked", "code": "live_telemetry_token_unavailable", "e2e_run_id": e2e_run_id}

    consent = "granted" if token else "local_only"
    update_auto_e2e_state(phase="backup_create", status="running")
    write_heartbeat(run_id=e2e_run_id, phase="backup_create")
    sm.transition("backup_running")
    workflow = run_physical_e2e_workflow(
        source_dir=paths["source"],
        backup_archive=paths["backup_archive"],
        restore_dir=paths["restore_dir"],
        consent=consent,
        operator_approved=True,
        allowed_source_prefixes=tuple(paths["allowed_source_prefixes"]),
        allowed_output_prefixes=tuple(paths["allowed_output_prefixes"]),
        allowed_restore_prefixes=tuple(paths["allowed_restore_prefixes"]),
        setup_logs_base=logs,
        e2e_run_id=e2e_run_id,
        token_file=token,
        lab_tmpfs_mode=False,
        skip_diagnostics_poll=not bool(token),
    )

    if workflow.get("success"):
        update_auto_e2e_state(phase="data_compare", status="running")
        sm.transition("backup_completed")
        sm.transition("verify_completed")
        sm.transition("restore_completed")
        sm.transition("manifest_comparison_completed")
    else:
        sm.transition("failed", detail={"phase": workflow.get("phase")})

    receipts = int((workflow.get("telemetry") or {}).get("receipts_stored") or 0)
    expected = int(run_control.get("expected_event_count") or len(OPERATION_EVENTS))
    if workflow.get("success") and token:
        update_auto_e2e_state(phase="telemetry_send", status="running")
        sm.transition("telemetry_sending")
        if receipts >= expected:
            sm.transition("telemetry_receipts_complete")
            update_auto_e2e_state(phase="diagnostics_fetch", status="running")
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

    update_auto_e2e_state(phase="evidence_save", status="passed" if workflow.get("success") else "failed")
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
        "automation_class": paths.get("automation_class", "physical_full_destructive"),
        "source": "physical_msi",
        "token_present": bool(token),
        "consent_effective": consent,
        "production_ready": PRODUCTION_READY,
        "target_type": paths.get("target_type"),
        "target_layout": paths.get("target_layout"),
        "target_capacity_class": paths.get("target_capacity_class"),
        "workflow": workflow,
        "status": final_status,
    }
    write_json(journal_dir / AUTO_RESULT, auto_result)
    _write_shutdown_evidence(journal_dir, state=final_status, evidence_complete=True)
    _sync_journal(journal_dir)
    mirror_state_to_setup_logs(logs)
    sm.transition("evidence_complete")
    if workflow.get("success") and final_status.startswith("physical_rescue"):
        sm.transition("passed", detail={"status": final_status})
        update_auto_e2e_state(phase="shutdown", status="passed", last_progress="Evidence synchronisiert")
    elif final_status == "blocked":
        sm.transition("blocked")
        update_auto_e2e_state(status="blocked")
    elif not workflow.get("success"):
        sm.transition("failed")
        update_auto_e2e_state(status="failed")

    unmount_e2e_partitions(mounts)
    _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status=final_status)
    append_auto_e2e_event("run_complete", detail={"status": final_status, "run_id": e2e_run_id})
    return auto_result


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
    write_heartbeat(run_id=e2e_run_id, phase="initialized")

    boot_gate = verify_boot_parameters()
    if not boot_gate.get("ok"):
        sm.transition("blocked", detail={"reason": "boot_parameters", "missing": boot_gate.get("missing")})
        _finalize_terminal(logs=logs or Path("/tmp"), run_control=run_control, e2e_run_id=e2e_run_id, final_status="blocked")
        return {"feature": FEATURE_ID_UNATTENDED, "status": "blocked", "code": "boot_parameters_missing", "e2e_run_id": e2e_run_id}
    sm.transition("boot_verified")

    machine_gate = verify_machine_identity((run_control or {}).get("expected_machine"))
    write_json(journal_dir / "machine-identity.json", machine_gate.get("identity") or {})
    if not machine_gate.get("ok"):
        sm.transition("blocked", detail={"code": machine_gate.get("code")})
        _finalize_terminal(logs=logs or Path("/tmp"), run_control=run_control, e2e_run_id=e2e_run_id, final_status="blocked")
        return {"feature": FEATURE_ID_UNATTENDED, "status": "blocked", "code": machine_gate.get("code"), "e2e_run_id": e2e_run_id}
    sm.transition("machine_identity_verified")

    pv_gate = verify_payload_version_gate(str((run_control or {}).get("expected_payload_version") or ""))
    if not pv_gate.get("ok"):
        sm.transition("blocked", detail=pv_gate)
        _finalize_terminal(logs=logs or Path("/tmp"), run_control=run_control, e2e_run_id=e2e_run_id, final_status="blocked")
        return {"feature": FEATURE_ID_UNATTENDED, "status": "blocked", "code": pv_gate.get("code"), "e2e_run_id": e2e_run_id}

    if logs is None:
        sm.transition("blocked", detail={"reason": "setup_logs_not_mounted"})
        _finalize_terminal(logs=Path("/tmp"), run_control=run_control, e2e_run_id=e2e_run_id, final_status="blocked")
        return {"feature": FEATURE_ID_UNATTENDED, "status": "blocked", "code": "setup_logs_not_mounted", "e2e_run_id": e2e_run_id}
    sm.transition("setup_logs_ready")

    destructive_cfg = load_destructive_lab_config(run_control)
    if destructive_cfg:
        return _run_destructive_lab_path(
            logs=logs,
            repo=repo,
            run_control=run_control or {},
            e2e_run_id=e2e_run_id,
            correlation_id=correlation_id,
            journal_dir=journal_dir,
            sm=sm,
            started=started,
            target_bytes=target_bytes,
            create_data_script=create_data_script,
        )

    candidates = _collect_external_candidates()
    valid, ambiguity = discover_registered_test_targets(candidates)
    if ambiguity:
        sm.transition("blocked", detail=ambiguity)
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status="blocked")
        return {"feature": FEATURE_ID_UNATTENDED, "status": "blocked", "code": ambiguity.get("code"), "e2e_run_id": e2e_run_id}

    if not valid:
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
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status=result["status"])
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
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status="failed")
        return {"feature": FEATURE_ID_UNATTENDED, "status": "failed", "error": "create_e2e_test_data_script_missing", "e2e_run_id": e2e_run_id}

    try:
        create_test_data(paths["source"], repo_root=repo, target_bytes=target_bytes)
    except Exception as exc:  # noqa: BLE001
        sm.transition("failed", detail={"error": str(exc)})
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status="failed")
        return {"feature": FEATURE_ID_UNATTENDED, "status": "failed", "error": "test_data_creation_failed", "e2e_run_id": e2e_run_id}
    sm.transition("test_data_ready")

    token = _resolve_token()
    telemetry_required = bool((run_control or {}).get("telemetry_required"))
    if telemetry_required and not token:
        sm.transition("blocked", detail={"reason": "live_telemetry_token_unavailable"})
        _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status="blocked")
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

    _finalize_terminal(logs=logs, run_control=run_control, e2e_run_id=e2e_run_id, final_status=final_status)
    return auto_result


def is_physical_e2e_success_status(status: str | None) -> bool:
    if not status:
        return False
    return status in PHYSICAL_SUCCESS_STATUSES or str(status).startswith("physical_rescue")
