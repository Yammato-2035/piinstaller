from __future__ import annotations

from typing import Any


def _seq(runbook_id: str, order: int, *, requires_root: bool, requires_test_media: bool) -> dict[str, Any]:
    return {
        "runbook_id": runbook_id,
        "order": int(order),
        "manual_operator_required": True,
        "auto_allowed": False,
        "requires_root": bool(requires_root),
        "requires_test_media": bool(requires_test_media),
        "required_before_next": True,
    }


def _ack(text: str) -> dict[str, Any]:
    return {"text": text, "must_acknowledge": True, "auto_allowed": False}


def _runbook(
    runbook_id: str,
    source_gap: str,
    summary: str,
    required_inputs: list[str],
    manual_steps: list[str],
    expected_evidence: list[str],
    stop_conditions: list[str],
    rollback_or_cleanup: list[str],
    pass_criteria: list[str],
    fail_criteria: list[str],
) -> dict[str, Any]:
    return {
        "runbook_id": runbook_id,
        "source_gap": source_gap,
        "summary": summary,
        "required_inputs": required_inputs,
        "manual_steps": manual_steps,
        "expected_evidence": expected_evidence,
        "stop_conditions": stop_conditions,
        "rollback_or_cleanup": rollback_or_cleanup,
        "pass_criteria": pass_criteria,
        "fail_criteria": fail_criteria,
    }


