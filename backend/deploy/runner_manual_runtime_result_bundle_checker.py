from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from deploy.runner_manual_runtime_result_edit_checker import check_manual_runtime_result_file
from deploy.runner_runtime_runbook_bundle import build_runner_runtime_runbook_bundle

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ALLOWED_ROOT = (_REPO_ROOT / "docs" / "evidence" / "runtime-results").resolve(strict=False)
_MAX_FILE_SIZE = 2 * 1024 * 1024
_WRITE_RUNBOOKS = {
    "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
    "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
    "RUNBOOK_DEVICE_REENUMERATION",
    "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
    "RUNBOOK_ROLLBACK_RUNTIME",
}


def _expected_sequence() -> list[str]:
    bundle = build_runner_runtime_runbook_bundle()
    seq: list[str] = []
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


def _resolve_allowed_result_file(path: str) -> tuple[Path | None, str | None]:
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
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_ALLOWED_ROOT) + "/") or str(resolved) == str(_ALLOWED_ROOT)):
        return None, "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"
    return resolved, None


def _try_load_payload(result_file: str) -> dict[str, Any] | None:
    resolved, err = _resolve_allowed_result_file(result_file)
    if err or resolved is None:
        return None
    if not resolved.is_file() or resolved.stat().st_size > _MAX_FILE_SIZE:
        return None
    try:
        data = json.loads(resolved.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _bundle_safety_scan(by_runbook: dict[str, dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    for _rb, payload in by_runbook.items():
        ev = payload.get("evidence") if isinstance(payload.get("evidence"), dict) else {}
        if bool(ev.get("internal_drive_touched")):
            findings.append("BUNDLE_INTERNAL_DRIVE_TOUCHED")
        if bool(ev.get("untracked_mount_change")):
            findings.append("BUNDLE_UNTRACKED_MOUNT_CHANGE")
        if str(ev.get("verify_status") or "").lower() == "mismatch":
            findings.append("BUNDLE_VERIFY_MISMATCH")
        if str(payload.get("pass_fail") or "").lower() == "failed":
            findings.append("BUNDLE_RUNBOOK_FAILED")
        rs = str(payload.get("rollback_status") or "").strip().lower()
        if rs in {"", "incomplete"}:
            findings.append("BUNDLE_ROLLBACK_INCOMPLETE")

        rb_id = str(payload.get("runbook_id") or "")
        if not str(ev.get("audit_jsonl_excerpt") or "").strip():
            findings.append("BUNDLE_AUDIT_MISSING")
        if not str(ev.get("jobfile_hash") or "").strip():
            findings.append("BUNDLE_JOB_HASH_MISSING")
        if not str(ev.get("snapshot_fingerprint") or "").strip():
            findings.append("BUNDLE_FINGERPRINT_MISSING")

        if rb_id in _WRITE_RUNBOOKS:
            if "bytes_written" not in ev:
                findings.append("BUNDLE_WRITE_EVIDENCE_MISSING")
            if not str(ev.get("expected_sha256") or "").strip():
                findings.append("BUNDLE_WRITE_EVIDENCE_MISSING")
            if not str(ev.get("actual_sha256") or "").strip():
                findings.append("BUNDLE_WRITE_EVIDENCE_MISSING")
            if not str(ev.get("verify_status") or "").strip():
                findings.append("BUNDLE_WRITE_EVIDENCE_MISSING")
    return findings


def check_manual_runtime_result_bundle(*, result_files: list[str] | None = None) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    bundle_findings: list[str] = []
    sequence = _expected_sequence()
    sequence_set = set(sequence)

    raw_files = [str(x).strip() for x in (result_files or []) if str(x or "").strip()]

    per_file_checks: list[dict[str, Any]] = []
    for f in raw_files:
        chk = check_manual_runtime_result_file(result_file=f)
        vr = chk.get("validator_readiness") if isinstance(chk.get("validator_readiness"), dict) else {}
        per_file_checks.append(
            {
                "result_file": f,
                "runbook_id": str(chk.get("runbook_id") or ""),
                "check_status": str(chk.get("check_status") or "review_required"),
                "blocking_findings": list(chk.get("blocking_findings") or []),
                "warnings": list(chk.get("warnings") or []),
                "ready_for_ingestion_validator": bool(vr.get("ready_for_ingestion_validator")),
            }
        )
        warnings.extend(list(chk.get("warnings") or []))
        errors.extend(list(chk.get("errors") or []))

    payloads_ordered: list[dict[str, Any] | None] = []
    for f in raw_files:
        payloads_ordered.append(_try_load_payload(f))

    ids_in_order = [str(p.get("runbook_id") or "") if isinstance(p, dict) else "" for p in payloads_ordered]
    ids_nonempty = [i for i in ids_in_order if i]
    id_counts: dict[str, int] = {}
    for i in ids_nonempty:
        id_counts[i] = id_counts.get(i, 0) + 1

    duplicate_runbooks = sorted([rb for rb, c in id_counts.items() if c > 1])
    present_set = set(ids_nonempty)
    missing_runbooks = [rb for rb in sequence if rb not in present_set]
    unknown_runbooks = sorted([rb for rb in present_set if rb not in sequence_set])

    if duplicate_runbooks:
        bundle_findings.append("BUNDLE_RESULT_DUPLICATE_RUNBOOK")
    if unknown_runbooks:
        bundle_findings.append("BUNDLE_RESULT_UNKNOWN_RUNBOOK")
    if missing_runbooks:
        bundle_findings.append("BUNDLE_RESULT_MISSING_RUNBOOK")

    order_ok = bool(
        len(ids_in_order) == 7
        and ids_in_order == sequence
        and not duplicate_runbooks
        and not unknown_runbooks
        and not missing_runbooks
    )
    if (
        not duplicate_runbooks
        and not unknown_runbooks
        and not missing_runbooks
        and len(ids_in_order) == 7
        and ids_in_order != sequence
    ):
        bundle_findings.append("BUNDLE_RESULT_SEQUENCE_OUT_OF_ORDER")

    by_runbook: dict[str, dict[str, Any]] = {}
    for p in payloads_ordered:
        if isinstance(p, dict):
            rb = str(p.get("runbook_id") or "")
            if rb:
                by_runbook[rb] = p

    prev_non_pass = False
    for rb in sequence:
        pl = by_runbook.get(rb)
        if not isinstance(pl, dict):
            continue
        pf = str(pl.get("pass_fail") or "").lower()
        if prev_non_pass and pf == "pass":
            bundle_findings.append("BUNDLE_RESULT_PREVIOUS_RUNBOOK_NOT_PASS")
        if pf in {"failed", "skipped", "repeat_required"}:
            prev_non_pass = True

    bundle_findings.extend(_bundle_safety_scan(by_runbook))

    bundle_findings = list(dict.fromkeys(bundle_findings))

    any_pf_blocked = any(str(x.get("check_status")) == "blocked" for x in per_file_checks)
    any_pf_review = any(str(x.get("check_status")) == "review_required" for x in per_file_checks)

    bundle_check_status = "ok"
    if bundle_findings or any_pf_blocked:
        bundle_check_status = "blocked"
    elif any_pf_review:
        bundle_check_status = "review_required"

    sequence_all_present = not missing_runbooks and not duplicate_runbooks and not unknown_runbooks
    previous_chain_ok = "BUNDLE_RESULT_PREVIOUS_RUNBOOK_NOT_PASS" not in bundle_findings
    runbook_sequence_status = {
        "expected_sequence": list(sequence),
        "runbook_ids_in_input_order": list(ids_in_order),
        "all_seven_present": sequence_all_present and len(raw_files) == 7,
        "no_duplicates": not duplicate_runbooks,
        "no_unknown_runbooks": not unknown_runbooks,
        "order_matches_sequence": order_ok,
        "previous_runbook_chain_ok": previous_chain_ok,
    }

    all_per_file_ok = bool(per_file_checks) and all(str(x.get("check_status")) == "ok" for x in per_file_checks)
    if not raw_files:
        all_per_file_ok = False
        bundle_check_status = "blocked"
        errors.append("empty_result_files")

    no_bundle_blockers = not bundle_findings
    ready_for_runtime_result_validator = bool(
        raw_files
        and order_ok
        and all_per_file_ok
        and no_bundle_blockers
        and previous_chain_ok
    )

    expected_blockers: list[str] = []
    expected_blockers.extend(bundle_findings)
    for p in per_file_checks:
        expected_blockers.extend(list(p.get("blocking_findings") or []))
    expected_blockers = list(dict.fromkeys(expected_blockers))

    expected_warnings = list(dict.fromkeys(warnings))

    if ready_for_runtime_result_validator:
        expected_validator_status = "ok"
    elif bundle_check_status == "blocked":
        expected_validator_status = "blocked"
    else:
        expected_validator_status = "review_required"

    validator_bundle_readiness = {
        "ready_for_runtime_result_validator": ready_for_runtime_result_validator,
        "expected_validator_status": expected_validator_status,
        "validator_input_files": list(raw_files) if ready_for_runtime_result_validator else [],
        "expected_blockers": expected_blockers if not ready_for_runtime_result_validator else [],
        "expected_warnings": expected_warnings if not ready_for_runtime_result_validator else [],
    }

    return {
        "bundle_check_status": bundle_check_status,
        "result_files": list(raw_files),
        "runbook_sequence_status": runbook_sequence_status,
        "per_file_checks": per_file_checks,
        "bundle_findings": bundle_findings,
        "validator_bundle_readiness": validator_bundle_readiness,
        "missing_runbooks": missing_runbooks,
        "duplicate_runbooks": duplicate_runbooks,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
