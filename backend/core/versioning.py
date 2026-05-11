from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VERSION_FILE = _REPO_ROOT / "config" / "version.json"
_VALID_RELEASE_STAGES = {"internal_testing", "staging", "production_ready"}


@dataclass(frozen=True)
class ProjectVersionInfo:
    project_version: str
    release_stage: str
    version_track: str


def load_project_version(*, version_file: Path | None = None) -> ProjectVersionInfo:
    target = version_file or _VERSION_FILE
    raw = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("version config must be an object")
    if raw.get("version_source_of_truth") is not True:
        raise ValueError("version_source_of_truth must be true")
    version = str(raw.get("project_version") or "").strip()
    stage = str(raw.get("release_stage") or "").strip()
    track = str(raw.get("version_track") or "").strip()
    if not version:
        raise ValueError("project_version missing")
    if stage not in _VALID_RELEASE_STAGES:
        raise ValueError("invalid release_stage")
    if not track:
        raise ValueError("version_track missing")
    return ProjectVersionInfo(project_version=version, release_stage=stage, version_track=track)


def get_project_version() -> str:
    return load_project_version().project_version


def get_release_stage() -> str:
    return load_project_version().release_stage


def validate_version_state(state: dict[str, Any]) -> tuple[bool, list[str]]:
    errs: list[str] = []
    if not isinstance(state, dict):
        return False, ["version_state_not_object"]
    cur = str(state.get("current_version") or "").strip()
    prev = str(state.get("previous_version") or "").strip()
    phase_status = str(state.get("phase_status") or "").strip()
    test_status = str(state.get("test_status") or "").strip()
    release_readiness = str(state.get("release_readiness") or "").strip()
    if not cur:
        errs.append("missing_current_version")
    if not prev:
        errs.append("missing_previous_version")
    if phase_status not in {"completed", "in_progress", "blocked"}:
        errs.append("invalid_phase_status")
    if test_status not in {"green", "yellow", "red"}:
        errs.append("invalid_test_status")
    if release_readiness not in _VALID_RELEASE_STAGES:
        errs.append("invalid_release_readiness")
    return len(errs) == 0, errs
