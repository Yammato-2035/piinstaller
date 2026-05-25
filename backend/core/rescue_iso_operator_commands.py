from __future__ import annotations

from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _build_root(repo_root: Path | None = None) -> Path:
    repo = repo_root or _repo_root()
    return (repo / "build" / "rescue" / "live-build" / "setuphelfer-rescue-live").resolve(strict=False)


def _ensure_expected_build_root(path: Path, repo_root: Path) -> str | None:
    expected = (repo_root / "build" / "rescue" / "live-build" / "setuphelfer-rescue-live").resolve(strict=False)
    try:
        path.resolve(strict=False).relative_to(expected)
    except (OSError, ValueError):
        return "BUILD_ROOT_OUTSIDE_ALLOWED_TREE"
    return None


def build_sudo_clean_commands(*, repo_root: Path | None = None) -> dict[str, Any]:
    repo = (repo_root or _repo_root()).resolve(strict=False)
    build_root = _build_root(repo)
    err = _ensure_expected_build_root(build_root, repo)
    commands: list[str] = []
    warnings: list[str] = []
    if err is None:
        commands = [
            f'cd "{build_root}"',
            "sudo rm -rf .build chroot cache binary local",
        ]
        warnings.extend(
            [
                "Nur ausführen, wenn Pfad exakt geprüft wurde.",
                "Kein lb clean verwenden: auto/clean darf keine rekursive live-build-Ausführung triggern.",
            ]
        )
    else:
        warnings.append("Pfadprüfung fehlgeschlagen; keine Kommandos erzeugt.")
    return {
        "status": "operator_required" if commands else "blocked",
        "warning": "Nur ausführen, wenn Pfad exakt geprüft wurde.",
        "repo_root": str(repo),
        "build_root": str(build_root),
        "commands": commands,
        "warnings": warnings,
        "errors": [err] if err else [],
    }


def build_operator_build_commands(*, repo_root: Path | None = None) -> dict[str, Any]:
    repo = (repo_root or _repo_root()).resolve(strict=False)
    build_root = _build_root(repo)
    err = _ensure_expected_build_root(build_root, repo)
    commands: list[str] = []
    warnings: list[str] = []
    if err is None:
        commands = [
            f'cd "{build_root}"',
            "./auto/config",
            "sudo lb build noauto",
        ]
        warnings.extend(
            [
                "Nur ausführen, wenn Pfad exakt geprüft wurde.",
                "USB-Schreiben, dd, mkfs und Partition-Write bleiben verboten.",
            ]
        )
    else:
        warnings.append("Pfadprüfung fehlgeschlagen; keine Kommandos erzeugt.")
    return {
        "status": "operator_required" if commands else "blocked",
        "warning": "Nur ausführen, wenn Pfad exakt geprüft wurde.",
        "repo_root": str(repo),
        "build_root": str(build_root),
        "commands": commands,
        "warnings": warnings,
        "errors": [err] if err else [],
    }
