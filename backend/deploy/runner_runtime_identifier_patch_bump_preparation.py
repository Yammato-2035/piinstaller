from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)

_ZERO_STATE_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_zero_state_verification.json"
_CFG_VERSION_REL = "config/version.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_patch_bump_preparation.json"
_MAX_OUTPUT_BYTES = 128 * 1024


def _resolve_handoff(rel_path: str, prefix: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, f"{prefix}_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, f"{prefix}_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, f"{prefix}_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, f"{prefix}_OUTSIDE_HANDOFF"
    return resolved, None


def _resolve_repo(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip().replace("\\", "/")
    if not raw or ".." in raw or raw.startswith("/"):
        return None, "PATCH_PREP_REPO_PATH_INVALID"
    unresolved = _REPO_ROOT / raw
    try:
        resolved = unresolved.resolve(strict=False)
        resolved.relative_to(_REPO_ROOT.resolve(strict=False))
    except (OSError, ValueError):
        return None, "PATCH_PREP_OUTSIDE_REPO"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _parse_version_parts(v: str) -> tuple[int, ...] | None:
    parts = str(v).strip().split(".")
    if len(parts) not in (3, 4):
        return None
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


def _bump_patch(v: str) -> str | None:
    p = _parse_version_parts(v)
    if p is None:
        return None
    if len(p) == 4:
        return f"{p[0]}.{p[1]}.{p[2]}.{p[3] + 1}"
    return f"{p[0]}.{p[1]}.{p[2] + 1}"


def prepare_runtime_identifier_patch_bump(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_OUT_REL, "PATCH_PREP")
    if oerr or out_path is None:
        return _emit("blocked", {}, [oerr or "PATCH_PREP_OUTPUT_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _emit("blocked", {}, ["PATCH_PREP_EXISTS_NO_OVERWRITE"], [])

    zp, zerr = _resolve_handoff(_ZERO_STATE_REL, "ZERO_STATE_IN")
    if zerr or zp is None or not zp.is_file():
        return _emit("blocked", {}, [zerr or "ZERO_STATE_VERIFICATION_MISSING"], [])
    try:
        zero_doc = json.loads(zp.read_text(encoding="utf-8"))
    except Exception:
        return _emit("blocked", {}, ["ZERO_STATE_VERIFICATION_JSON_INVALID"], [])

    zero_st = str(zero_doc.get("zero_state_status") or "")
    if zero_st != "ok":
        body = {
            "preparation_schema_version": 1,
            "strict_mode": "runtime_identifier_patch_bump_preparation",
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "preparation_status": "blocked",
            "blocked_reason": "ZERO_STATE_NOT_OK",
            "zero_state_status_observed": zero_st,
            "no_auto_apply": True,
        }
        text = json.dumps(body, indent=2, sort_keys=True)
        _atomic_write(out_path, text)
        return _emit("blocked", body, ["ZERO_STATE_NOT_OK"], [])

    cfg_path, gerr = _resolve_repo(_CFG_VERSION_REL)
    if gerr or cfg_path is None or not cfg_path.is_file():
        return _emit("blocked", {}, [gerr or "CONFIG_VERSION_MISSING"], [])
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return _emit("blocked", {}, ["CONFIG_VERSION_JSON_INVALID"], [])

    prev = str(cfg.get("project_version") or "")
    nxt = _bump_patch(prev)
    if not nxt or _parse_version_parts(nxt) is None:
        return _emit("blocked", {}, ["PATCH_PREP_VERSION_PARSE_FAILED"], [])

    body = {
        "preparation_schema_version": 1,
        "strict_mode": "runtime_identifier_patch_bump_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "preparation_status": "ok",
        "previous_version": prev,
        "suggested_next_version": nxt,
        "phase": "runtime_identifier_zero_state",
        "release_stage": "internal_testing",
        "no_auto_apply": True,
        "source_zero_state_file": _ZERO_STATE_REL,
        "source_config_version": _CFG_VERSION_REL,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit("blocked", {}, ["PATCH_PREP_OUTPUT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _emit("blocked", {}, ["PATCH_PREP_WRITE_FAILED"], [])
    return _emit("ok", body, [], [])


def _emit(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "runtime_identifier_patch_bump_preparation_status": status,
        "runtime_identifier_patch_bump_preparation_file_path": _OUT_REL,
        "runtime_identifier_patch_bump_preparation": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