def build_runner_runtime_runbook_bundle() -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    runbook_sequence = [
        _seq("RUNBOOK_SUDOERS_RUNTIME_DRYRUN", 1, requires_root=True, requires_test_media=False),
        _seq("RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN", 2, requires_root=True, requires_test_media=False),
        _seq("RUNBOOK_REAL_WRITE_HARDWARE_E2E", 3, requires_root=True, requires_test_media=True),
        _seq("RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E", 4, requires_root=True, requires_test_media=True),
        _seq("RUNBOOK_DEVICE_REENUMERATION", 5, requires_root=False, requires_test_media=True),
        _seq("RUNBOOK_HOTPLUG_UNMOUNT_RACE", 6, requires_root=False, requires_test_media=True),
        _seq("RUNBOOK_ROLLBACK_RUNTIME", 7, requires_root=False, requires_test_media=True),
    ]

    global_preconditions = [
        {"code": "GLOBAL_PRECONDITION_FULL_BACKUP", "auto_allowed": False},
        {"code": "GLOBAL_PRECONDITION_LOCAL_HOST_ACCESS", "auto_allowed": False},
        {"code": "GLOBAL_PRECONDITION_SINGLE_DISPOSABLE_MEDIA", "auto_allowed": False},
        {"code": "GLOBAL_PRECONDITION_MEDIA_LABELED", "auto_allowed": False},
        {"code": "GLOBAL_PRECONDITION_NO_PRODUCTIVE_REMOVABLE_MEDIA", "auto_allowed": False},
        {"code": "GLOBAL_PRECONDITION_SECOND_CONTROL_TERMINAL", "auto_allowed": False},
        {"code": "GLOBAL_PRECONDITION_STABLE_POWER", "auto_allowed": False},
        {"code": "GLOBAL_PRECONDITION_OPERATOR_READ_ABORT_CRITERIA", "auto_allowed": False},
        {"code": "GLOBAL_PRECONDITION_ALL_TEST_DESIGNS_PRESENT", "auto_allowed": False},
        {"code": "GLOBAL_PRECONDITION_LAB_STATUS_TEST_DESIGN_READY", "auto_allowed": False},
    ]

    global_stop_conditions = [
        "operator_unsure",
        "multiple_possible_removable_media",
        "systemdisk_as_target",
        "test_media_not_unique",
        "unexpected_mount_change",
        "unexpected_device_change",
        "audit_missing",
        "lock_not_released",
        "verify_mismatch",
        "runner_stdout_not_json",
        "blocked_environment_variable_detected",
    ]

    global_evidence_requirements = [
        "per_runbook_result_file",
        "lsblk_before_after",
        "findmnt_before_after",
        "mount_before_after",
        "runner_stdout_json",
        "runner_stderr",
        "audit_jsonl",
        "jobfile_hash",
        "snapshot_fingerprint",
        "sha256_verify_for_write_tests",
        "root_su_evidence_for_dryrun_checks",
        "proof_no_internal_drive_touched",
        "proof_no_untracked_mount_change",
    ]

    operator_checklist = [
        _ack("Ich habe ein vollstaendiges Backup"),
        _ack("Ich erkenne das Testmedium physisch eindeutig"),
        _ack("Ich habe produktive Wechselmedien entfernt"),
        _ack("Ich fuehre keine Tests remote ohne lokale Kontrolle aus"),
        _ack("Ich breche bei Unsicherheit ab"),
        _ack("Ich bestaetige, dass Testmedium ueberschrieben werden darf"),
        _ack("Ich fuehre nur einen Runbook-Schritt zur Zeit aus"),
        _ack("Ich fuehre keine automatischen Retries aus"),
    ]

    common_stops = ["operator_unsure", "audit_missing", "lock_not_released"]
    per_runbook = [
        _runbook(
            "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
            "RUNNER_GAP_SUDOERS_RUNTIME_OPEN",
            "Manuelle Runtime-Policy-Pruefung im Dry-run ohne echten Write.",
            ["sudoers_runtime_test_plan", "install_validator", "consistency_report"],
            ["temporary_snippet_prepare", "manual_policy_check", "dryrun_invocation", "audit_review"],
            ["sudoers_snippet_text", "runner_stdout_json", "audit_jsonl"],
            common_stops + ["runner_stdout_not_json"],
            ["remove_temp_snippet", "archive_audit"],
            ["unsafe_patterns_blocked", "dryrun_only_confirmed"],
            ["unexpected_prompt", "env_injection_detected"],
        ),
        _runbook(
            "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN",
            "RUNNER_GAP_PRIVILEGED_RUNNER_VALIDATION_OPEN",
            "Privileggrenzen im Dry-run validieren inklusive UID/GID und Lock-Lifecycle.",
            ["privileged_validation_test_plan", "permission_boundary", "sandbox_policy"],
            ["create_valid_job", "document_hash", "manual_dryrun_start", "verify_uid_gid", "verify_lock_release"],
            ["effective_uid_gid", "runner_stdout_json", "lifecycle_audit_jsonl"],
            common_stops + ["device_open_detected"],
            ["delete_test_job", "cleanup_stale_lock_if_present"],
            ["dryrun_enforced", "no_device_open"],
            ["hash_mismatch", "parallel_runner_conflict"],
        ),
        _runbook(
            "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
            "RUNNER_GAP_REAL_WRITE_HARDWARE_E2E_OPEN",
            "Erster manueller Hardware-E2E-Lauf auf Wegwerfmedium mit Verify-Pflicht.",
            ["real_write_hw_e2e_test_plan", "hardware_gate_report", "real_write_guard_report"],
            ["identify_media", "capture_pre_state", "confirm_gate_ready", "manual_real_write_step", "verify_sha256", "capture_post_state"],
            ["bytes_written", "expected_sha256", "actual_sha256", "verify_status"],
            common_stops + ["verify_mismatch", "systemdisk_as_target"],
            ["delete_test_job", "mark_media_overwritten"],
            ["verify_success", "no_internal_drive_touched"],
            ["verify_mismatch", "unexpected_mount_change"],
        ),
        _runbook(
            "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
            "RUNNER_GAP_FAILURE_INJECTION_HW_OPEN",
            "Failure-Cases einzeln gegen Hardwarepfad und Cleanup-Verhalten auswerten.",
            ["failure_injection_hw_test_plan", "failure_hooks", "hardware_gate_report"],
            ["confirm_happy_path", "run_case_individually", "document_abort_code", "validate_cleanup_state"],
            ["failure_case_code", "expected_abort_code", "actual_abort_code", "audit_jsonl"],
            common_stops + ["verify_mismatch_unexplained"],
            ["cleanup_case_artifacts", "reassess_state"],
            ["case_fail_closed", "no_retry_performed"],
            ["stale_lock_unresolved", "unexpected_device_change"],
        ),
        _runbook(
            "RUNBOOK_DEVICE_REENUMERATION",
            "RUNNER_GAP_DEVICE_REENUMERATION_OPEN",
            "Pfad-/Identitaetswechsel robust erkennen und fail-closed behandeln.",
            ["device_reenumeration_test_plan", "snapshot_fingerprint_logic"],
            ["capture_baseline", "run_case_individually", "compare_realpath_and_fingerprint", "document_result"],
            ["target_device_before_after", "realpath_before_after", "fingerprint_before_after"],
            common_stops + ["other_media_on_old_path"],
            ["reidentify_media", "require_new_gate_check"],
            ["identity_consistency_enforced"],
            ["ambiguous_media_identity", "device_change_retry_attempted"],
        ),
        _runbook(
            "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
            "RUNNER_GAP_HOTPLUG_RACE_OPEN",
            "Race-Trigger gegen Guard/Lifecycle mit klaren Abort-/Block-Codes validieren.",
            ["hotplug_race_test_plan", "device_reenumeration_test_plan"],
            ["document_trigger_point", "run_case_individually", "record_abort_code", "verify_lock_cleanup"],
            ["trigger_point", "expected_abort_code", "actual_abort_code", "lock_cleanup_proof"],
            common_stops + ["internal_drive_becomes_target"],
            ["cleanup_stale_lock_if_present", "mark_media_state"],
            ["race_case_handled_fail_closed"],
            ["retry_after_race_abort", "unexpected_mount_state"],
        ),
        _runbook(
            "RUNBOOK_ROLLBACK_RUNTIME",
            "RUNNER_GAP_ROLLBACK_RUNTIME_OPEN",
            "Rollback-Cleanup strikt auf Testartefakte begrenzen und Audit-Erhalt sicherstellen.",
            ["rollback_runtime_test_plan", "install_consistency", "rollback_manifest"],
            ["define_allowed_cleanup_paths", "run_case_individually", "verify_no_system_path_change", "archive_audit"],
            ["allowed_cleanup_paths", "forbidden_cleanup_paths", "audit_jsonl_before_after"],
            common_stops + ["cleanup_path_points_to_system_or_root"],
            ["remove_test_artifacts_only", "reassess_cleanup_boundaries"],
            ["no_system_paths_touched", "audit_preserved"],
            ["symlink_cleanup_path_detected", "recursive_cleanup_without_prefix"],
        ),
    ]

    if len(runbook_sequence) != 7:
        errors.append("runbook_sequence_incomplete")
    if len(per_runbook) != 7:
        errors.append("per_runbook_incomplete")

    bundle_status = "ok"
    if errors:
        bundle_status = "blocked"
    elif warnings:
        bundle_status = "review_required"

    return {
        "bundle_status": bundle_status,
        "bundle_id": "RUNNER_RUNTIME_RUNBOOK_BUNDLE_V1",
        "runbook_sequence": runbook_sequence,
        "global_preconditions": global_preconditions,
        "global_stop_conditions": global_stop_conditions,
        "global_evidence_requirements": global_evidence_requirements,
        "operator_checklist": operator_checklist,
        "per_runbook": per_runbook,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
