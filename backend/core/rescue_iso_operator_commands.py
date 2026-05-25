from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

_RUNTIME_ROOT = Path("/opt/setuphelfer")
_DEFAULT_WORKSPACE_ROOT = Path("/home/volker/piinstaller")
_BUILD_TREE_REL = Path("build/rescue/live-build/setuphelfer-rescue-live")
_TEMP_BUNDLE_REL = Path("build/rescue/temp-runtime/setuphelfer-rescue-runtime")
_LOG_ROOT_REL = Path("build/rescue/logs/controlled-iso-build")
_SUMMARY_REL = Path("docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json")


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _resolve(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _path_is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except (OSError, ValueError):
        return False


def _is_opt_runtime_root(path: Path) -> bool:
    current = _resolve(path)
    expected = _resolve(_RUNTIME_ROOT)
    return current == expected or _path_is_within(expected, current)


def _git_text(path: Path, *args: str) -> str | None:
    safe_root = _resolve(path)
    try:
        proc = subprocess.run(
            ["git", "-c", f"safe.directory={safe_root}", "-C", str(path), *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    value = (proc.stdout or "").strip()
    return value or None


def _git_top_level(path: Path) -> Path | None:
    raw = _git_text(path, "rev-parse", "--show-toplevel")
    if not raw:
        return None
    return _resolve(Path(raw))


def _configured_workspace_root(runtime_root: Path) -> Path:
    try:
        from core.dev_dashboard import _effective_workspace_root
    except Exception:
        return _resolve(runtime_root)
    try:
        return _resolve(_effective_workspace_root(runtime_root))
    except Exception:
        return _resolve(runtime_root)


def _allowed_workspace_roots(runtime_root: Path) -> tuple[Path, ...]:
    roots = [_resolve(_DEFAULT_WORKSPACE_ROOT)]
    resolved_runtime = _resolve(runtime_root)
    if not _is_opt_runtime_root(resolved_runtime):
        roots.append(resolved_runtime)
    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root)
        if key in seen:
            continue
        seen.add(key)
        unique.append(root)
    return tuple(unique)


def resolve_rescue_iso_paths(*, repo_root: Path | None = None) -> dict[str, Any]:
    runtime_root = _resolve(repo_root or _repo_root())
    workspace_root = _configured_workspace_root(runtime_root)
    build_root = _resolve(workspace_root / _BUILD_TREE_REL)
    temp_bundle_root = _resolve(workspace_root / _TEMP_BUNDLE_REL)
    log_root = _resolve(workspace_root / _LOG_ROOT_REL)
    summary_path = _resolve(workspace_root / _SUMMARY_REL)
    errors: list[str] = []
    warnings: list[str] = []

    if _is_opt_runtime_root(workspace_root):
        warnings.append("WORKSPACE_PATH_POINTS_TO_RUNTIME_OPT")

    if not any(workspace_root == allowed for allowed in _allowed_workspace_roots(runtime_root)):
        errors.append("WORKSPACE_NOT_ALLOWLISTED")

    try:
        workspace_exists = workspace_root.is_dir()
    except OSError:
        workspace_exists = False
    if not workspace_exists:
        errors.append("WORKSPACE_MISSING")

    git_top = _git_top_level(workspace_root)
    if git_top is None:
        errors.append("WORKSPACE_NOT_GIT_REPO")
    elif git_top != workspace_root:
        errors.append("WORKSPACE_GIT_TOPLEVEL_MISMATCH")

    if not _path_is_within(workspace_root, build_root.parent):
        errors.append("BUILD_TREE_PARENT_OUTSIDE_WORKSPACE")
    if not _path_is_within(workspace_root, temp_bundle_root.parent):
        errors.append("TEMP_BUNDLE_PARENT_OUTSIDE_WORKSPACE")
    if not _path_is_within(workspace_root, log_root):
        errors.append("LOG_ROOT_OUTSIDE_WORKSPACE")
    if not _path_is_within(workspace_root, summary_path.parent):
        errors.append("SUMMARY_PATH_OUTSIDE_WORKSPACE")

    workspace_head = _git_text(workspace_root, "rev-parse", "--short", "HEAD")
    workspace_branch = _git_text(workspace_root, "branch", "--show-current")

    if errors:
        path_status = "blocked"
    elif warnings:
        path_status = "review_required"
    else:
        path_status = "ok"

    return {
        "runtime_path": str(runtime_root),
        "workspace_path": str(workspace_root),
        "build_tree_path": str(build_root),
        "temp_runtime_bundle_path": str(temp_bundle_root),
        "logs_path": str(log_root),
        "summary_path": str(summary_path),
        "path_mode": "workspace_build_runtime_opt" if _is_opt_runtime_root(runtime_root) else "workspace_build_runtime_local",
        "path_status": path_status,
        "errors": errors,
        "warnings": warnings,
        "workspace_head": workspace_head,
        "workspace_branch": workspace_branch,
    }


def build_sudo_clean_commands(*, repo_root: Path | None = None) -> dict[str, Any]:
    paths = resolve_rescue_iso_paths(repo_root=repo_root)
    build_root = Path(paths["build_tree_path"]).resolve(strict=False)
    commands: list[str] = []
    warnings: list[str] = []
    errors = list(paths.get("errors") or [])
    warnings.extend(str(item) for item in (paths.get("warnings") or []))
    if paths.get("path_status") == "ok":
        commands = [
            f'cd "{build_root}"',
            "sudo rm -rf .build chroot cache binary local "
            "config/includes.chroot/opt/setuphelfer-rescue "
            "config/includes.chroot/opt/setuphelfer-rescue.old.*",
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
        "runtime_path": str(paths["runtime_path"]),
        "workspace_path": str(paths["workspace_path"]),
        "path_mode": str(paths["path_mode"]),
        "path_status": str(paths["path_status"]),
        "build_root": str(build_root),
        "commands": commands,
        "warnings": warnings,
        "errors": errors,
    }


def build_operator_build_commands(*, repo_root: Path | None = None) -> dict[str, Any]:
    paths = resolve_rescue_iso_paths(repo_root=repo_root)
    build_root = Path(paths["build_tree_path"]).resolve(strict=False)
    commands: list[str] = []
    warnings: list[str] = []
    errors = list(paths.get("errors") or [])
    warnings.extend(str(item) for item in (paths.get("warnings") or []))
    if paths.get("path_status") == "ok":
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
        "runtime_path": str(paths["runtime_path"]),
        "workspace_path": str(paths["workspace_path"]),
        "path_mode": str(paths["path_mode"]),
        "path_status": str(paths["path_status"]),
        "build_root": str(build_root),
        "commands": commands,
        "warnings": warnings,
        "errors": errors,
    }
