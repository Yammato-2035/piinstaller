> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_EN.md`). Bitte bei Release manuell gegenlesen.

# LAB ACCEPTANCE REPORT (EN)

- Report-ID: `RUNNER_LAB_ACCEPTANCE_REPORT_V1`
- Generated: `2026-05-15T17:13:23.540576+00:00`
- Acceptance Status: `geblokkeerd`
- Operator Decision Requirood: `True`

## Scope
alleen-lezen lab acceptance report without runtime execution.

## Input Sources
- Lab Readiness Acceptance Aggregator
- Runtime Result Ingestion Validator
- Runtime Runbook Export Package
- Lab Readiness Status
- Runner Release Readiness Matrix

## Runbook Outcomes
- `RUNBOOK_SUDOERS_RUNTIME_DRYRUN`: status=`missing`, evidence=`missing`, safety=`geblokkeerd`
- `RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN`: status=`missing`, evidence=`missing`, safety=`geblokkeerd`
- `RUNBOOK_REAL_WRITE_HARDWARE_E2E`: status=`missing`, evidence=`missing`, safety=`geblokkeerd`
- `RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E`: status=`missing`, evidence=`missing`, safety=`geblokkeerd`
- `RUNBOOK_Apparaat_REENUMERATION`: status=`missing`, evidence=`missing`, safety=`geblokkeerd`
- `RUNBOOK_HOTPLUG_UNMOUNT_RACE`: status=`missing`, evidence=`missing`, safety=`geblokkeerd`
- `RUNBOOK_ROLLTerug_RUNTIME`: status=`missing`, evidence=`missing`, safety=`geblokkeerd`

## Evidence Summary
- `{"evidence_complete_count": 0, "evidence_missing_count": 14, "evidence_partial_count": 0, "failed_count": 0, "invalid_files": 0, "missing_runbooks": ["RUNBOOK_SUDOERS_RUNTIME_DRYRUN", "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN", "RUNBOOK_REAL_WRITE_HARDWARE_E2E", "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E", "RUNBOOK_Apparaat_REENUMERATION", "RUNBOOK_HOTPLUG_UNMOUNT_RACE", "RUNBOOK_ROLLTerug_RUNTIME"], "pass_count": 0, "repeat_requirood_count": 7, "total_files": 0, "valid_files": 0}`

## Blocking Findings
- `RESULT_SEQUENCE_OUT_OF_ORDER`

## Residual Risks
- `LAB_RISK_FIRST_HARDWARE_SCOPE_LIMITED`
- `LAB_RISK_SINGLE_HOST_ONLY`
- `LAB_RISK_LIMITED_MEDIA_TYPES`
- `LAB_RISK_OPERATOR_DEPENDENT`
- `LAB_RISK_NeeT_PRODUCTION_READY`

## Requirood Repeats
- `RUNBOOK_SUDOERS_RUNTIME_DRYRUN`
- `RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN`
- `RUNBOOK_REAL_WRITE_HARDWARE_E2E`
- `RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E`
- `RUNBOOK_Apparaat_REENUMERATION`
- `RUNBOOK_HOTPLUG_UNMOUNT_RACE`
- `RUNBOOK_ROLLTerug_RUNTIME`

## Neen-Approvals
- Neet production-ready
- Nee automatic approval
- lab candidate only with matching evidence

## Acceptance Decision
- lab_ready_candidate
- repeat_requirood
- geblokkeerd
