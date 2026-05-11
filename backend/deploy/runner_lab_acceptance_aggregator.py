from __future__ import annotations

from typing import Any

from deploy.runner_lab_readiness_status import build_runner_lab_readiness_status
from deploy.runner_release_readiness import build_runner_release_readiness_matrix
from deploy.runner_runtime_runbook_bundle import build_runner_runtime_runbook_bundle

_REQUIRED_RUNBOOKS = [
    "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
    "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN",
    "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
    "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
    "RUNBOOK_DEVICE_REENUMERATION",
    "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
    "RUNBOOK_ROLLBACK_RUNTIME",
]
_BLOCKING_FINDINGS = {
    "RESULT_SCHEMA_MISSING_FIELD",
    "RESULT_JSON_INVALID",
    "RESULT_PATH_OUTSIDE_ALLOWED_ROOT",
    "RESULT_SYMLINK_BLOCKED",
    "RESULT_SEQUENCE_OUT_OF_ORDER",
    "RESULT_PREVIOUS_RUNBOOK_FAILED",
    "RESULT_EVIDENCE_MISSING",
    "RESULT_VERIFY_MISMATCH",
    "RESULT_INTERNAL_DRIVE_TOUCHED",
    "RESULT_UNTRACKED_MOUNT_CHANGE",
    "RESULT_ROLLBACK_INCOMPLETE",
}
_RESIDUAL_RISKS = [
    "LAB_RISK_FIRST_HARDWARE_SCOPE_LIMITED",
    "LAB_RISK_SINGLE_HOST_ONLY",
    "LAB_RISK_LIMITED_MEDIA_TYPES",
    "LAB_RISK_OPERATOR_DEPENDENT",
    "LAB_RISK_NOT_PRODUCTION_READY",
]


def _runbook_status_for(result: dict[str, Any]) -> tuple[str, bool]:
    pass_fail = str((result or {}).get("pass_fail") or "")
    if pass_fail == "pass":
        return "pass", False
    if pass_fail == "fail":
        return "failed", False
    return "repeat_required", True


