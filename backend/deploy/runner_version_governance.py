from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_VERSION_STATE_REL = "docs/evidence/runtime-results/handoff/version_state.json"
_PHASE_TRACKING_REL = "docs/evidence/runtime-results/handoff/phase_release_tracking.json"
_CONFIG_VERSION = _REPO_ROOT / "config" / "version.json"
_MAX_OUTPUT_BYTES = 256 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "VERSION_GOVERNANCE_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, "VERSION_GOVERNANCE_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "VERSION_GOVERNANCE_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "VERSION_GOVERNANCE_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _parse_version(v: str) -> tuple[int, int, int] | None:
    parts = str(v).split(".")
    if len(parts) != 3:
        return None
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None


def _bump(v: str, level: str) -> str | None:
    p = _parse_version(v)
    if p is None:
        return None
    major, minor, patch = p
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "major":
        return f"{major + 1}.0.0"
    return None


def _classify_bump(*, changes: list[str]) -> str:
    c = {x.strip().lower() for x in changes}
    if c & {"architecture", "platform_production", "runtime_engine", "deploy_engine", "rescue_production"}:
        return "major"
    if c & {"strict_mode_module", "evidence_chain", "api_route", "safety_gate", "test_matrix"}:
        return "minor"
    return "patch"


def build_version_governance_state(
    *,
    previous_version: str = "1.5.0",
    strict_mode_phase: str = "laptop_failure_finalization_chain",
    phase_status: str = "completed",
    release_readiness: str = "internal_testing",
    completed_modules: list[str] | None = None,
    evidence_artifacts: list[str] | None = None,
    test_status: str = "green",
    changes: list[str] | None = None,
    explicit_overwrite: bool = False,
) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []
    out_path, err = _resolve_handoff(_VERSION_STATE_REL)
    if err or out_path is None:
        return {
            "state_status": "blocked",
            "state_file_path": _VERSION_STATE_REL,
            "warnings": [],
            "errors": [err or "VERSION_GOVERNANCE_OUTPUT_PATH_INVALID"],
            "blocked_reasons": [err or "VERSION_GOVERNANCE_OUTPUT_PATH_INVALID"],
        }
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return {
            "state_status": "blocked",
            "state_file_path": _VERSION_STATE_REL,
            "warnings": [],
            "errors": ["VERSION_GOVERNANCE_EXISTS_NO_OVERWRITE"],
            "blocked_reasons": ["VERSION_GOVERNANCE_EXISTS_NO_OVERWRITE"],
        }

    bump_kind = _classify_bump(changes=changes or [])
    next_version = _bump(previous_version, bump_kind)
    if next_version is None:
        blocked_reasons.append("VERSION_GOVERNANCE_PREVIOUS_VERSION_INVALID")
        return _emit(out_path, "blocked", {}, blocked_reasons, warnings)

    body = {
        "version_schema_version": 1,
        "current_version": next_version,
        "previous_version": previous_version,
        "strict_mode_phase": strict_mode_phase,
        "phase_status": phase_status,
        "release_readiness": release_readiness,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "completed_modules": completed_modules or [],
        "evidence_artifacts": evidence_artifacts or [],
        "test_status": test_status,
        "recommended_bump": bump_kind,
        "consistency_check_triggerable": True,
    }
    try:
        _write_config_version(
            project_version=next_version,
            release_stage=release_readiness,
            version_track="strict_mode_laptop_failure_pipeline",
        )
        _write_phase_tracking(
            phase_name=strict_mode_phase,
            phase_status=phase_status,
            version=next_version,
            test_status=test_status,
            release_level=release_readiness,
        )
    except OSError:
        blocked_reasons.append("VERSION_GOVERNANCE_SIDEWRITE_FAILED")
        return _emit(out_path, "blocked", body, blocked_reasons, warnings)
    return _emit(out_path, "ok", body, blocked_reasons, warnings)


def _write_config_version(*, project_version: str, release_stage: str, version_track: str) -> None:
    body = {
        "schema_version": 1,
        "project_version": project_version,
        "release_stage": release_stage,
        "version_track": version_track,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version_source_of_truth": True,
    }
    _CONFIG_VERSION.parent.mkdir(parents=True, exist_ok=True)
    tmp = _CONFIG_VERSION.with_name(_CONFIG_VERSION.name + ".tmp")
    tmp.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(_CONFIG_VERSION)


def _write_phase_tracking(
    *, phase_name: str, phase_status: str, version: str, test_status: str, release_level: str
) -> None:
    path, err = _resolve_handoff(_PHASE_TRACKING_REL)
    if err or path is None:
        raise OSError("invalid tracking path")
    existing: dict[str, Any] = {"tracking_schema_version": 1, "tracked_phases": []}
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                existing = {"tracking_schema_version": 1, "tracked_phases": []}
        except Exception:
            existing = {"tracking_schema_version": 1, "tracked_phases": []}
    tracked = existing.get("tracked_phases")
    if not isinstance(tracked, list):
        tracked = []
    phase_row = {
        "phase_name": phase_name,
        "phase_status": phase_status,
        "version": version,
        "test_status": test_status,
        "evidence_complete": phase_status == "completed",
        "release_level": release_level,
    }
    replaced = False
    out_rows: list[dict[str, Any]] = []
    for row in tracked:
        if isinstance(row, dict) and str(row.get("phase_name") or "") == phase_name:
            out_rows.append(phase_row)
            replaced = True
        elif isinstance(row, dict):
            out_rows.append(row)
    if not replaced:
        out_rows.append(phase_row)
    payload = {
        "tracking_schema_version": 1,
        "tracked_phases": out_rows,
    }
    _atomic_write(path, json.dumps(payload, indent=2, sort_keys=True))


def _emit(out_path: Path, state_status: str, body: dict[str, Any], blocked_reasons: list[str], warnings: list[str]) -> dict[str, Any]:
    text = json.dumps(body, indent=2, sort_keys=True)
    if body and len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return {
            "state_status": "blocked",
            "state_file_path": _VERSION_STATE_REL,
            "warnings": [],
            "errors": ["VERSION_GOVERNANCE_OUTPUT_TOO_LARGE"],
            "blocked_reasons": ["VERSION_GOVERNANCE_OUTPUT_TOO_LARGE"],
        }
    if body:
        try:
            _atomic_write(out_path, text)
        except OSError:
            return {
                "state_status": "blocked",
                "state_file_path": _VERSION_STATE_REL,
                "warnings": [],
                "errors": ["VERSION_GOVERNANCE_WRITE_FAILED"],
                "blocked_reasons": ["VERSION_GOVERNANCE_WRITE_FAILED"],
            }
    return {
        "state_status": state_status,
        "state_file_path": _VERSION_STATE_REL,
        "state": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(blocked_reasons)) if state_status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
