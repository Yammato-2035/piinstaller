"""
Workspace- und Runtime-Version-Konsistenz (Source of Truth: config/version.json).

Keine Secrets. Wird von check-backend-version-gate.sh und deploy-runtime-verify genutzt.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from core.version_projection import build_version_projection

VERSION_JSON_REL = "config/version.json"
VERSION_TXT_REL = "VERSION"
ROOT_PACKAGE_REL = "package.json"
FRONTEND_PACKAGE_REL = "frontend/package.json"
FRONTEND_LOCK_REL = "frontend/package-lock.json"
TAURI_CONF_REL = "frontend/src-tauri/tauri.conf.json"
CARGO_TOML_REL = "frontend/src-tauri/Cargo.toml"

_CARGO_VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)


def semver_triple(project_version: str) -> str:
    """1.7.3.1 -> 1.7.3 (Tauri/Cargo Semver)."""
    try:
        from core.version_projection import build_version_projection

        return build_version_projection(project_version).semver_package_version
    except ValueError:
        parts = str(project_version or "").strip().split(".")
        if len(parts) >= 3:
            return ".".join(parts[:3])
        return str(project_version or "").strip()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _read_text_version(path: Path) -> str | None:
    try:
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8").strip()
        return text or None
    except OSError:
        return None


def _cargo_version(path: Path) -> str | None:
    try:
        if not path.is_file():
            return None
        m = _CARGO_VERSION_RE.search(path.read_text(encoding="utf-8"))
        return m.group(1) if m else None
    except OSError:
        return None


def _lockfile_root_version(path: Path) -> str | None:
    data = _read_json(path)
    if not data:
        return None
    pkg = data.get("packages")
    if isinstance(pkg, dict):
        root_pkg = pkg.get("")
        if isinstance(root_pkg, dict):
            v = str(root_pkg.get("version") or "").strip()
            if v:
                return v
    v = str(data.get("version") or "").strip()
    return v or None


def collect_version_sources(repo_root: Path) -> dict[str, str | None]:
    root = repo_root.expanduser().resolve()
    cfg = _read_json(root / VERSION_JSON_REL) or {}
    canonical = str(cfg.get("project_version") or "").strip() or None
    tauri_expected = semver_triple(canonical) if canonical else None
    return {
        "canonical": canonical,
        "config/version.json": canonical,
        "VERSION": _read_text_version(root / VERSION_TXT_REL),
        "package.json": str((_read_json(root / ROOT_PACKAGE_REL) or {}).get("version") or "").strip() or None,
        "frontend/package.json": str((_read_json(root / FRONTEND_PACKAGE_REL) or {}).get("version") or "").strip() or None,
        "frontend/package-lock.json": _lockfile_root_version(root / FRONTEND_LOCK_REL),
        "frontend/src-tauri/tauri.conf.json": str((_read_json(root / TAURI_CONF_REL) or {}).get("version") or "").strip() or None,
        "frontend/src-tauri/Cargo.toml": _cargo_version(root / CARGO_TOML_REL),
        "tauri_semver_expected": tauri_expected,
    }


def _mismatch(label: str, expected: str | None, actual: str | None) -> str | None:
    if expected is None:
        return None
    if actual is None:
        return f"{label}:missing"
    if actual != expected:
        return f"{label}:expected={expected}:actual={actual}"
    return None


def check_workspace_consistency(repo_root: Path) -> dict[str, Any]:
    sources = collect_version_sources(repo_root)
    canonical = sources.get("canonical")
    tauri_expected = sources.get("tauri_semver_expected")
    mismatches: list[str] = []

    for label, expected in (
        ("config/version.json", canonical),
        ("VERSION", canonical),
        ("package.json", canonical),
        ("frontend/package.json", canonical),
        ("frontend/package-lock.json", canonical),
        ("frontend/src-tauri/tauri.conf.json", tauri_expected),
        ("frontend/src-tauri/Cargo.toml", tauri_expected),
    ):
        mm = _mismatch(label, expected, sources.get(label))
        if mm:
            mismatches.append(mm)

    if not canonical:
        mismatches.append("config/version.json:project_version_missing")

    projection = None
    if canonical:
        try:
            projection = build_version_projection(canonical).to_public_dict()
        except ValueError:
            mismatches.append("config/version.json:invalid_project_version_format")

    return {
        "ok": not mismatches,
        "scope": "workspace",
        "canonical": canonical,
        "tauri_semver_expected": tauri_expected,
        "version_projection": projection,
        "sources": {k: v for k, v in sources.items() if k not in ("canonical", "tauri_semver_expected")},
        "mismatches": mismatches,
    }


def check_runtime_consistency(
    *,
    workspace_root: Path,
    runtime_root: Path,
    api_project_version: str | None = None,
) -> dict[str, Any]:
    ws = check_workspace_consistency(workspace_root)
    rt_sources = collect_version_sources(runtime_root)
    canonical = ws.get("canonical")
    tauri_expected = ws.get("tauri_semver_expected")
    mismatches: list[str] = list(ws.get("mismatches") or [])

    for label in (
        "config/version.json",
        "VERSION",
        "package.json",
        "frontend/package.json",
        "frontend/package-lock.json",
        "frontend/src-tauri/tauri.conf.json",
        "frontend/src-tauri/Cargo.toml",
    ):
        expected = canonical if label not in (
            "frontend/src-tauri/tauri.conf.json",
            "frontend/src-tauri/Cargo.toml",
        ) else tauri_expected
        mm = _mismatch(f"runtime/{label}", expected, rt_sources.get(label))
        if mm:
            mismatches.append(mm)

    if api_project_version is not None and canonical and api_project_version != canonical:
        mismatches.append(
            f"api/project_version:expected={canonical}:actual={api_project_version}"
        )

    return {
        "ok": not mismatches,
        "scope": "runtime",
        "canonical": canonical,
        "tauri_semver_expected": tauri_expected,
        "workspace_sources": ws.get("sources"),
        "runtime_sources": {k: v for k, v in rt_sources.items() if k not in ("canonical", "tauri_semver_expected")},
        "api_project_version": api_project_version,
        "mismatches": mismatches,
    }