def build_runner_lab_acceptance_summary(
    *,
    validated_runtime_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validated = dict(validated_runtime_results or {})
    warnings: list[str] = []
    errors: list[str] = []

    validator_status = str(validated.get("validation_status") or "blocked")
    validator_findings = list(validated.get("blocking_findings") or [])
    validator_results = list(validated.get("runbook_results") or [])
    acceptance_check = dict(validated.get("acceptance_check") or {})
    requested_decision = str(acceptance_check.get("accepted_decision") or "blocked")

    runbook_by_id: dict[str, dict[str, Any]] = {}
    for item in validator_results:
        if not isinstance(item, dict):
            continue
        rb = str(((item.get("result") or {}).get("runbook_id")) or "")
        if rb:
            runbook_by_id[rb] = item

    runbook_outcomes: list[dict[str, Any]] = []
    required_repeats: list[str] = []
    pass_count = 0
    failed_count = 0
    repeat_required_count = 0
    evidence_complete_count = 0
    evidence_partial_count = 0
    evidence_missing_count = 0

    for runbook_id in _REQUIRED_RUNBOOKS:
        item = runbook_by_id.get(runbook_id)
        notes: list[str] = []
        if item is None:
            status = "missing"
            evidence_status = "missing"
            safety_status = "blocked"
            required_repeat = True
            notes.append("runbook_result_missing")
            evidence_missing_count += 1
            required_repeats.append(runbook_id)
        else:
            result = dict(item.get("result") or {})
            findings = set(item.get("blocking_findings") or [])
            status, required_repeat = _runbook_status_for(result)

            if "RESULT_EVIDENCE_MISSING" in findings:
                if status == "pass":
                    evidence_status = "partial"
                    evidence_partial_count += 1
                else:
                    evidence_status = "missing"
                    evidence_missing_count += 1
                if status != "failed":
                    status = "repeat_required"
                    required_repeat = True
            else:
                evidence_status = "complete"
                evidence_complete_count += 1

            if findings.intersection(_BLOCKING_FINDINGS):
                safety_status = "blocked"
            elif evidence_status == "partial":
                safety_status = "warning"
            else:
                safety_status = "ok"
            for finding in sorted(findings):
                notes.append(f"finding:{finding}")

            if status == "pass":
                pass_count += 1
            elif status == "failed":
                failed_count += 1
            else:
                repeat_required_count += 1
                required_repeats.append(runbook_id)

        runbook_outcomes.append(
            {
                "runbook_id": runbook_id,
                "status": status,
                "evidence_status": evidence_status,
                "safety_status": safety_status,
                "required_repeat": bool(required_repeat),
                "notes": notes,
            }
        )

    invalid_files = 0
    for item in validator_results:
        if not bool((item or {}).get("ok")):
            invalid_files += 1
    total_files = len(list(validated.get("result_files") or []))
    valid_files = max(0, total_files - invalid_files)
    missing_runbooks = [rb for rb in _REQUIRED_RUNBOOKS if rb not in runbook_by_id]

    evidence_summary = {
        "total_files": total_files,
        "valid_files": valid_files,
        "invalid_files": invalid_files,
        "missing_runbooks": missing_runbooks,
        "pass_count": pass_count,
        "failed_count": failed_count,
        "repeat_required_count": repeat_required_count + len(missing_runbooks),
        "evidence_complete_count": evidence_complete_count,
        "evidence_partial_count": evidence_partial_count,
        "evidence_missing_count": evidence_missing_count + len(missing_runbooks),
    }

    release = build_runner_release_readiness_matrix()
    lab_status = build_runner_lab_readiness_status()
    bundle = build_runner_runtime_runbook_bundle()
    runtime_summary = {
        "validator_status": validator_status,
        "required_runbook_count": len(_REQUIRED_RUNBOOKS),
        "validated_runbook_count": len(runbook_by_id),
        "runtime_bundle_id": bundle.get("bundle_id"),
        "lab_readiness_status": lab_status.get("lab_readiness_status"),
        "release_readiness_status": release.get("readiness_status"),
    }

    blocking_findings = list(dict.fromkeys(validator_findings))
    for outcome in runbook_outcomes:
        if outcome["status"] == "failed":
            blocking_findings.append("RESULT_PREVIOUS_RUNBOOK_FAILED")
        if outcome["status"] == "missing":
            blocking_findings.append("RESULT_SEQUENCE_OUT_OF_ORDER")
        if "finding:RESULT_ROLLBACK_INCOMPLETE" in outcome["notes"]:
            blocking_findings.append("RESULT_ROLLBACK_INCOMPLETE")
        if "finding:RESULT_VERIFY_MISMATCH" in outcome["notes"]:
            blocking_findings.append("RESULT_VERIFY_MISMATCH")
        if "finding:RESULT_INTERNAL_DRIVE_TOUCHED" in outcome["notes"]:
            blocking_findings.append("RESULT_INTERNAL_DRIVE_TOUCHED")
        if "finding:RESULT_UNTRACKED_MOUNT_CHANGE" in outcome["notes"]:
            blocking_findings.append("RESULT_UNTRACKED_MOUNT_CHANGE")

    all_present = len(missing_runbooks) == 0
    all_pass = pass_count == len(_REQUIRED_RUNBOOKS)
    no_blockers = len(blocking_findings) == 0
    rollback_complete = "RESULT_ROLLBACK_INCOMPLETE" not in blocking_findings
    acceptance_contradiction = requested_decision == "lab_ready_candidate" and not (
        validator_status == "ok" and all_present and all_pass and no_blockers and rollback_complete
    )
    if acceptance_contradiction:
        blocking_findings.append("RESULT_PREVIOUS_RUNBOOK_FAILED")
        errors.append("acceptance_decision_contradictory")

    acceptance_status = "repeat_required"
    if validator_status == "blocked" or blocking_findings or failed_count > 0 or acceptance_contradiction:
        acceptance_status = "blocked"
    elif validator_status == "ok" and all_present and all_pass and no_blockers and rollback_complete:
        acceptance_status = "lab_ready_candidate"
    elif evidence_partial_count > 0 or repeat_required_count > 0 or missing_runbooks:
        acceptance_status = "repeat_required"

    return {
        "acceptance_status": acceptance_status,
        "runtime_summary": runtime_summary,
        "runbook_outcomes": runbook_outcomes,
        "evidence_summary": evidence_summary,
        "blocking_findings": list(dict.fromkeys(blocking_findings)),
        "residual_risks": list(_RESIDUAL_RISKS),
        "required_repeats": list(dict.fromkeys(required_repeats + missing_runbooks)),
        "operator_decision_required": True,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
