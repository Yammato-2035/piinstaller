from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_INDEX_REL = "docs/evidence/runtime-results/handoff/validator_seal_index.json"
_MAX_SEAL_FILE_BYTES = 128 * 1024
_MAX_INDEX_BYTES = 256 * 1024


def _resolve_handoff_only_rel(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "INDEX_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "INDEX_PATH_INVALID"
    if ".." in p.parts:
        return None, "INDEX_PATH_INVALID"
    if p.suffix.lower() != ".json":
        return None, "INDEX_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "INDEX_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "INDEX_OUTSIDE_HANDOFF"
    return resolved, None


def _path_chain_symlink_clean(path: Path) -> bool:
    cur = path
    while True:
        if cur.exists() and cur.is_symlink():
            return False
        if cur.parent == cur:
            break
        cur = cur.parent
    return True


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _try_parse_seal(path: Path, rel_seal: str) -> tuple[dict[str, Any] | None, str | None]:
    label = Path(rel_seal).name
    if not path.is_file():
        return None, f"invalid_seal_skipped:{label}"
    if path.stat().st_size > _MAX_SEAL_FILE_BYTES:
        return None, f"invalid_seal_skipped:{label}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None, f"invalid_seal_skipped:{label}"
    if not isinstance(data, dict):
        return None, f"invalid_seal_skipped:{label}"
    sha = str(data.get("source_report_sha256") or "").strip()
    if not sha:
        return None, f"invalid_seal_skipped:{label}"
    sealed_at = str(data.get("sealed_at") or "").strip()
    if not sealed_at:
        return None, f"invalid_seal_skipped:{label}"
    if str(data.get("validator_status") or "") != "ok":
        return None, f"invalid_seal_skipped:{label}"
    src = str(data.get("source_report") or "").strip()
    if not src:
        return None, f"invalid_seal_skipped:{label}"
    return (
        {
            "seal_file": rel_seal,
            "source_report": src,
            "source_report_sha256": sha,
            "sealed_at": sealed_at,
        },
        None,
    )


def build_validator_report_seal_index(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []
    indexed_seals: list[dict[str, Any]] = []

    def fail(codes: list[str]) -> dict[str, Any]:
        blocked_reasons.extend(c for c in codes if c not in blocked_reasons)
        return {
            "index_status": "blocked",
            "indexed_seals": [],
            "index_file_path": _INDEX_REL,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    index_resolved, ierr = _resolve_handoff_only_rel(_INDEX_REL)
    if ierr or index_resolved is None:
        return fail([ierr or "INDEX_PATH_INVALID"])

    if index_resolved.exists() and index_resolved.is_file() and not explicit_overwrite:
        return fail(["INDEX_EXISTS_NO_OVERWRITE"])

    _HANDOFF_ROOT.mkdir(parents=True, exist_ok=True)

    if not _path_chain_symlink_clean(_HANDOFF_ROOT):
        return fail(["INDEX_HANDOFF_SYMLINK_BLOCKED"])

    for entry in sorted(_HANDOFF_ROOT.iterdir(), key=lambda p: p.name):
        if not entry.is_file():
            continue
        if not entry.name.endswith(".seal.json"):
            continue
        if not _path_chain_symlink_clean(entry):
            warnings.append(f"invalid_seal_skipped:{entry.name}")
            continue
        rel = str(entry.resolve(strict=False).relative_to(_REPO_ROOT))
        parsed, warn = _try_parse_seal(entry, rel)
        if warn:
            warnings.append(warn)
            continue
        if parsed:
            indexed_seals.append(parsed)

    indexed_seals.sort(key=lambda x: (x.get("sealed_at") or "", x.get("seal_file") or ""))

    if not indexed_seals:
        blocked_reasons.append("INDEX_NO_VALID_SEALS")
        return {
            "index_status": "blocked",
            "indexed_seals": [],
            "index_file_path": _INDEX_REL,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body: dict[str, Any] = {
        "index_schema_version": 1,
        "strict_mode": "validator_report_seal_index",
        "generated_at": generated_at,
        "seal_count": len(indexed_seals),
        "seals": indexed_seals,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_INDEX_BYTES:
        return fail(["INDEX_OUTPUT_TOO_LARGE"])

    try:
        _atomic_write(index_resolved, text)
    except OSError:
        return fail(["INDEX_WRITE_FAILED"])

    index_status = "review_required" if warnings else "ok"
    return {
        "index_status": index_status,
        "indexed_seals": list(indexed_seals),
        "index_file_path": _INDEX_REL,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "blocked_reasons": [],
    }
