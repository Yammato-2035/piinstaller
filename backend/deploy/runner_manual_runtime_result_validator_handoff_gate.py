from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME_RESULTS_ROOT = (_REPO_ROOT / "docs" / "evidence" / "runtime-results").resolve(strict=False)
_HANDOFF_ROOT = (_REPO_ROOT / "docs" / "evidence" / "runtime-results" / "handoff").resolve(strict=False)
_DEFAULT_MANIFEST_REL = "docs/evidence/runtime-results/handoff/validator_handoff_manifest.json"
_MAX_MANIFEST_BYTES = 512 * 1024
_MAX_RESULT_FILE_SIZE = 2 * 1024 * 1024


def _under_handoff(resolved: Path) -> bool:
    rs = str(resolved)
    hs = str(_HANDOFF_ROOT)
    return rs == hs or rs.startswith(hs + os.sep)


def _resolve_runtime_result_data_file(path: str) -> tuple[Path | None, str | None]:
    raw = str(path or "").strip()
    if not raw:
        return None, "HANDOFF_PATH_OUTSIDE_ALLOWED_ROOT"
    p = Path(raw)
    if p.is_absolute():
        return None, "HANDOFF_PATH_OUTSIDE_ALLOWED_ROOT"
    if ".." in p.parts:
        return None, "HANDOFF_PATH_OUTSIDE_ALLOWED_ROOT"
    if p.suffix.lower() != ".json":
        return None, "HANDOFF_PATH_OUTSIDE_ALLOWED_ROOT"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "HANDOFF_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_RUNTIME_RESULTS_ROOT) + os.sep) or str(resolved) == str(_RUNTIME_RESULTS_ROOT)):
        return None, "HANDOFF_PATH_OUTSIDE_ALLOWED_ROOT"
    if _under_handoff(resolved):
        return None, "HANDOFF_RESULT_FILE_MUST_NOT_BE_UNDER_HANDOFF"
    return resolved, None


def _resolve_handoff_manifest_path(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "HANDOFF_MANIFEST_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "HANDOFF_MANIFEST_PATH_INVALID"
    if ".." in p.parts:
        return None, "HANDOFF_MANIFEST_PATH_INVALID"
    if p.suffix.lower() != ".json":
        return None, "HANDOFF_MANIFEST_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "HANDOFF_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "HANDOFF_MANIFEST_OUTSIDE_HANDOFF_ROOT"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def build_manual_runtime_result_validator_handoff(
    *,
    bundle_check_result: dict[str, Any] | None = None,
    result_files: list[str] | None = None,
    explicit_overwrite: bool = False,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []
    handoff_status: str = "blocked"
    validator_input_files: list[str] = []
    handoff_manifest_path = ""
    expected_validator_status = ""

    bundle = dict(bundle_check_result or {})
    vr = bundle.get("validator_bundle_readiness") if isinstance(bundle.get("validator_bundle_readiness"), dict) else {}
    expected_validator_status = str(vr.get("expected_validator_status") or "")

    raw_results = [str(x).strip() for x in (result_files or []) if str(x or "").strip()]
    vif = [str(x).strip() for x in (vr.get("validator_input_files") or []) if str(x or "").strip()]
    validator_input_files = list(vif)

    def fail(code: str) -> dict[str, Any]:
        blocked_reasons.append(code)
        return {
            "handoff_status": "blocked",
            "validator_input_files": validator_input_files,
            "handoff_manifest_path": "",
            "expected_validator_status": expected_validator_status,
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
        }

    bundle_st = str(bundle.get("bundle_check_status") or "")
    if bundle_st == "review_required":
        warnings.append("bundle_check_review_required")
        return {
            "handoff_status": "review_required",
            "validator_input_files": validator_input_files,
            "handoff_manifest_path": "",
            "expected_validator_status": expected_validator_status,
            "blocked_reasons": [],
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors)),
        }

    if bundle_st != "ok":
        return fail("HANDOFF_BUNDLE_NOT_OK")

    findings = list(bundle.get("bundle_findings") or [])
    if findings:
        return fail("HANDOFF_BUNDLE_FINDINGS_PRESENT")

    if not bool(vr.get("ready_for_runtime_result_validator")):
        return fail("HANDOFF_BUNDLE_NOT_READY_FOR_VALIDATOR")

    if expected_validator_status not in {"ok", "ready"}:
        return fail("HANDOFF_EXPECTED_VALIDATOR_STATUS_NOT_OK")

    if len(vif) != 7:
        return fail("HANDOFF_VALIDATOR_INPUT_FILES_COUNT_NOT_SEVEN")

    if raw_results != vif:
        return fail("HANDOFF_RESULT_FILES_MISMATCH_VALIDATOR_INPUT")

    rss = bundle.get("runbook_sequence_status") if isinstance(bundle.get("runbook_sequence_status"), dict) else {}
    if not bool(rss.get("order_matches_sequence")):
        return fail("HANDOFF_RUNBOOK_SEQUENCE_ORDER_INVALID")
    if not bool(rss.get("previous_runbook_chain_ok")):
        return fail("HANDOFF_PREVIOUS_RUNBOOK_CHAIN_BROKEN")

    per_file = list(bundle.get("per_file_checks") or [])
    if len(per_file) != 7:
        return fail("HANDOFF_PER_FILE_CHECKS_COUNT_INVALID")
    for entry in per_file:
        st = str(entry.get("check_status") or "")
        if st != "ok":
            return fail("HANDOFF_PER_FILE_NOT_ALL_OK")

    for rel in raw_results:
        resolved, perr = _resolve_runtime_result_data_file(rel)
        if perr or resolved is None:
            return fail(perr or "HANDOFF_PATH_OUTSIDE_ALLOWED_ROOT")
        if not resolved.is_file():
            return fail("HANDOFF_RESULT_FILE_MISSING")
        if resolved.stat().st_size > _MAX_RESULT_FILE_SIZE:
            return fail("HANDOFF_RESULT_FILE_TOO_LARGE")

    manifest_rel = _DEFAULT_MANIFEST_REL
    mpath, merr = _resolve_handoff_manifest_path(manifest_rel)
    if merr or mpath is None:
        return fail(merr or "HANDOFF_MANIFEST_PATH_INVALID")

    if mpath.exists() and mpath.is_file() and not explicit_overwrite:
        return fail("HANDOFF_MANIFEST_EXISTS_NO_OVERWRITE")

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest_body: dict[str, Any] = {
        "handoff_schema_version": 1,
        "strict_mode": "manual_runtime_result_validator_handoff",
        "created_at": created_at,
        "validator_input_files": list(raw_results),
        "bundle_check_status": bundle_st,
        "runbook_sequence_status": {
            "order_matches_sequence": bool(rss.get("order_matches_sequence")),
            "previous_runbook_chain_ok": bool(rss.get("previous_runbook_chain_ok")),
            "expected_sequence": list(rss.get("expected_sequence") or []),
        },
    }
    manifest_text = json.dumps(manifest_body, indent=2, sort_keys=True)
    if len(manifest_text.encode("utf-8")) > _MAX_MANIFEST_BYTES:
        return fail("HANDOFF_MANIFEST_TOO_LARGE")

    try:
        _atomic_write(mpath, manifest_text)
    except OSError:
        return fail("HANDOFF_MANIFEST_WRITE_FAILED")

    handoff_manifest_path = manifest_rel
    handoff_status = "ready"
    return {
        "handoff_status": handoff_status,
        "validator_input_files": list(raw_results),
        "handoff_manifest_path": handoff_manifest_path,
        "expected_validator_status": "ok",
        "blocked_reasons": [],
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
