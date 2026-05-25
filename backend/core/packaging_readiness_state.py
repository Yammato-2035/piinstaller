"""
Read-only Packaging-Readiness fuer das Development Dashboard.

Keine Paketinstallation, kein AppImage-Start, keine Root-Aktion.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc

DEFAULT_RUNTIME_ROOT = Path("/opt/setuphelfer")
_BUNDLE_ROOT_REL = Path("frontend/src-tauri/target/release/bundle")
_ARTIFACT_PATTERNS: dict[str, tuple[str, ...]] = {
    "deb": ("deb/*.deb",),
    "rpm": ("rpm/*.rpm",),
    "appimage": ("appimage/*.AppImage",),
}


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _collect_artifacts(bundle_root: Path, kind: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for pattern in _ARTIFACT_PATTERNS.get(kind, ()):
        for path in sorted(bundle_root.glob(pattern)):
            try:
                size_bytes = int(path.stat().st_size)
            except OSError:
                size_bytes = None
            items.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "kind": kind,
                    "size_bytes": size_bytes,
                }
            )
    return items[:20]


def build_packaging_readiness_state(*, runtime_root: Path | None = None) -> dict[str, Any]:
    root = (runtime_root or DEFAULT_RUNTIME_ROOT).resolve(strict=False)
    bundle_root = (root / _BUNDLE_ROOT_REL).resolve(strict=False)

    artifacts: dict[str, list[dict[str, Any]]] = {
        kind: _collect_artifacts(bundle_root, kind) for kind in _ARTIFACT_PATTERNS
    }
    deb_present = bool(artifacts["deb"])
    any_present = any(artifacts[kind] for kind in artifacts)

    if deb_present:
        status = "green"
        summary = "Packaging-Artefakte fuer manuelle Installationspruefung vorhanden."
    elif any_present:
        status = "yellow"
        summary = "Nur optionale Packaging-Artefakte vorhanden; DEB-Readiness fehlt."
    else:
        status = "yellow"
        summary = "Noch keine Packaging-Artefakte gefunden."

    return {
        "status": status,
        "generated_at": _now_iso(),
        "runtime_root": str(root),
        "bundle_root": str(bundle_root),
        "artifacts": artifacts,
        "deb_ready": deb_present,
        "rpm_ready": bool(artifacts["rpm"]),
        "appimage_ready": bool(artifacts["appimage"]),
        "install_test_passed": False,
        "install_test_pending": True,
        "summary": summary,
        "evidence_path": "docs/evidence/dev-dashboard/PROJECT_OVERVIEW_DASHBOARD_INTEGRATION_RESULT.md",
        "forbidden_actions": {
            "dpkg_install_allowed": False,
            "rpm_install_allowed": False,
            "appimage_start_allowed": False,
            "apt_install_allowed": False,
            "apt_upgrade_allowed": False,
            "root_actions_allowed": False,
        },
    }
