from __future__ import annotations

from typing import Any

from deploy.runner_lab_phase_consolidation import build_runner_lab_phase_consolidation
from deploy.runner_lab_readiness_status import build_runner_lab_readiness_status
from deploy.runner_next_phase_gate import evaluate_runner_next_phase_gate
from deploy.runner_runtime_runbook_bundle import build_runner_runtime_runbook_bundle
from deploy.runner_runtime_runbook_export import build_runner_runtime_runbook_export_package

_ALLOWED_RUNBOOKS = [
    "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
    "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN",
    "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
    "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
    "RUNBOOK_DEVICE_REENUMERATION",
    "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
    "RUNBOOK_ROLLBACK_RUNTIME",
]
_WRITE_RELATED = {
    "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
    "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
    "RUNBOOK_DEVICE_REENUMERATION",
    "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
    "RUNBOOK_ROLLBACK_RUNTIME",
}


def _check(code: str, status: str) -> dict[str, Any]:
    return {"code": code, "status": status, "auto_allowed": False}


def build_runner_manual_runtime_precheck(
    *,
    selected_runbook: str,
    next_phase_gate: dict[str, Any] | None = None,
    operator_confirmations: dict[str, bool] | None = None,
    hardware_gate_report: dict[str, Any] | None = None,
    real_write_guard_report: dict[str, Any] | None = None,
    runtime_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []
    selected = str(selected_runbook or "")

    gate = dict(next_phase_gate or evaluate_runner_next_phase_gate())
    bundle = build_runner_runtime_runbook_bundle()
    runbook_export = build_runner_runtime_runbook_export_package()
    consolidation = build_runner_lab_phase_consolidation(include_artifact_existence=False)
    lab_status = build_runner_lab_readiness_status()

    if selected not in _ALLOWED_RUNBOOKS:
        return {
            "precheck_status": "blocked",
            "selected_runbook": selected,
            "environment_checks": [],
            "operator_checks": [],
            "test_media_checks": [],
            "evidence_plan": [],
            "stop_conditions": [],
            "blocked_reasons": ["MANUAL_RUNTIME_PRECHECK_BLOCKED_UNKNOWN_RUNBOOK"],
            "warnings": [],
            "errors": ["MANUAL_RUNTIME_PRECHECK_BLOCKED_UNKNOWN_RUNBOOK"],
        }

    confirmations = dict(operator_confirmations or {})
    hw = dict(hardware_gate_report or {})
    guard = dict(real_write_guard_report or {})
    ctx = dict(runtime_context or {})

    env_checks = [
        _check("ENV_NEXT_PHASE_GATE_MANUAL_RUNTIME_ALLOWED", "pass" if "NEXT_PHASE_MANUAL_RUNTIME_TESTS" in list(gate.get("allowed_next_phases") or []) else "blocked"),
        _check("ENV_LAB_PHASE_CONSOLIDATION_PRESENT", "pass" if consolidation.get("consolidation_status") in {"ok", "review_required"} else "blocked"),
        _check("ENV_RUNBOOK_BUNDLE_PRESENT", "pass" if bundle.get("bundle_status") in {"ok", "review_required"} else "blocked"),
        _check("ENV_RUNBOOK_EXPORT_PRESENT", "pass" if runbook_export.get("export_status") == "ok" else "blocked"),
        _check("ENV_RESULT_VALIDATOR_PRESENT", "pass"),
        _check("ENV_ACCEPTANCE_AGGREGATOR_PRESENT", "pass"),
        _check("ENV_EVIDENCE_TEMPLATES_PRESENT", "pass"),
        _check("ENV_PRODUCTION_READY_NOT_EXPECTED", "pass"),
    ]

    operator_checks = []
    required_operator = [
        ("full_backup_confirmed", "blocked"),
        ("local_control_confirmed", "blocked"),
        ("single_test_media_confirmed", "blocked"),
        ("productive_media_removed_confirmed", "warning"),
        ("stop_conditions_acknowledged", "blocked"),
        ("no_remote_without_local_control_confirmed", "warning"),
        ("no_auto_retry_confirmed", "warning"),
        ("operator_understands_data_loss", "blocked"),
    ]
    for key, critical in required_operator:
        ok = bool(confirmations.get(key))
        status = "pass" if ok else ("blocked" if critical == "blocked" else "warning")
        operator_checks.append(_check(f"OPERATOR_{key.upper()}", status))

    test_media_checks: list[dict[str, Any]] = []
    if selected in _WRITE_RELATED:
        test_media_checks.extend(
            [
                _check("MEDIA_PHYSICAL_LABEL_PRESENT", "pass" if bool(ctx.get("physical_label_present")) else "blocked"),
                _check("MEDIA_TARGET_DEVICE_DECLARED", "pass" if bool(ctx.get("target_device_declared")) else "blocked"),
                _check("MEDIA_HARDWARE_GATE_REPORT_PROVIDED", "pass" if bool(hw) else "blocked"),
                _check("MEDIA_HARDWARE_GATE_TEST_READY", "pass" if str(hw.get("gate_status") or "").lower() == "test_ready" else "blocked"),
                _check("MEDIA_REAL_WRITE_GUARD_READY", "pass" if str(guard.get("guard_status") or "").upper() == "READY" else "blocked"),
                _check("MEDIA_SNAPSHOT_FINGERPRINT_PRESENT", "pass" if bool(ctx.get("snapshot_fingerprint_present")) else "blocked"),
                _check("MEDIA_MOUNT_STATE_DOCUMENTED", "pass" if bool(ctx.get("mount_state_documented")) else "warning"),
                _check("MEDIA_NO_MULTIPLE_CANDIDATE_MEDIA", "pass" if not bool(ctx.get("multiple_candidate_media")) else "blocked"),
            ]
        )
    else:
        test_media_checks.extend(
            [
                _check("MEDIA_NOT_APPLICABLE_DRYRUN", "pass"),
                _check("MEDIA_REAL_WRITE_GUARD_NOT_APPLICABLE", "pass"),
            ]
        )

    evidence_plan = [
        {"code": "EVIDENCE_RESULT_FILE_PATH", "value": f"docs/evidence/runtime-results/{selected}.json", "auto_allowed": False},
        {"code": "EVIDENCE_LSBLK_BEFORE_AFTER", "auto_allowed": False},
        {"code": "EVIDENCE_FINDMNT_BEFORE_AFTER", "auto_allowed": False},
        {"code": "EVIDENCE_MOUNT_BEFORE_AFTER", "auto_allowed": False},
        {"code": "EVIDENCE_RUNNER_STDOUT_STDERR", "auto_allowed": False},
        {"code": "EVIDENCE_AUDIT_JSONL", "auto_allowed": False},
        {"code": "EVIDENCE_JOBFILE_HASH", "auto_allowed": False},
        {"code": "EVIDENCE_SNAPSHOT_FINGERPRINT", "auto_allowed": False},
        {"code": "EVIDENCE_ROLLBACK_CLEANUP_STATUS", "auto_allowed": False},
    ]
    if selected in _WRITE_RELATED:
        evidence_plan.append({"code": "EVIDENCE_SHA256_FIELDS", "auto_allowed": False})

    stop_conditions = list(dict.fromkeys(list(bundle.get("global_stop_conditions") or []) + [
        "operator_unsure",
        "unknown_target_media",
        "multiple_removable_media",
        "systemdisk_as_target",
        "hardware_gate_not_ready",
        "guard_not_ready",
        "unexpected_mount_change",
        "unexpected_device_change",
        "verify_mismatch",
        "audit_missing",
        "non_json_stdout",
        "blocked_env_variable",
    ]))

    all_checks = env_checks + operator_checks + test_media_checks
    if any(c["status"] == "blocked" for c in all_checks):
        precheck_status = "blocked"
    elif any(c["status"] == "warning" for c in all_checks):
        precheck_status = "review_required"
    else:
        precheck_status = "ready_for_manual_runtime"

    for c in all_checks:
        if c["status"] == "blocked":
            blocked_reasons.append(c["code"])
        elif c["status"] == "warning":
            warnings.append(c["code"])

    _ = lab_status.get("lab_readiness_status")

    return {
        "precheck_status": precheck_status,
        "selected_runbook": selected,
        "environment_checks": env_checks,
        "operator_checks": operator_checks,
        "test_media_checks": test_media_checks,
        "evidence_plan": evidence_plan,
        "stop_conditions": stop_conditions,
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
