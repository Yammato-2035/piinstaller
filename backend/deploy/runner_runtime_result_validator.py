from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from deploy.runner_lab_readiness_status import build_runner_lab_readiness_status
from deploy.runner_runtime_runbook_bundle import build_runner_runtime_runbook_bundle

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ALLOWED_ROOT = (_REPO_ROOT / "docs" / "evidence" / "runtime-results").resolve(strict=False)
_SCHEMA_PATH = (_REPO_ROOT / "docs" / "evidence" / "templates" / "RUNNER_RUNTIME_RESULT_SCHEMA.json").resolve(strict=False)
_MAX_FILE_SIZE = 2 * 1024 * 1024
_WRITE_RUNBOOKS = {
    "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
    "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
}
_REQUIRED_FIELDS = [
    "runbook_id",
    "started_at",
    "completed_at",
    "operator",
    "host",
    "target_device",
    "pre_state",
    "post_state",
    "runner_result",
    "evidence",
    "pass_fail",
    "rollback_status",
]
_ALLOWED_PASS_FAIL = {"pass", "fail", "skipped"}
_ALLOWED_ACCEPTANCE = {"lab_ready_candidate", "repeat_required", "blocked"}


def _expected_sequence() -> list[str]:
    bundle = build_runner_runtime_runbook_bundle()
    seq = []
    for item in list(bundle.get("runbook_sequence") or []):
        if isinstance(item, dict):
            rb = str(item.get("runbook_id") or "")
            if rb:
                seq.append(rb)
    if len(seq) == 7:
        return seq
    return [
        "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
        "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN",
        "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
        "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
        "RUNBOOK_DEVICE_REENUMERATION",
        "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
        "RUNBOOK_ROLLBACK_RUNTIME",
    ]


def _load_schema_required_fields() -> list[str]:
    try:
        txt = _SCHEMA_PATH.read_text(encoding="utf-8")
        data = json.loads(txt)
        req = data.get("required")
        if isinstance(req, list) and req:
            return [str(x) for x in req]
    except Exception:
        return list(_REQUIRED_FIELDS)
    return list(_REQUIRED_FIELDS)


def _validate_result_path(path: str) -> tuple[Path | None, str | None]:
    raw = str(path or "").strip()
    if not raw:
        return None, "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"
    p = Path(raw)
    if p.is_absolute():
        return None, "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"
    if ".." in p.parts:
        return None, "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"
    if p.suffix.lower() != ".json":
        return None, "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "RESULT_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    abs_path = unresolved.resolve(strict=False)
    if not (str(abs_path).startswith(str(_ALLOWED_ROOT) + "/") or str(abs_path) == str(_ALLOWED_ROOT)):
        return None, "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"
    return abs_path, None


def validate_runner_runtime_result_file(path: str) -> dict[str, Any]:
    findings: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    parsed: dict[str, Any] = {}

    resolved, path_err = _validate_result_path(path)
    if path_err or resolved is None:
        findings.append(path_err or "RESULT_PATH_OUTSIDE_ALLOWED_ROOT")
        return {
            "path": path,
            "ok": False,
            "result": {},
            "blocking_findings": findings,
            "warnings": warnings,
            "errors": errors + findings,
        }

    if not resolved.exists() or not resolved.is_file():
        findings.append("RESULT_JSON_INVALID")
        return {"path": path, "ok": False, "result": {}, "blocking_findings": findings, "warnings": warnings, "errors": errors + findings}
    if resolved.stat().st_size > _MAX_FILE_SIZE:
        findings.append("RESULT_JSON_INVALID")
        return {"path": path, "ok": False, "result": {}, "blocking_findings": findings, "warnings": warnings, "errors": errors + findings}

    try:
        parsed = json.loads(resolved.read_text(encoding="utf-8"))
    except Exception:
        findings.append("RESULT_JSON_INVALID")
        return {"path": path, "ok": False, "result": {}, "blocking_findings": findings, "warnings": warnings, "errors": errors + findings}

    required = _load_schema_required_fields()
    for field in required:
        if field not in parsed:
            findings.append("RESULT_SCHEMA_MISSING_FIELD")
            errors.append(f"missing_field:{field}")

    runbook_id = str(parsed.get("runbook_id") or "")
    evidence = parsed.get("evidence")
    if not isinstance(evidence, dict):
        findings.append("RESULT_EVIDENCE_MISSING")
    else:
        for key in [
            "lsblk_before_after",
            "findmnt_before_after",
            "mount_before_after",
            "runner_stdout_json",
            "audit_jsonl",
            "jobfile_hash",
            "snapshot_fingerprint",
        ]:
            if key not in evidence:
                findings.append("RESULT_EVIDENCE_MISSING")
                errors.append(f"missing_evidence:{key}")
        if runbook_id in _WRITE_RUNBOOKS:
            for key in ["bytes_written", "expected_sha256", "actual_sha256", "verify_status"]:
                if key not in evidence:
                    findings.append("RESULT_EVIDENCE_MISSING")
                    errors.append(f"missing_evidence:{key}")
        if bool(evidence.get("internal_drive_touched")):
            findings.append("RESULT_INTERNAL_DRIVE_TOUCHED")
        if bool(evidence.get("untracked_mount_change")):
            findings.append("RESULT_UNTRACKED_MOUNT_CHANGE")
        if str(evidence.get("verify_status") or "").lower() == "mismatch":
            findings.append("RESULT_VERIFY_MISMATCH")
        if str(parsed.get("rollback_status") or "").lower() in {"incomplete", "failed"}:
            findings.append("RESULT_ROLLBACK_INCOMPLETE")

    pass_fail = str(parsed.get("pass_fail") or "")
    if pass_fail not in _ALLOWED_PASS_FAIL:
        findings.append("RESULT_EVIDENCE_MISSING")
        errors.append("invalid_pass_fail")

    return {
        "path": path,
        "ok": not findings,
        "result": parsed,
        "blocking_findings": list(dict.fromkeys(findings)),
        "warnings": warnings,
        "errors": errors,
    }


