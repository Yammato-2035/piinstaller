"""
System Runtime Info — read-only runtime/installation/profile probes for system status facade.

Phase G.13: extracted from ``app`` helpers; facade delegates only, no ``import app``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.install_paths import get_backend_runtime_dir, get_config_dir, get_opt_install_dir, is_dev_mode
from core.versioning import get_project_version

SYSTEM_RUNTIME_INFO_VERSION = 1

_VALID_PROFILE_LEVELS = frozenset({"beginner", "advanced", "developer"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_version_from_path(root: Path) -> str | None:
    try:
        vf = root / "VERSION"
        if vf.exists():
            return vf.read_text(encoding="utf-8").strip() or None
    except OSError:
        pass
    return None


def get_app_edition() -> str:
    """repo | release from APP_EDITION env (same rules as legacy app.get_app_edition)."""
    raw = (os.environ.get("APP_EDITION") or "").strip().lower()
    if raw in ("repo", "release"):
        return raw
    return "release"


def _user_profile_primary_path() -> Path:
    return get_config_dir() / "user_profile.json"


def _user_profile_fallback_path() -> Path:
    return Path.home() / ".config" / "setuphelfer" / "user_profile.json"


def _user_profile_candidate_paths() -> list[Path]:
    primary = _user_profile_primary_path()
    fallback = _user_profile_fallback_path()
    try:
        if primary.resolve() == fallback.resolve():
            return [primary]
    except OSError:
        pass
    return [primary, fallback]


def collect_user_profiles_from_disk() -> list[tuple[str, float, str, Path]]:
    """(updated_at, mtime, experience_level, path) for readable profile files."""
    out: list[tuple[str, float, str, Path]] = []
    for path in _user_profile_candidate_paths():
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8") or "{}")
            if not isinstance(data, dict):
                continue
            level = str(data.get("experience_level") or "beginner").lower()
            if level not in _VALID_PROFILE_LEVELS:
                level = "beginner"
            updated_at = str(data.get("updated_at") or _now_iso())
            mtime = path.stat().st_mtime
            out.append((updated_at, mtime, level, path))
        except OSError:
            continue
    return out


@dataclass(frozen=True)
class UserProfileInfo:
    experience_level: str
    updated_at: str

    def as_dict(self) -> dict[str, str]:
        return {"experience_level": self.experience_level, "updated_at": self.updated_at}


def build_runtime_info() -> dict[str, Any]:
    """Backend version, edition, runtime path (read-only)."""
    try:
        version = str(get_project_version() or "unknown")
    except Exception:
        version = "unknown"
    edition = get_app_edition()
    runtime_path = str(get_backend_runtime_dir().resolve())
    return {
        "version": version,
        "edition": edition,
        "runtime_path": runtime_path,
        "status_hint": "ok" if version != "unknown" else "unknown",
    }


def build_installation_info(*, repo_root: Path | None = None) -> dict[str, Any]:
    """Source vs /opt installation drift (read-only)."""
    root = repo_root or Path(__file__).resolve().parent.parent.parent
    source_version = str(get_project_version() or "unknown")
    source_path = str(root)
    opt_dir = get_opt_install_dir()
    installed_version = _read_version_from_path(opt_dir) if opt_dir.exists() else None
    installed_path = str(opt_dir) if opt_dir.exists() else None
    try:
        is_source_opt = root.resolve() == opt_dir.resolve()
    except OSError:
        is_source_opt = False
    update_available = not is_source_opt and (
        installed_version is None or installed_version != source_version
    )
    deploy_script = root / "scripts" / "deploy-to-opt.sh"
    return {
        "source_path": source_path,
        "source_version": source_version,
        "installed_path": installed_path,
        "installed_version": installed_version,
        "update_available": update_available,
        "is_running_from_opt": is_source_opt,
        "can_run_deploy": deploy_script.is_file(),
        "deploy_script": str(deploy_script),
        "dev_mode": is_dev_mode(),
    }


def build_profile_info() -> dict[str, Any]:
    """User experience profile from disk (read-only)."""
    level = "beginner"
    updated_at = _now_iso()
    warnings: list[str] = []
    try:
        cands = collect_user_profiles_from_disk()
        if cands:
            cands.sort(key=lambda x: (x[0], x[1]), reverse=True)
            updated_at, _mtime, level, _path = cands[0]
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"profile_partial:{exc}")
    profile = UserProfileInfo(experience_level=level, updated_at=updated_at)
    return {
        "profile": profile.as_dict(),
        "warnings": warnings,
    }


def build_runtime_diagnostics() -> dict[str, Any]:
    return {
        "core_version": SYSTEM_RUNTIME_INFO_VERSION,
        "core_module": "core.system_runtime_info",
        "public_functions": [
            "build_runtime_info",
            "build_installation_info",
            "build_profile_info",
            "build_runtime_diagnostics",
            "get_app_edition",
            "collect_user_profiles_from_disk",
        ],
        "config_dir": str(get_config_dir()),
        "opt_install_dir": str(get_opt_install_dir()),
        "imports_app": False,
        "read_only": True,
        "writes_allowed": False,
    }
