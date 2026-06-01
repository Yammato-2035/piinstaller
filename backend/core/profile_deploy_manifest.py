"""Profile-aware deploy manifests and drift evaluation."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def profile_manifest_path(profile: str, root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / "deploy" / "manifests" / f"{profile}.manifest.json"


def load_profile_manifest(profile: str, root: Path | None = None) -> dict[str, Any]:
    path = profile_manifest_path(profile, root)
    if not path.is_file():
        return {"profile": profile, "missing": True}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"profile": profile, "invalid": True}
    except json.JSONDecodeError:
        return {"profile": profile, "invalid": True}


def manifest_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def evaluate_profile_runtime_paths(
    *,
    profile: str,
    runtime_root: Path,
    root: Path | None = None,
) -> dict[str, Any]:
    """Check forbidden paths from profile manifest exist under runtime_root."""
    manifest = load_profile_manifest(profile, root)
    forbidden = manifest.get("forbidden_runtime_paths") or []
    violations: list[str] = []
    for rel in forbidden:
        rel_s = str(rel).replace("\\", "/").lstrip("/")
        if (runtime_root / rel_s).exists():
            violations.append(rel_s)
    status = "green" if not violations else "red"
    return {
        "status": status,
        "forbidden_runtime_present": violations,
        "manifest_profile": profile,
    }


def build_profile_manifest_data(profile: str, root: Path | None = None) -> dict[str, Any]:
    """Merge common + profile manifest metadata for generator output."""
    base = root or repo_root()
    common = load_profile_manifest("common", base)
    spec = load_profile_manifest(profile, base)
    include = list(dict.fromkeys((common.get("include") or []) + (spec.get("include") or [])))
    exclude = list(dict.fromkeys((common.get("exclude") or []) + (spec.get("exclude") or [])))
    return {
        "manifest_schema_version": 1,
        "profile": profile,
        "generated_at": datetime.now(UTC).isoformat(),
        "include": include,
        "exclude": exclude,
        "required_paths": spec.get("required_paths") or [],
        "forbidden_runtime_paths": spec.get("forbidden_runtime_paths") or [],
        "required_api_paths": spec.get("required_api_paths") or [],
        "forbidden_api_paths": spec.get("forbidden_api_paths") or [],
        "allowed_capabilities": spec.get("allowed_capabilities") or [],
        "forbidden_capabilities": spec.get("forbidden_capabilities") or [],
        "public_exposure_allowed": bool(spec.get("public_exposure_allowed", False)),
    }
