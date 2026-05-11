from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_EXPORT_REL = "docs/evidence/runtime-results/handoff/validator_final_export_package.json"
_MAX_EXPORT_BYTES = 512 * 1024
_MAX_INPUT_FILE_BYTES = 512 * 1024

_FIXED_INPUTS: tuple[str, ...] = (
    "docs/evidence/runtime-results/handoff/validator_final_acceptance.json",
    "docs/evidence/runtime-results/handoff/validator_evidence_final_snapshot.json",
    "docs/evidence/runtime-results/handoff/validator_evidence_timeline.json",
    "docs/evidence/runtime-results/handoff/validator_seal_index.json",
    "docs/evidence/runtime-results/handoff/validator_seal_consistency_audit.json",
    "docs/evidence/runtime-results/handoff/validator_dryrun_report.json",
)


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "EXPORT_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "EXPORT_PATH_INVALID"
    if ".." in p.parts:
        return None, "EXPORT_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "EXPORT_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "EXPORT_OUTSIDE_HANDOFF"
    return resolved, None


def _rel_posix(resolved: Path) -> str:
    rel = resolved.relative_to(_REPO_ROOT)
    return rel.as_posix()


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def build_manual_runtime_final_export_package(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []

    def fail(codes: list[str]) -> dict[str, Any]:
        blocked_reasons.extend(c for c in codes if c not in blocked_reasons)
        return {
            "export_package_status": "blocked",
            "export_file_path": _EXPORT_REL,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    out_resolved, oerr = _resolve_handoff(_EXPORT_REL)
    if oerr or out_resolved is None:
        return fail([oerr or "EXPORT_OUTPUT_PATH_INVALID"])

    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return fail(["EXPORT_EXISTS_NO_OVERWRITE"])

    acc_resolved, aerr = _resolve_handoff(_FIXED_INPUTS[0])
    if aerr or acc_resolved is None:
        return fail([aerr or "EXPORT_ACCEPTANCE_PATH_INVALID"])
    if not acc_resolved.is_file():
        return fail(["EXPORT_ACCEPTANCE_MISSING"])
    if acc_resolved.stat().st_size > _MAX_INPUT_FILE_BYTES:
        return fail(["EXPORT_ACCEPTANCE_TOO_LARGE"])

    try:
        acc_raw = acc_resolved.read_bytes()
        acc_data = json.loads(acc_raw.decode("utf-8"))
    except Exception:
        return fail(["EXPORT_ACCEPTANCE_JSON_INVALID"])

    if not isinstance(acc_data, dict):
        return fail(["EXPORT_ACCEPTANCE_JSON_INVALID"])

    acc_st = str(acc_data.get("acceptance_status") or "")
    if acc_st not in ("accepted", "review_required"):
        return fail(["EXPORT_ACCEPTANCE_NOT_ALLOWED"])

    seal_rels: list[str] = []
    for sp in sorted(_HANDOFF_ROOT.glob("*.seal.json")):
        if not sp.is_file():
            continue
        try:
            seal_rels.append(_rel_posix(sp.resolve(strict=False)))
        except ValueError:
            return fail(["EXPORT_SEAL_PATH_INVALID"])

    if not seal_rels:
        return fail(["EXPORT_NO_SEAL_FILES"])

    all_rels = list(dict.fromkeys([*_FIXED_INPUTS, *seal_rels]))
    sha_map: dict[str, str] = {}

    for rel in all_rels:
        rsv, rerr = _resolve_handoff(rel)
        if rerr or rsv is None:
            return fail([rerr or "EXPORT_INPUT_PATH_INVALID"])
        if not rsv.is_file():
            return fail([f"EXPORT_FILE_MISSING:{Path(rel).name}"])
        if rsv.stat().st_size > _MAX_INPUT_FILE_BYTES:
            return fail([f"EXPORT_FILE_TOO_LARGE:{Path(rel).name}"])
        try:
            raw = rsv.read_bytes()
            json.loads(raw.decode("utf-8"))
        except Exception:
            return fail([f"EXPORT_FILE_JSON_INVALID:{Path(rel).name}"])
        sha_map[rel] = hashlib.sha256(raw).hexdigest()

    included_sorted = sorted(all_rels)
    sha_ordered = {k: sha_map[k] for k in sorted(sha_map.keys())}
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    body: dict[str, Any] = {
        "export_schema_version": 1,
        "strict_mode": "final_evidence_export_package",
        "generated_at": generated_at,
        "acceptance_status": acc_st,
        "included_files": included_sorted,
        "file_count": len(included_sorted),
        "sha256": sha_ordered,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_EXPORT_BYTES:
        return fail(["EXPORT_OUTPUT_TOO_LARGE"])

    try:
        _atomic_write(out_resolved, text)
    except OSError:
        return fail(["EXPORT_WRITE_FAILED"])

    pkg_st = "ok" if acc_st == "accepted" else "review_required"
    return {
        "export_package_status": pkg_st,
        "export_file_path": _EXPORT_REL,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "blocked_reasons": [],
    }
