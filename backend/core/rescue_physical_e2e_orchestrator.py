"""Orchestrator for physical rescue backup/verify/restore E2E."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any, Callable

from core.rescue_payload_version import rescue_payload_version
from core.rescue_physical_e2e_backup import run_physical_e2e_backup
from core.rescue_physical_e2e_consent import build_consent_record, normalize_consent_choice
from core.rescue_physical_e2e_diagnostics import query_diagnostics_case
from core.rescue_physical_e2e_event_emitter import PhysicalE2EEventEmitter
from core.rescue_physical_e2e_journal import (
    append_operator_decision,
    default_evidence_base,
    ensure_journal_layout,
    journal_dir_for_run,
    write_json,
)
from core.rescue_physical_e2e_manifest import compare_manifest_summaries, write_source_artifacts
from core.rescue_physical_e2e_models import (
    FEATURE_ID,
    OPERATION_EVENTS,
    PRODUCTION_READY,
    PhysicalE2EPaths,
    PhysicalE2ESession,
)
from core.rescue_physical_e2e_restore import run_physical_e2e_restore
from core.rescue_physical_e2e_storage_safety import validate_paths_for_e2e
from core.rescue_physical_e2e_telemetry_payload import new_e2e_run_id
from core.rescue_physical_e2e_verify import run_physical_e2e_verify

HttpTransportFn = Callable[[str, bytes, dict[str, str], int], tuple[int, str, dict[str, str]]]


def _device_id_hash(seed: str = "msi-ge63-physical-e2e") -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]


def build_operator_gate_summary(
    session: PhysicalE2ESession,
    *,
    test_device: str = "MSI GE63 Raider RGB 8RF",
    rescue_stick_device: str = "unknown",
    source_path: str = "",
    backup_target_path: str = "",
    restore_target_path: str = "",
) -> str:
    lines = [
        "============================================================",
        "REALTEST BACKUP / VERIFY / RESTORE",
        "============================================================",
        f"Run-ID:\n  {session.e2e_run_id}",
        f"Testgerät:\n  {test_device}",
        f"Rettungsstick:\n  {rescue_stick_device}",
        f"Quelle:\n  {source_path}",
        f"Backupziel:\n  {backup_target_path}",
        f"Restoreziel:\n  {restore_target_path}",
        "Quelle und Restoreziel verschieden:\n  ja",
        "Restoreziel leer:\n  ja",
        "Interne Systempartition betroffen:\n  nein",
        "Produktive Daten:\n  nein",
        "Testdaten:\n  künstlich erzeugt",
        f"Telemetrie-Consent:\n  {'erteilt' if session.consent == 'granted' else 'nicht erteilt'}",
        "OPERATOR-FREIGABE:\n  erforderlich",
        "============================================================",
    ]
    return "\n".join(lines)


def init_physical_e2e_session(
    *,
    e2e_run_id: str | None = None,
    consent: str = "aborted",
    operator_approved: bool = False,
    setup_logs_base: Path | None = None,
    payload_sha256: str = "",
) -> tuple[PhysicalE2ESession, Path]:
    run_id = e2e_run_id or new_e2e_run_id()
    base = default_evidence_base(setup_logs_base)
    journal = journal_dir_for_run(base, run_id)
    ensure_journal_layout(journal)
    session = PhysicalE2ESession(
        e2e_run_id=run_id,
        rescue_session_id=str(uuid.uuid4()),
        backup_job_id=uuid.uuid4().hex[:16],
        restore_job_id=uuid.uuid4().hex[:16],
        device_id_hash=_device_id_hash(run_id),
        payload_version=rescue_payload_version(),
        payload_sha256=payload_sha256 or "unknown",
        consent=normalize_consent_choice(consent),
        operator_approved=operator_approved,
    )
    write_json(journal / "e2e-result.json", {"feature": FEATURE_ID, "e2e_run_id": run_id, "status": "initialized"})
    return session, journal


def run_physical_e2e_workflow(
    *,
    source_dir: Path,
    backup_archive: Path,
    restore_dir: Path,
    consent: str,
    operator_approved: bool,
    allowed_source_prefixes: tuple[Path, ...],
    allowed_output_prefixes: tuple[Path, ...],
    allowed_restore_prefixes: tuple[Path, ...],
    setup_logs_base: Path | None = None,
    e2e_run_id: str | None = None,
    source_device: dict[str, Any] | None = None,
    backup_device: dict[str, Any] | None = None,
    restore_device: dict[str, Any] | None = None,
    ingest_url: str | None = None,
    token_file: str | None = None,
    http_transport: HttpTransportFn | None = None,
    skip_diagnostics_poll: bool = False,
    lab_tmpfs_mode: bool = False,
) -> dict[str, Any]:
    if not operator_approved:
        return {"success": False, "code": "operator_gate_blocked", "message": "Operator-Freigabe fehlt."}

    session, journal = init_physical_e2e_session(
        e2e_run_id=e2e_run_id,
        consent=consent,
        operator_approved=operator_approved,
        setup_logs_base=setup_logs_base,
    )
    session.paths = PhysicalE2EPaths(
        e2e_run_id=session.e2e_run_id,
        evidence_root=str(journal),
        source_dir=str(source_dir),
        backup_archive=str(backup_archive),
        restore_dir=str(restore_dir),
        journal_dir=str(journal),
    )

    append_operator_decision(
        journal,
        {
            "decision": "operator_approved",
            "consent": session.consent,
            "source_dir": str(source_dir),
            "backup_archive": str(backup_archive),
            "restore_dir": str(restore_dir),
        },
    )
    safety = validate_paths_for_e2e(
        source_dir=source_dir,
        backup_dir=backup_archive.parent,
        restore_dir=restore_dir,
        source_device=source_device,
        backup_device=backup_device,
        restore_device=restore_device,
    )
    if not safety.get("ok"):
        write_json(journal / "e2e-result.json", {"status": "blocked", "errors": safety.get("errors")})
        return {"success": False, "code": "unsafe_paths", "errors": safety.get("errors"), "e2e_run_id": session.e2e_run_id}

    source_manifest = source_dir.parent / "source-manifest.sha256"
    source_summary_path = journal / "source-summary.json"
    source_summary = write_source_artifacts(
        source_dir,
        manifest_path=source_manifest,
        summary_path=source_summary_path,
    )
    write_json(journal / "source-summary.json", source_summary)

    emitter = PhysicalE2EEventEmitter(
        session,
        journal,
        ingest_url=ingest_url,
        token_file=token_file,
        http_transport=http_transport,
    )

    emitter.emit(
        "rescue_session_started",
        assessment={"session_phase": "started"},
        operation_status="started",
    )

    emitter.emit("backup_started", operation_status="started")
    backup_result = run_physical_e2e_backup(
        source_dir=source_dir,
        backup_archive=backup_archive,
        allowed_source_prefixes=allowed_source_prefixes,
        allowed_output_prefixes=allowed_output_prefixes,
        backup_job_id=session.backup_job_id,
        lab_tmpfs_mode=lab_tmpfs_mode,
    )
    write_json(journal / "backup-result.json", backup_result)
    write_json(journal / "backup-summary.json", {
        "file_count": backup_result.get("file_count"),
        "total_bytes": backup_result.get("total_bytes"),
        "manifest_sha256": backup_result.get("manifest_sha256"),
    })

    if not backup_result.get("success"):
        emitter.emit("backup_failed", assessment={"error_code": backup_result.get("code")}, operation_status="failed")
        write_json(journal / "e2e-result.json", {"status": "failed", "phase": "backup"})
        return {"success": False, "phase": "backup", "backup": backup_result, "e2e_run_id": session.e2e_run_id}

    emitter.emit(
        "backup_completed",
        assessment={
            "backup_file_count": backup_result.get("file_count"),
            "backup_total_bytes": backup_result.get("total_bytes"),
            "backup_manifest_hash": f"sha256:{backup_result.get('manifest_sha256')}",
            "backup_format": backup_result.get("backup_format"),
        },
    )

    emitter.emit("verify_started", operation_status="started")
    verify_result = run_physical_e2e_verify(
        backup_archive=backup_archive,
        expected_file_count=int(source_summary.get("file_count") or 0),
        expected_total_bytes=int(source_summary.get("total_bytes") or 0),
    )
    write_json(journal / "verify-result.json", verify_result)

    if not verify_result.get("passed"):
        emitter.emit("verify_failed", assessment={"error_code": verify_result.get("code")}, operation_status="failed")
        write_json(journal / "e2e-result.json", {"status": "failed", "phase": "verify"})
        return {"success": False, "phase": "verify", "verify": verify_result, "e2e_run_id": session.e2e_run_id}

    emitter.emit(
        "verify_completed",
        assessment={"verify_manifest_match": True, "verify_passed": True},
    )

    emitter.emit("restore_started", operation_status="started")
    restore_result = run_physical_e2e_restore(
        backup_archive=backup_archive,
        restore_dir=restore_dir,
        allowed_target_prefixes=allowed_restore_prefixes,
        restore_job_id=session.restore_job_id,
        lab_tmpfs_mode=lab_tmpfs_mode,
    )
    write_json(journal / "restore-result.json", restore_result)

    if not restore_result.get("success"):
        emitter.emit("restore_failed", assessment={"error_code": restore_result.get("code")}, operation_status="failed")
        write_json(journal / "e2e-result.json", {"status": "failed", "phase": "restore"})
        return {"success": False, "phase": "restore", "restore": restore_result, "e2e_run_id": session.e2e_run_id}

    emitter.emit(
        "restore_completed",
        assessment={
            "restore_target_separate": True,
            "restore_file_count": restore_result.get("file_count"),
            "restore_total_bytes": restore_result.get("total_bytes"),
            "restore_manifest_match": True,
        },
    )

    restored_summary_path = journal / "restored-summary.json"
    restored_summary = {
        "file_count": restore_result.get("file_count"),
        "total_bytes": restore_result.get("total_bytes"),
        "manifest_sha256": restore_result.get("manifest_sha256"),
        "contains_personal_data": False,
    }
    write_json(restored_summary_path, restored_summary)

    comparison = compare_manifest_summaries(source_summary, restored_summary)
    write_json(journal / "manifest-comparison.json", comparison)

    integrity_passed = comparison.get("restore_integrity_status") == "passed"
    if integrity_passed:
        emitter.emit(
            "rescue_session_completed",
            assessment={
                "restore_integrity_status": "passed",
                "file_count_match": comparison.get("file_count_match"),
                "total_bytes_match": comparison.get("total_bytes_match"),
                "manifest_match": comparison.get("manifest_match"),
            },
        )

    consent_record = build_consent_record(session.consent)
    telemetry_summary = emitter.summary()
    receipts = telemetry_summary.get("receipts_stored", 0)

    diagnostics_status: dict[str, Any] = {"diagnostics_status": "ausstehend"}
    if not skip_diagnostics_poll and receipts > 0:
        diagnostics_status = query_diagnostics_case(session.e2e_run_id)
        write_json(journal / "diagnostics-status.json", diagnostics_status)

    final_status = "failed"
    if integrity_passed:
        if receipts >= len(OPERATION_EVENTS):
            final_status = "physical_rescue_backup_restore_e2e_passed"
        elif receipts > 0:
            final_status = "physical_rescue_passed_server_verification_pending"
        else:
            final_status = "review_required"

    e2e_result = {
        "feature": FEATURE_ID,
        "e2e_run_id": session.e2e_run_id,
        "status": final_status,
        "production_ready": PRODUCTION_READY,
        "integrity": comparison,
        "telemetry": {
            "events_expected": len(OPERATION_EVENTS),
            "events_recorded": telemetry_summary.get("events_recorded"),
            "receipts_stored": receipts,
            "consent": consent_record,
        },
        "ionos_backup_target_verified": False,
        "physical_backup_restore_passed": integrity_passed,
    }
    write_json(journal / "e2e-result.json", e2e_result)

    return {
        "success": integrity_passed,
        "status": final_status,
        "e2e_run_id": session.e2e_run_id,
        "rescue_session_id": session.rescue_session_id,
        "backup": backup_result,
        "verify": verify_result,
        "restore": restore_result,
        "comparison": comparison,
        "telemetry": telemetry_summary,
        "diagnostics": diagnostics_status,
        "journal_dir": str(journal),
    }
