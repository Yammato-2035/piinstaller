from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs" / "evidence" / "runtime-results" / "handoff").resolve(strict=False)
_DEFAULT_SEAL_REL = "docs/evidence/runtime-results/handoff/validator_dryrun_report.seal.json"
_MAX_SOURCE_REPORT_BYTES = 512 * 1024
_MAX_SEAL_OUTPUT_BYTES = 128 * 1024


def _resolve_handoff_source_report(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "SEAL_REPORT_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "SEAL_REPORT_PATH_INVALID"
    if ".." in p.parts:
        return None, "SEAL_REPORT_PATH_INVALID"
    if p.suffix.lower() != ".json":
        return None, "SEAL_REPORT_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "SEAL_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "SEAL_REPORT_OUTSIDE_HANDOFF"
    return resolved, None


def _resolve_seal_output(rel_path: str) -> tuple[Path | None, str | None]:
    return _resolve_handoff_source_report(rel_path)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def seal_manual_runtime_validator_report(
    *,
    dryrun_report_path: str,
    explicit_overwrite: bool = False,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []

    def fail(codes: list[str]) -> dict[str, Any]:
        blocked_reasons.extend(c for c in codes if c not in blocked_reasons)
        return {
            "seal_status": "blocked",
            "seal_file_path": "",
            "sealed_sha256": "",
            "sealed_at": "",
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    seal_resolved, serr = _resolve_seal_output(_DEFAULT_SEAL_REL)
    if serr or seal_resolved is None:
        return fail([serr or "SEAL_OUTPUT_PATH_INVALID"])

    if seal_resolved.exists() and seal_resolved.is_file() and not explicit_overwrite:
        return fail(["SEAL_EXISTS_NO_OVERWRITE"])

    src_resolved, rerr = _resolve_handoff_source_report(dryrun_report_path)
    if rerr or src_resolved is None:
        return fail([rerr or "SEAL_REPORT_PATH_INVALID"])

    if str(src_resolved.resolve(strict=False)) == str(seal_resolved.resolve(strict=False)):
        return fail(["SEAL_SOURCE_EQUALS_OUTPUT"])

    if not src_resolved.is_file():
        return fail(["SEAL_SOURCE_REPORT_MISSING"])

    raw = src_resolved.read_bytes()
    if len(raw) > _MAX_SOURCE_REPORT_BYTES:
        return fail(["SEAL_SOURCE_REPORT_TOO_LARGE"])

    try:
        text = raw.decode("utf-8")
        data = json.loads(text)
    except Exception:
        return fail(["SEAL_SOURCE_REPORT_JSON_INVALID"])

    if not isinstance(data, dict):
        return fail(["SEAL_SOURCE_REPORT_JSON_INVALID"])

    if str(data.get("dryrun_status") or "") != "ok":
        return fail(["SEAL_DRYRUN_STATUS_NOT_OK"])

    vr = data.get("validator_result")
    if not isinstance(vr, dict) or not vr:
        return fail(["SEAL_VALIDATOR_RESULT_MISSING"])

    source_sha256 = hashlib.sha256(raw).hexdigest()
    sealed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rel_source = str(dryrun_report_path).strip()

    seal_body: dict[str, Any] = {
        "seal_schema_version": 1,
        "sealed_at": sealed_at,
        "source_report": rel_source,
        "source_report_sha256": source_sha256,
        "validator_status": "ok",
        "strict_mode": "immutable_validator_report_seal",
    }
    seal_text = json.dumps(seal_body, indent=2, sort_keys=True)
    if len(seal_text.encode("utf-8")) > _MAX_SEAL_OUTPUT_BYTES:
        return fail(["SEAL_OUTPUT_TOO_LARGE"])

    try:
        _atomic_write(seal_resolved, seal_text)
    except OSError:
        return fail(["SEAL_WRITE_FAILED"])

    return {
        "seal_status": "sealed",
        "seal_file_path": _DEFAULT_SEAL_REL,
        "sealed_sha256": source_sha256,
        "sealed_at": sealed_at,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "blocked_reasons": [],
    }
