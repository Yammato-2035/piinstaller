from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deploy.runner_runtime_result_validator import validate_runner_runtime_result_bundle

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME_RESULTS_ROOT = (_REPO_ROOT / "docs" / "evidence" / "runtime-results").resolve(strict=False)
_HANDOFF_ROOT = (_REPO_ROOT / "docs" / "evidence" / "runtime-results" / "handoff").resolve(strict=False)
_DEFAULT_REPORT_REL = "docs/evidence/runtime-results/handoff/validator_dryrun_report.json"
_MAX_MANIFEST_BYTES = 512 * 1024
_MAX_RESULT_FILE_SIZE = 2 * 1024 * 1024


def _under_handoff(resolved: Path) -> bool:
    rs = str(resolved)
    hs = str(_HANDOFF_ROOT)
    return rs == hs or rs.startswith(hs + os.sep)


def _resolve_handoff_manifest_read(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "DRYRUN_MANIFEST_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "DRYRUN_MANIFEST_PATH_INVALID"
    if ".." in p.parts:
        return None, "DRYRUN_MANIFEST_PATH_INVALID"
    if p.suffix.lower() != ".json":
        return None, "DRYRUN_MANIFEST_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "DRYRUN_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "DRYRUN_MANIFEST_OUTSIDE_HANDOFF"
    return resolved, None


def _resolve_dryrun_report(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "DRYRUN_REPORT_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "DRYRUN_REPORT_PATH_INVALID"
    if ".." in p.parts:
        return None, "DRYRUN_REPORT_PATH_INVALID"
    if p.suffix.lower() != ".json":
        return None, "DRYRUN_REPORT_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "DRYRUN_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "DRYRUN_REPORT_OUTSIDE_HANDOFF"
    return resolved, None


def _resolve_runtime_result_data_file(path: str) -> tuple[Path | None, str | None]:
    raw = str(path or "").strip()
    if not raw:
        return None, "DRYRUN_RESULT_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "DRYRUN_RESULT_PATH_INVALID"
    if ".." in p.parts:
        return None, "DRYRUN_RESULT_PATH_INVALID"
    if p.suffix.lower() != ".json":
        return None, "DRYRUN_RESULT_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "DRYRUN_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_RUNTIME_RESULTS_ROOT) + os.sep) or str(resolved) == str(_RUNTIME_RESULTS_ROOT)):
        return None, "DRYRUN_RESULT_OUTSIDE_RUNTIME_RESULTS"
    if _under_handoff(resolved):
        return None, "DRYRUN_RESULT_FILE_UNDER_HANDOFF_FORBIDDEN"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def run_manual_runtime_result_validator_dryrun_from_handoff(
    *,
    handoff_manifest_path: str,
    explicit_overwrite: bool = False,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []
    validator_input_files: list[str] = []
    validator_result: dict[str, Any] = {}
    dryrun_report_path_out = _DEFAULT_REPORT_REL

    def fail(codes: list[str]) -> dict[str, Any]:
        for c in codes:
            if c not in blocked_reasons:
                blocked_reasons.append(c)
        return {
            "dryrun_status": "blocked",
            "validator_input_files": list(validator_input_files),
            "validator_result": validator_result,
            "dryrun_report_path": dryrun_report_path_out,
            "blocked_reasons": list(blocked_reasons),
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
        }

    report_resolved, rerr = _resolve_dryrun_report(_DEFAULT_REPORT_REL)
    if rerr or report_resolved is None:
        dryrun_report_path_out = ""
        return fail([rerr or "DRYRUN_REPORT_PATH_INVALID"])

    if report_resolved.exists() and report_resolved.is_file() and not explicit_overwrite:
        return fail(["DRYRUN_REPORT_EXISTS_NO_OVERWRITE"])

    manifest_resolved, merr = _resolve_handoff_manifest_read(handoff_manifest_path)
    if merr or manifest_resolved is None:
        return fail([merr or "DRYRUN_MANIFEST_PATH_INVALID"])

    if not manifest_resolved.is_file():
        return fail(["DRYRUN_MANIFEST_MISSING"])

    if manifest_resolved.stat().st_size > _MAX_MANIFEST_BYTES:
        return fail(["DRYRUN_MANIFEST_TOO_LARGE"])

    try:
        manifest_data = json.loads(manifest_resolved.read_text(encoding="utf-8"))
    except Exception:
        return fail(["DRYRUN_MANIFEST_JSON_INVALID"])

    if not isinstance(manifest_data, dict):
        return fail(["DRYRUN_MANIFEST_JSON_INVALID"])

    vif_raw = manifest_data.get("validator_input_files")
    if not isinstance(vif_raw, list):
        return fail(["DRYRUN_MANIFEST_VALIDATOR_INPUT_FILES_INVALID"])
    vif = [str(x).strip() for x in vif_raw if str(x or "").strip()]
    validator_input_files = list(vif)
    if len(vif) != 7:
        return fail(["DRYRUN_VALIDATOR_INPUT_FILES_COUNT_NOT_SEVEN"])

    for rel in vif:
        resolved, perr = _resolve_runtime_result_data_file(rel)
        if perr or resolved is None:
            return fail([perr or "DRYRUN_RESULT_PATH_INVALID"])
        if not resolved.is_file():
            return fail(["DRYRUN_RESULT_FILE_MISSING"])
        if resolved.stat().st_size > _MAX_RESULT_FILE_SIZE:
            return fail(["DRYRUN_RESULT_FILE_TOO_LARGE"])

    validator_result = validate_runner_runtime_result_bundle(result_files=vif, acceptance_decision="blocked")
    vstatus = str(validator_result.get("validation_status") or "blocked")
    dryrun_status = vstatus
    if dryrun_status not in {"ok", "review_required", "blocked"}:
        dryrun_status = "blocked"

    report_body: dict[str, Any] = {
        "dryrun_schema_version": 1,
        "strict_mode": "manual_runtime_result_validator_dryrun_from_handoff",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "handoff_manifest_path": str(handoff_manifest_path).strip(),
        "manifest_not_modified": True,
        "result_files_not_modified": True,
        "validator_input_files": list(vif),
        "dryrun_status": dryrun_status,
        "validator_result": validator_result,
    }
    report_text = json.dumps(report_body, indent=2, sort_keys=True)
    try:
        _atomic_write(report_resolved, report_text)
    except OSError:
        return fail(["DRYRUN_REPORT_WRITE_FAILED"])

    return {
        "dryrun_status": dryrun_status,
        "validator_input_files": list(vif),
        "validator_result": validator_result,
        "dryrun_report_path": dryrun_report_path_out,
        "blocked_reasons": [],
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