def validate_runner_runtime_result_bundle(
    *,
    result_files: list[str] | None = None,
    acceptance_decision: str = "blocked",
) -> dict[str, Any]:
    sequence = _expected_sequence()
    files = list(result_files or [])
    runbook_results: list[dict[str, Any]] = []
    blocking_findings: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    for p in files:
        r = validate_runner_runtime_result_file(p)
        runbook_results.append(r)
        blocking_findings.extend(list(r.get("blocking_findings") or []))
        warnings.extend(list(r.get("warnings") or []))
        errors.extend(list(r.get("errors") or []))

    by_runbook: dict[str, dict[str, Any]] = {}
    for r in runbook_results:
        res = r.get("result") if isinstance(r.get("result"), dict) else {}
        rb = str(res.get("runbook_id") or "")
        if rb:
            by_runbook[rb] = r

    previous_failed = False
    for idx, rb in enumerate(sequence):
        current = by_runbook.get(rb)
        if current is None:
            blocking_findings.append("RESULT_SEQUENCE_OUT_OF_ORDER")
            errors.append(f"missing_runbook:{rb}")
            continue
        if previous_failed:
            blocking_findings.append("RESULT_PREVIOUS_RUNBOOK_FAILED")
        res = current.get("result") if isinstance(current.get("result"), dict) else {}
        pf = str(res.get("pass_fail") or "")
        if pf in {"fail", "skipped"}:
            previous_failed = True
        # out-of-order check: ensure all earlier are present
        for prev in sequence[:idx]:
            if prev not in by_runbook:
                blocking_findings.append("RESULT_SEQUENCE_OUT_OF_ORDER")

    schema_check = {
        "required_fields": _load_schema_required_fields(),
        "all_required_present": "RESULT_SCHEMA_MISSING_FIELD" not in blocking_findings,
    }
    sequence_check = {
        "expected_sequence": list(sequence),
        "sequence_ok": "RESULT_SEQUENCE_OUT_OF_ORDER" not in blocking_findings and "RESULT_PREVIOUS_RUNBOOK_FAILED" not in blocking_findings,
    }
    evidence_check = {
        "evidence_ok": "RESULT_EVIDENCE_MISSING" not in blocking_findings,
    }

    acc = str(acceptance_decision or "blocked")
    if acc not in _ALLOWED_ACCEPTANCE:
        acc = "blocked"
        errors.append("invalid_acceptance_decision")

    all_pass = True
    for rb in sequence:
        entry = by_runbook.get(rb)
        if entry is None:
            all_pass = False
            break
        pf = str(((entry.get("result") or {}).get("pass_fail")) or "")
        if pf != "pass":
            all_pass = False
            break

    acceptance_check = {"accepted_decision": acc, "lab_ready_candidate_allowed": bool(all_pass and not blocking_findings)}
    if acc == "lab_ready_candidate" and not acceptance_check["lab_ready_candidate_allowed"]:
        blocking_findings.append("RESULT_PREVIOUS_RUNBOOK_FAILED")
        errors.append("lab_ready_candidate_not_allowed")

    _ = build_runner_lab_readiness_status()
    validation_status = "ok"
    if blocking_findings:
        validation_status = "blocked"
    elif warnings:
        validation_status = "review_required"

    return {
        "validation_status": validation_status,
        "result_files": files,
        "runbook_results": runbook_results,
        "sequence_check": sequence_check,
        "schema_check": schema_check,
        "evidence_check": evidence_check,
        "acceptance_check": acceptance_check,
        "blocking_findings": list(dict.fromkeys(blocking_findings)),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
