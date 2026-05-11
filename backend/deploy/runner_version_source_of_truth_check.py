from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.versioning import load_project_version

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_VERSION_STATE_REL = "docs/evidence/runtime-results/handoff/version_state.json"
_CHECK_REL = "docs/evidence/runtime-results/handoff/version_source_of_truth_check.json"
_MAX_OUTPUT_BYTES = 256 * 1024


def _parse(v: str) -> tuple[int, int, int] | None:
    parts = str(v).split(".")
    if len(parts) != 3:
        return None
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "SOT_CHECK_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, "SOT_CHECK_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "SOT_CHECK_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "SOT_CHECK_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _load_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception:
        return None, "SOT_CHECK_JSON_INVALID"


def check_version_source_of_truth_consistency(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []

    out_path, oerr = _resolve_handoff(_CHECK_REL)
    if oerr or out_path is None:
        return _ret("blocked", {}, [oerr or "SOT_CHECK_OUTPUT_PATH_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _ret("blocked", {}, ["SOT_CHECK_EXISTS_NO_OVERWRITE"], [])

    try:
        central = load_project_version()
    except Exception:
        return _ret("blocked", {}, ["SOT_CHECK_CONFIG_INVALID"], [])

    pkg_root, _ = _load_json(_REPO_ROOT / "package.json")
    pkg_front, _ = _load_json(_REPO_ROOT / "frontend" / "package.json")
    tauri, _ = _load_json(_REPO_ROOT / "frontend" / "src-tauri" / "tauri.conf.json")
    vs_path, verr = _resolve_handoff(_VERSION_STATE_REL)
    if verr or vs_path is None or not vs_path.is_file():
        blocked_reasons.append("SOT_CHECK_VERSION_STATE_MISSING")
        return _emit(out_path, "blocked", {}, blocked_reasons, warnings)
    version_state, _ = _load_json(vs_path)
    if not isinstance(version_state, dict):
        blocked_reasons.append("SOT_CHECK_VERSION_STATE_INVALID")
        return _emit(out_path, "blocked", {}, blocked_reasons, warnings)

    versions = {
        "config/version.json": central.project_version,
        "package.json": str((pkg_root or {}).get("version") or ""),
        "frontend/package.json": str((pkg_front or {}).get("version") or ""),
        "frontend/src-tauri/tauri.conf.json": str((tauri or {}).get("version") or ""),
        "evidence/version_state.json": str(version_state.get("current_version") or ""),
        "api": central.project_version,
    }
    central_semver = central.project_version
    tauri_expected = ".".join(central_semver.split(".")[:3]) if central_semver else ""
    if versions["package.json"] != central_semver:
        blocked_reasons.append("SOT_CHECK_DRIFT_ROOT_PACKAGE")
    if versions["frontend/package.json"] != central_semver:
        blocked_reasons.append("SOT_CHECK_DRIFT_FRONTEND_PACKAGE")
    if versions["frontend/src-tauri/tauri.conf.json"] != tauri_expected:
        blocked_reasons.append("SOT_CHECK_DRIFT_TAURI")
    if versions["evidence/version_state.json"] != central_semver:
        blocked_reasons.append("SOT_CHECK_DRIFT_EVIDENCE")
    if str(version_state.get("release_readiness") or "") != central.release_stage:
        blocked_reasons.append("SOT_CHECK_RELEASE_STAGE_INCONSISTENT")
    cur = _parse(str(version_state.get("current_version") or ""))
    prev = _parse(str(version_state.get("previous_version") or ""))
    if cur is None or prev is None:
        blocked_reasons.append("SOT_CHECK_VERSION_STATE_INVALID")
    elif cur <= prev:
        blocked_reasons.append("SOT_CHECK_BACKWARDS_VERSION")

    check_status = "ok" if not blocked_reasons else "blocked"
    body = {
        "check_schema_version": 1,
        "strict_mode": "version_source_of_truth_check",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "check_status": check_status,
        "project_version": central.project_version,
        "release_stage": central.release_stage,
        "version_track": central.version_track,
        "versions": versions,
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
    return _emit(out_path, check_status, body, blocked_reasons, warnings)


def _emit(out_path: Path, check_status: str, body: dict[str, Any], blocked_reasons: list[str], warnings: list[str]) -> dict[str, Any]:
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _ret("blocked", {}, ["SOT_CHECK_OUTPUT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _ret("blocked", {}, ["SOT_CHECK_WRITE_FAILED"], [])
    return _ret(check_status, body, blocked_reasons if check_status == "blocked" else [], warnings)


def _ret(check_status: str, body: dict[str, Any], blocked_reasons: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "check_status": check_status,
        "check_file_path": _CHECK_REL,
        "check": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(blocked_reasons)) if check_status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
