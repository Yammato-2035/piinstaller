from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

_RUNTIME_ROOT = Path("/opt/setuphelfer")
_DEFAULT_WORKSPACE_ROOT = Path("/home/volker/piinstaller")
_BUILD_TREE_REL = Path("build/rescue/live-build/setuphelfer-rescue-live")
_TEMP_BUNDLE_REL = Path("build/rescue/temp-runtime/setuphelfer-rescue-runtime")
_LOG_ROOT_REL = Path("build/rescue/logs/controlled-iso-build")
_SUMMARY_REL = Path("docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json")
_LIVE_BUILD_SYSLINUX = Path("/usr/lib/live/build/lb_binary_syslinux")
_RSVG_INSTALL_COMMAND = "sudo apt install librsvg2-bin"
_RSVG_WRAPPER_REL = Path("build/rescue/tool-compat/bin/rsvg")


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


def _package_installed(name: str) -> bool:
    try:
        proc = subprocess.run(
            ["dpkg", "-s", name],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


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


def inspect_rsvg_build_dependency(*, repo_root: Path | None = None) -> dict[str, Any]:
    paths = resolve_rescue_iso_paths(repo_root=repo_root)
    workspace_root = Path(paths["workspace_path"]).resolve(strict=False)
    build_root = Path(paths["build_tree_path"]).resolve(strict=False)
    splash_template = build_root / "config/bootloaders/isolinux/splash.svg.in"
    legacy_rsvg = shutil.which("rsvg")
    compat_rsvg = shutil.which("rsvg-convert")
    wrapper_path = (workspace_root / _RSVG_WRAPPER_REL).resolve(strict=False)
    wrapper_exists = wrapper_path.is_file()
    live_build_script = _LIVE_BUILD_SYSLINUX.resolve(strict=False)
    try:
        live_build_text = live_build_script.read_text(encoding="utf-8", errors="replace")
    except OSError:
        live_build_text = ""
    live_build_uses_rsvg = "rsvg --format png" in live_build_text or "/usr/bin/rsvg" in live_build_text
    live_build_uses_rsvg_convert = "rsvg-convert" in live_build_text
    required = splash_template.is_file() and live_build_uses_rsvg
    status = "ok"
    summary = "Keine zusätzliche rsvg-Build-Abhängigkeit erkannt."
    error_code = None
    commands: list[str] = []
    warnings: list[str] = []
    package_installed = _package_installed("librsvg2-bin")
    effective_legacy_path = legacy_rsvg
    legacy_source = "system"

    if not effective_legacy_path and wrapper_exists and compat_rsvg:
        effective_legacy_path = str(wrapper_path)
        legacy_source = "project_local_wrapper"

    if required and effective_legacy_path:
        if legacy_source == "project_local_wrapper":
            summary = (
                "live-build erwartet den Legacy-Befehl 'rsvg'; der projektlokale Kompatibilitaets-Wrapper "
                "delegiert kontrolliert auf rsvg-convert."
            )
            warnings.append("Kein globaler /usr/bin/rsvg-Symlink; Operator-Build muss PATH explizit um den Wrapper erweitern.")
        else:
            summary = "live-build erwartet den Legacy-Befehl 'rsvg'; der Befehl ist verfuegbar."

    if required and not effective_legacy_path:
        if compat_rsvg:
            status = "review_required"
            error_code = "blocked_legacy_rsvg_command_missing"
            summary = (
                "live-build erwartet den Legacy-Befehl 'rsvg' fuer die splash.svg.in-zu-splash.png-"
                "Konvertierung; rsvg-convert ist vorhanden, aber kein kontrollierter Legacy-Kompatibilitaetsbefehl."
            )
            warnings.append("rsvg-convert allein wird vom aktuellen lb_binary_syslinux nicht direkt aufgerufen.")
            warnings.append("Kein globaler /usr/bin/rsvg-Symlink empfohlen; stattdessen projektlokalen Wrapper verwenden.")
        elif package_installed:
            status = "review_required"
            error_code = "review_required_rsvg_convert_not_in_path"
            summary = (
                "librsvg2-bin ist installiert, aber rsvg-convert ist im aktuellen PATH nicht auffindbar; "
                "Host-PATH oder Paketinstallation muessen geprueft werden."
            )
        else:
            status = "blocked"
            error_code = "blocked_build_tools_missing"
            commands = [_RSVG_INSTALL_COMMAND]
            summary = (
                "live-build erwartet 'rsvg' fuer die splash.svg.in-zu-splash.png-Konvertierung; "
                "auf dem Host ist weder rsvg noch rsvg-convert vorhanden."
            )

    return {
        "required": required,
        "status": status,
        "summary": summary,
        "command_name": "rsvg",
        "legacy_path": effective_legacy_path,
        "system_legacy_path": legacy_rsvg,
        "legacy_source": legacy_source if effective_legacy_path else None,
        "wrapper_path": str(wrapper_path),
        "wrapper_exists": wrapper_exists,
        "compat_command_name": "rsvg-convert",
        "compat_path": compat_rsvg,
        "hint_package": "librsvg2-bin",
        "package_installed": package_installed,
        "install_command": _RSVG_INSTALL_COMMAND,
        "commands": commands,
        "error_code": error_code,
        "warnings": warnings,
        "splash_template_path": str(splash_template),
        "live_build_script_path": str(live_build_script),
        "live_build_uses_rsvg": live_build_uses_rsvg,
        "live_build_uses_rsvg_convert": live_build_uses_rsvg_convert,
    }


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
    rsvg = inspect_rsvg_build_dependency(repo_root=repo_root)
    commands: list[str] = []
    warnings: list[str] = []
    errors = list(paths.get("errors") or [])
    warnings.extend(str(item) for item in (paths.get("warnings") or []))
    wrapper_path = str(rsvg.get("wrapper_path") or "")
    wrapper_dir = str(Path(wrapper_path).parent) if wrapper_path else ""
    use_wrapper = bool(wrapper_dir) and str(rsvg.get("legacy_source") or "") == "project_local_wrapper"
    if paths.get("path_status") == "ok" and rsvg.get("status") == "ok":
        commands = [f'cd "{build_root}"']
        if use_wrapper:
            commands.append(f'export PATH="{wrapper_dir}:$PATH"')
        commands.extend(
            [
                "./auto/config",
                (
                    f'sudo env PATH="{wrapper_dir}:$PATH" lb build noauto'
                    if use_wrapper
                    else "sudo lb build noauto"
                ),
            ]
        )
        warnings.extend(
            [
                "Nur ausführen, wenn Pfad exakt geprüft wurde.",
                "USB-Schreiben, dd, mkfs und Partition-Write bleiben verboten.",
            ]
        )
    else:
        if rsvg.get("status") in {"blocked", "review_required"}:
            commands = list(rsvg.get("commands") or [])
            warnings.extend(str(item) for item in (rsvg.get("warnings") or []))
            errors.extend(
                [
                    str(rsvg.get("error_code") or "blocked_build_tools_missing"),
                ]
            )
            if str(rsvg.get("error_code") or "") == "blocked_build_tools_missing":
                errors.append("missing_tools:rsvg")
                warnings.append("Build bleibt blockiert, bis die benoetigte rsvg-Abhaengigkeit verfuegbar ist.")
            else:
                warnings.append("Build bleibt blockiert, bis die Legacy-rsvg-Kompatibilitaet kontrolliert geklaert ist.")
        else:
            warnings.append("Pfadprüfung fehlgeschlagen; keine Kommandos erzeugt.")
    return {
        "status": "operator_required" if commands and rsvg.get("status") == "ok" else "blocked",
        "warning": (
            "Nur ausführen, wenn Pfad exakt geprüft wurde."
            if rsvg.get("status") == "ok"
            else (
                "Vor dem Build fehlt die benoetigte rsvg-Build-Abhaengigkeit."
                if str(rsvg.get("error_code") or "") == "blocked_build_tools_missing"
                else "Vor dem Build fehlt ein kontrollierter Legacy-rsvg-Kompatibilitaetspfad."
            )
        ),
        "runtime_path": str(paths["runtime_path"]),
        "workspace_path": str(paths["workspace_path"]),
        "path_mode": str(paths["path_mode"]),
        "path_status": str(paths["path_status"]),
        "build_root": str(build_root),
        "rsvg_preflight": rsvg,
        "commands": commands,
        "warnings": warnings,
        "errors": errors,
    }
