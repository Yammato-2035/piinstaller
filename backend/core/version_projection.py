"""
Versionsebenen: Setuphelfer-Projektversion (X.Y.Z.W) vs. Cargo/Tauri-Semver (X.Y.Z).

Cargo und Tauri verlangen gueltiges Semver (major.minor.patch). Vierstellige
Projektversionen (Patch W) werden nicht als Cargo-Version akzeptiert.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PROJECT_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)\.(\d+)$")


@dataclass(frozen=True)
class VersionProjection:
    """Kanonische Abbildung project_version -> Packaging-/Semver-Ebenen."""

    project_version: str
    semver_package_version: str
    patch_component: int
    deb_upstream_version: str
    deb_package_revision: str
    rpm_version: str
    rpm_release: str
    cargo_compile_label: str

    @property
    def deb_version(self) -> str:
        return f"{self.deb_upstream_version}-{self.deb_package_revision}"

    def expected_artifact_names(self, *, product: str = "SetupHelfer") -> dict[str, str]:
        pv = self.project_version
        return {
            "deb": f"{product}_{pv}_amd64.deb",
            "rpm": f"{product}-{pv}-{self.rpm_release}.x86_64.rpm",
            "appimage": f"{product}_{pv}_amd64.AppImage",
        }

    def tauri_default_artifact_names(self, *, product: str = "SetupHelfer") -> dict[str, str]:
        """Dateinamen, die Tauri/Cargo nativ aus semver_package_version erzeugt."""
        sv = self.semver_package_version
        return {
            "deb": f"{product}_{sv}_amd64.deb",
            "rpm": f"{product}-{sv}-{self.rpm_release}.x86_64.rpm",
            "appimage": f"{product}_{sv}_amd64.AppImage",
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "setuphelfer_project_version": self.project_version,
            "semver_package_version": self.semver_package_version,
            "patch_component": self.patch_component,
            "deb_upstream_version": self.deb_upstream_version,
            "deb_package_revision": self.deb_package_revision,
            "deb_version": self.deb_version,
            "rpm_version": self.rpm_version,
            "rpm_release": self.rpm_release,
            "cargo_compile_label": self.cargo_compile_label,
            "expected_artifact_names": self.expected_artifact_names(),
            "tauri_default_artifact_names": self.tauri_default_artifact_names(),
            "mapping_rule": (
                "Cargo/Tauri compile with semver_package_version (X.Y.Z); "
                "bundle filenames SHOULD use setuphelfer_project_version (X.Y.Z.W). "
                "Legacy Tauri output with semver-only names is a documented projection, not drift."
            ),
        }


def parse_project_version(project_version: str) -> tuple[int, int, int, int]:
    m = _PROJECT_VERSION_RE.match(str(project_version or "").strip())
    if not m:
        raise ValueError(f"invalid_project_version:{project_version!r}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))


def project_version_from_repo(repo_root: Path) -> str:
    path = repo_root / "config" / "version.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("version_json_not_object")
    pv = str(data.get("project_version") or "").strip()
    if not pv:
        raise ValueError("project_version_missing")
    return pv


def build_version_projection(project_version: str) -> VersionProjection:
    x, y, z, w = parse_project_version(project_version)
    semver = f"{x}.{y}.{z}"
    return VersionProjection(
        project_version=project_version,
        semver_package_version=semver,
        patch_component=w,
        deb_upstream_version=project_version,
        deb_package_revision="1",
        rpm_version=project_version,
        rpm_release="1",
        cargo_compile_label=f"v{semver}",
    )


def build_version_projection_from_repo(repo_root: Path) -> VersionProjection:
    return build_version_projection(project_version_from_repo(repo_root))


def classify_bundle_filename(name: str, projection: VersionProjection) -> dict[str, Any]:
    """Ordnet einen Bundle-Dateinamen der Projekt- oder Semver-Projektion zu."""
    expected = projection.expected_artifact_names()
    legacy = projection.tauri_default_artifact_names()
    if name in expected.values():
        return {"name": name, "match": "project_version", "ok": True, "misleading": False}
    if name in legacy.values():
        return {
            "name": name,
            "match": "semver_projection",
            "ok": True,
            "misleading": projection.patch_component > 0,
            "maps_to_project_version": projection.project_version,
        }
    return {"name": name, "match": "unknown", "ok": False, "misleading": True}


def check_packaging_artifacts(
    *,
    repo_root: Path,
    bundle_root: Path | None = None,
) -> dict[str, Any]:
    """
    Prueft Tauri-Bundle-Artefakte gegen VersionProjection.
    Fehlen Artefakte: ok (kein Build). Semver-only bei W>0: warn, nicht fail.
    Unbekannte Version in Dateiname: fail.
    """
    projection = build_version_projection_from_repo(repo_root)
    root = repo_root.expanduser().resolve()
    bundle = bundle_root or (root / "frontend/src-tauri/target/release/bundle")
    warnings: list[str] = []
    errors: list[str] = []
    found: list[dict[str, Any]] = []
    stale_ignored: list[str] = []

    pv = projection.project_version
    sv = projection.semver_package_version

    for kind, pattern in (
        ("deb", "deb/*.deb"),
        ("rpm", "rpm/*.rpm"),
        ("appimage", "appimage/*.AppImage"),
    ):
        if not bundle.is_dir():
            continue
        for path in sorted(bundle.glob(pattern)):
            name = path.name
            if pv not in name and sv not in name:
                stale_ignored.append(name)
                continue
            info = classify_bundle_filename(name, projection)
            info["kind"] = kind
            info["path"] = str(path)
            found.append(info)
            if not info.get("ok"):
                errors.append(f"{kind}:{path.name}:unknown_version_in_filename")
            elif info.get("misleading"):
                warnings.append(
                    f"{kind}:{path.name}:semver_projection_only;"
                    f"project_version={projection.project_version};"
                    f"run scripts/rename-tauri-bundle-artifacts.sh after tauri build"
                )

    if stale_ignored:
        warnings.append(
            f"stale_bundle_artifacts_ignored:{len(stale_ignored)};"
            f"not_matching_current_{pv}_or_{sv}"
        )

    ok = not errors
    status = "ok"
    if errors:
        status = "blocked"
    elif warnings:
        status = "warn"

    return {
        "ok": ok,
        "status": status,
        "projection": projection.to_public_dict(),
        "bundle_root": str(bundle),
        "artifacts": found,
        "stale_ignored": stale_ignored[:12],
        "warnings": warnings,
        "errors": errors,
    }
