"""
System Status Facade — canonical read-only aggregation for /api/status and /api/system/status.

Phase G.1: contract + delegation only; routes unchanged.
Delegates to existing app.py/core helpers. No network diagnostics (G.2).
No subprocess, systemctl, sudo, or writes in this module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from core.dcc_status_facade import build_section_status
from core.system_status_core import build_overall_status, load_backup_realtest_state

FACADE_VERSION = 1

FACADE_STATUS_VALUES = frozenset(
    {
        "ok",
        "warning",
        "degraded",
        "blocked",
        "unavailable",
        "unknown",
    }
)

_LEGACY_AMPEL_MAP: dict[str, str] = {
    "green": "ok",
    "yellow": "warning",
    "red": "blocked",
    "gray": "unavailable",
}


@dataclass(frozen=True)
class SystemStatusFacadeWarning:
    code: str
    message: str
    section: str | None = None


@dataclass
class SystemStatusSection:
    section_id: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class SystemStatusFacadeResult:
    facade_version: int = FACADE_VERSION
    sections: list[SystemStatusSection] = field(default_factory=list)
    warnings: list[SystemStatusFacadeWarning] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def normalize_legacy_system_status(ampel: dict[str, Any] | None) -> dict[str, Any]:
    """Map legacy green/yellow/red ampel keys to facade vocabulary."""
    body = ampel if isinstance(ampel, dict) else {}
    mapped: dict[str, str] = {}
    for key in ("backup", "restore", "security", "updates"):
        raw = str(body.get(key) or "").strip().lower()
        mapped[key] = _LEGACY_AMPEL_MAP.get(raw, build_section_status(raw))
    values = list(mapped.values())
    if "blocked" in values:
        overall = "blocked"
    elif "warning" in values or "degraded" in values:
        overall = "warning"
    elif values and all(v == "ok" for v in values):
        overall = "ok"
    elif any(v == "unavailable" for v in values):
        overall = "unavailable"
    else:
        overall = "unknown"
    return {"status": overall, "ampel": mapped, "legacy_ampel": {k: str(body.get(k) or "") for k in mapped}}


def build_unavailable_section(section_id: str, *, reason: str) -> SystemStatusSection:
    return SystemStatusSection(
        section_id=section_id,
        status="unavailable",
        data={},
        errors=[reason],
        warnings=[reason],
    )


def _warning(code: str, message: str, section: str | None = None) -> SystemStatusFacadeWarning:
    return SystemStatusFacadeWarning(code=code, message=message, section=section)


def _safe_section(
    section_id: str,
    builder: Callable[[], SystemStatusSection],
    *,
    facade_warnings: list[SystemStatusFacadeWarning],
    facade_errors: list[str],
) -> SystemStatusSection:
    try:
        return builder()
    except Exception as exc:  # noqa: BLE001
        msg = f"{section_id}_failed:{exc}"
        facade_errors.append(msg)
        facade_warnings.append(_warning(f"{section_id}_unavailable", msg, section_id))
        return build_unavailable_section(section_id, reason=msg)


def _result_to_dict(result: SystemStatusFacadeResult) -> dict[str, Any]:
    return {
        "facade_version": result.facade_version,
        "sections": [asdict(section) for section in result.sections],
        "warnings": [asdict(w) for w in result.warnings],
        "errors": result.errors,
    }


def _legacy_compute_ampel_status() -> dict[str, str]:
    """Ampel via system_status_core (G.12); no direct ``app._compute_system_status`` in facade."""
    return build_overall_status()


def _legacy_backup_realtest_state() -> dict[str, Any]:
    return load_backup_realtest_state()


def build_backend_runtime_section() -> dict[str, Any]:
    """Backend version and runtime path (read-only, no subprocess)."""
    from core.install_paths import get_backend_runtime_dir

    warnings: list[SystemStatusFacadeWarning] = []
    errors: list[str] = []

    def _build() -> SystemStatusSection:
        runtime_path = str(get_backend_runtime_dir().resolve())
        version = "unknown"
        edition = "unknown"
        try:
            import app as app_module

            version = str(app_module.get_pi_installer_version() or "unknown")
            edition = str(app_module.get_app_edition() or "unknown")
        except Exception as exc:  # noqa: BLE001
            warnings.append(_warning("backend_runtime_partial", str(exc), "backend_runtime"))
        status = "ok" if version != "unknown" else "unknown"
        return SystemStatusSection(
            section_id="backend_runtime",
            status=status,
            data={
                "version": version,
                "edition": edition,
                "runtime_path": runtime_path,
            },
        )

    section = _safe_section("backend_runtime", _build, facade_warnings=warnings, facade_errors=errors)
    return asdict(section)


def build_installation_section(*, repo_root: Path | None = None) -> dict[str, Any]:
    """Installation /opt drift summary (delegates to app version helpers)."""
    warnings: list[SystemStatusFacadeWarning] = []
    errors: list[str] = []

    def _build() -> SystemStatusSection:
        import app as app_module

        root = repo_root or Path(__file__).resolve().parent.parent.parent
        source_version = str(app_module.get_pi_installer_version() or "unknown")
        source_path = str(root)
        opt_dir = app_module.OPT_INSTALL_DIR
        installed_version = (
            app_module._read_version_from_path(opt_dir) if opt_dir.exists() else None
        )
        installed_path = str(opt_dir) if opt_dir.exists() else None
        is_source_opt = root.resolve() == opt_dir.resolve()
        update_available = not is_source_opt and (
            installed_version is None or installed_version != source_version
        )
        deploy_script = root / "scripts" / "deploy-to-opt.sh"
        if update_available:
            section_status = "warning"
        elif is_source_opt:
            section_status = "ok"
        else:
            section_status = "ok"
        return SystemStatusSection(
            section_id="installation",
            status=section_status,
            data={
                "source_path": source_path,
                "source_version": source_version,
                "installed_path": installed_path,
                "installed_version": installed_version,
                "update_available": update_available,
                "is_running_from_opt": is_source_opt,
                "can_run_deploy": deploy_script.is_file(),
                "deploy_script": str(deploy_script),
            },
        )

    section = _safe_section("installation", _build, facade_warnings=warnings, facade_errors=errors)
    return asdict(section)


def build_profile_section() -> dict[str, Any]:
    """User experience profile (read-only disk scan via app legacy helper)."""
    warnings: list[SystemStatusFacadeWarning] = []
    errors: list[str] = []

    def _build() -> SystemStatusSection:
        import app as app_module

        level = "beginner"
        updated_at = app_module._now_iso()
        try:
            cands = app_module._user_profile_collect_from_disk()
            if cands:
                cands.sort(key=lambda x: (x[0], x[1]), reverse=True)
                updated_at, _mtime, level, _path = cands[0]
        except Exception as exc:  # noqa: BLE001
            warnings.append(_warning("profile_partial", str(exc), "profile"))
        profile = app_module.UserProfile(experience_level=level, updated_at=updated_at)
        return SystemStatusSection(
            section_id="profile",
            status="ok",
            data={"profile": profile.dict()},
        )

    section = _safe_section("profile", _build, facade_warnings=warnings, facade_errors=errors)
    return asdict(section)


def build_system_status_sections(
    *,
    repo_root: Path | None = None,
    include_ampel: bool = True,
) -> dict[str, Any]:
    """All system status sections; section failures are isolated."""
    warnings: list[SystemStatusFacadeWarning] = []
    errors: list[str] = []
    sections: list[SystemStatusSection] = []

    if include_ampel:

        def _ampel() -> SystemStatusSection:
            ampel = _legacy_compute_ampel_status()
            normalized = normalize_legacy_system_status(ampel)
            rs = _legacy_backup_realtest_state()
            return SystemStatusSection(
                section_id="system_ampel",
                status=str(normalized.get("status") or "unknown"),
                data={
                    "ampel": ampel,
                    "normalized": normalized,
                    "realtest_state": rs,
                },
            )

        sections.append(_safe_section("system_ampel", _ampel, facade_warnings=warnings, facade_errors=errors))

    for fn, sid in (
        (build_backend_runtime_section, "backend_runtime"),
        (lambda: build_installation_section(repo_root=repo_root), "installation"),
        (build_profile_section, "profile"),
    ):
        try:
            raw = fn()
            if isinstance(raw, dict):
                sections.append(SystemStatusSection(**raw))
            else:
                sections.append(raw)
        except Exception as exc:  # noqa: BLE001
            msg = f"{sid}_attach_failed:{exc}"
            errors.append(msg)
            warnings.append(_warning(f"{sid}_unavailable", msg, sid))
            sections.append(build_unavailable_section(sid, reason=msg))

    result = SystemStatusFacadeResult(sections=sections, warnings=warnings, errors=errors)
    return _result_to_dict(result)


def build_system_status(*, repo_root: Path | None = None) -> dict[str, Any]:
    """
    Canonical API payload for ``GET /api/system/status`` (exact legacy response shape).

    Delegates ampel computation via legacy adapters; no extra facade envelope keys.
    """
    overview = build_system_status_sections(repo_root=repo_root, include_ampel=True)
    ampel_section = next(
        (s for s in overview.get("sections") or [] if isinstance(s, dict) and s.get("section_id") == "system_ampel"),
        {},
    )
    data = ampel_section.get("data") if isinstance(ampel_section.get("data"), dict) else {}
    ampel = data.get("ampel") if isinstance(data.get("ampel"), dict) else {}
    rs = data.get("realtest_state") if isinstance(data.get("realtest_state"), dict) else {}
    payload = dict(ampel)
    payload["realtest_state"] = rs
    return {
        "status": "success",
        "api_status": "ok",
        "message": "",
        "data": payload,
        **ampel,
        "realtest_state": rs,
    }


def build_system_status_diagnostics() -> dict[str, Any]:
    """Lightweight facade diagnostics — no heavy aggregation."""
    return {
        "facade_version": FACADE_VERSION,
        "facade_module": "core.system_status_facade",
        "status_vocabulary": sorted(FACADE_STATUS_VALUES),
        "legacy_ampel_map_keys": sorted(_LEGACY_AMPEL_MAP.keys()),
        "delegates_to": [
            "system_status_core.build_overall_status",
            "system_status_core.load_backup_realtest_state",
            "app.get_pi_installer_version",
            "app.get_app_edition",
            "app._user_profile_collect_from_disk",
            "core.install_paths.get_backend_runtime_dir",
        ],
        "ampel_via_system_status_core": True,
        "facade_ampel_computation": False,
        "public_functions": [
            "build_system_status",
            "build_system_status_sections",
            "build_backend_runtime_section",
            "build_installation_section",
            "build_profile_section",
            "build_system_status_diagnostics",
            "normalize_legacy_system_status",
            "build_unavailable_section",
        ],
        "routes_pending_facade_migration": [
            "GET /api/status",
        ],
        "excluded_g2": [
            "GET /api/system/network",
            "app.get_network_info",
            "app._demo_network",
        ],
        "read_only": True,
        "writes_allowed": False,
        "network_diagnostics_allowed": False,
    }
