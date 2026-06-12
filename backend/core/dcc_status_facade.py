"""
DCC Status Facade — canonical read-only aggregation entry for Development Dashboard.

Delegates to existing core modules only. No new discovery, parsers, notification logic,
or parallel ampel/status engines. Phase F.1: contract + delegation; routes unchanged.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

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

_LEGACY_STATUS_MAP: dict[str, str] = {
    "ok": "ok",
    "success": "ok",
    "green": "ok",
    "partial_green": "warning",
    "yellow": "warning",
    "warning": "warning",
    "degraded": "degraded",
    "review_required": "warning",
    "red": "blocked",
    "blocked": "blocked",
    "error": "blocked",
    "gray": "unavailable",
    "unavailable": "unavailable",
    "unknown": "unknown",
}


@dataclass(frozen=True)
class DccStatusFacadeWarning:
    code: str
    message: str
    section: str | None = None


@dataclass
class DccStatusSection:
    section_id: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class DccStatusFacadeResult:
    facade_version: int = FACADE_VERSION
    sections: list[DccStatusSection] = field(default_factory=list)
    warnings: list[DccStatusFacadeWarning] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def build_section_status(raw: str | None, *, default: str = "unknown") -> str:
    """Map legacy/project status tokens to the facade vocabulary."""
    key = str(raw or "").strip().lower()
    if not key:
        return default if default in FACADE_STATUS_VALUES else "unknown"
    return _LEGACY_STATUS_MAP.get(key, default if default in FACADE_STATUS_VALUES else "unknown")


def normalize_legacy_dcc_status(dashboard: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize ``build_dashboard_status`` body to facade section summary."""
    body = dashboard if isinstance(dashboard, dict) else {}
    deploy = body.get("deploy_drift") if isinstance(body.get("deploy_drift"), dict) else {}
    consistency = body.get("consistency") if isinstance(body.get("consistency"), dict) else {}
    runtime_gate = body.get("runtime_gate") if isinstance(body.get("runtime_gate"), dict) else {}
    candidates = [
        deploy.get("status"),
        consistency.get("status"),
        runtime_gate.get("status"),
        body.get("release_gate_status"),
    ]
    mapped = [build_section_status(str(v) if v is not None else None) for v in candidates]
    if "blocked" in mapped:
        overall = "blocked"
    elif "degraded" in mapped:
        overall = "degraded"
    elif "warning" in mapped:
        overall = "warning"
    elif mapped and all(m == "ok" for m in mapped if m != "unknown"):
        overall = "ok"
    elif any(m == "unavailable" for m in mapped):
        overall = "unavailable"
    else:
        overall = "unknown"
    return {
        "status": overall,
        "legacy_statuses": {k: str(v) for k, v in zip(
            ("deploy_drift", "consistency", "runtime_gate", "release_gate"),
            candidates,
            strict=False,
        )},
        "generated_at": body.get("generated_at"),
        "backend_version": body.get("backend_version"),
        "warning_count": len(body.get("warnings") or []),
        "error_count": len(body.get("errors") or []),
    }


def normalize_legacy_roadmap_bundle(bundle: dict[str, Any] | None) -> dict[str, Any]:
    body = bundle if isinstance(bundle, dict) else {}
    summary = body.get("summary") if isinstance(body.get("summary"), dict) else {}
    return {
        "status": build_section_status(str(body.get("status") or summary.get("status"))),
        "schema_valid": bool(body.get("schema_valid")),
        "read_only": bool(body.get("read_only", True)),
        "area_count": len(body.get("areas") or []),
        "warning_count": len(body.get("warnings") or []),
    }


def normalize_legacy_notification_summary(summary: dict[str, Any] | None) -> dict[str, Any]:
    body = summary if isinstance(summary, dict) else {}
    raw = body.get("status") or body.get("summary_status")
    return {
        "status": build_section_status(str(raw) if raw is not None else None, default="unavailable"),
        "event_count": int(body.get("event_count") or body.get("visible_event_count") or 0),
        "email_status": str((body.get("email") or {}).get("status") or "unknown"),
    }


def _warning(code: str, message: str, section: str | None = None) -> DccStatusFacadeWarning:
    return DccStatusFacadeWarning(code=code, message=message, section=section)


def _safe_section(
    section_id: str,
    builder: Callable[[], DccStatusSection],
    *,
    facade_warnings: list[DccStatusFacadeWarning],
    facade_errors: list[str],
) -> DccStatusSection:
    try:
        return builder()
    except Exception as exc:  # noqa: BLE001
        msg = f"{section_id}_failed:{exc}"
        facade_errors.append(msg)
        facade_warnings.append(_warning(f"{section_id}_unavailable", msg, section_id))
        return DccStatusSection(
            section_id=section_id,
            status="unavailable",
            data={},
            errors=[msg],
        )


def _result_to_dict(result: DccStatusFacadeResult) -> dict[str, Any]:
    return {
        "facade_version": result.facade_version,
        "sections": [asdict(section) for section in result.sections],
        "warnings": [asdict(w) for w in result.warnings],
        "errors": result.errors,
    }


def build_dcc_status_overview(
    *,
    repo_root: Path | None = None,
    running_jobs: list[dict[str, Any]] | None = None,
    package_activity: list[dict[str, Any]] | None = None,
    frontend_build_version: str | None = None,
    frontend_runtime_source: str | None = None,
) -> dict[str, Any]:
    """Canonical dashboard status overview (delegates to ``core.dev_dashboard``)."""
    from core import dev_dashboard as dev_dashboard_core

    warnings: list[DccStatusFacadeWarning] = []
    errors: list[str] = []

    def _build() -> DccStatusSection:
        body = dev_dashboard_core.build_dashboard_status(
            repo_root=repo_root,
            running_jobs=running_jobs or [],
            package_activity=package_activity or [],
            frontend_build_version=frontend_build_version,
            frontend_runtime_source=frontend_runtime_source,
        )
        normalized = normalize_legacy_dcc_status(body)
        section_warnings = [str(w) for w in (body.get("warnings") or []) if str(w).strip()]
        section_errors = [str(e) for e in (body.get("errors") or []) if str(e).strip()]
        return DccStatusSection(
            section_id="dashboard",
            status=str(normalized.get("status") or "unknown"),
            data={"dashboard": body, "normalized": normalized},
            warnings=section_warnings,
            errors=section_errors,
        )

    section = _safe_section("dashboard", _build, facade_warnings=warnings, facade_errors=errors)
    result = DccStatusFacadeResult(sections=[section], warnings=warnings, errors=errors)
    return _result_to_dict(result)


def build_dcc_roadmap_overview(
    *,
    repo_root: Path | None = None,
    dashboard_context: dict[str, Any] | None = None,
    include_dashboard_context: bool = False,
    running_jobs: list[dict[str, Any]] | None = None,
    package_activity: list[dict[str, Any]] | None = None,
    frontend_build_version: str | None = None,
    frontend_runtime_source: str | None = None,
) -> dict[str, Any]:
    """Roadmap registry bundle with optional dashboard overlay (delegates to ``core.dev_dashboard_roadmap``)."""
    from core.dev_dashboard_roadmap import load_roadmap_registry_bundle

    warnings: list[DccStatusFacadeWarning] = []
    errors: list[str] = []
    context = dashboard_context

    if context is None and include_dashboard_context:
        overview = build_dcc_status_overview(
            repo_root=repo_root,
            running_jobs=running_jobs,
            package_activity=package_activity,
            frontend_build_version=frontend_build_version,
            frontend_runtime_source=frontend_runtime_source,
        )
        sections = overview.get("sections") or []
        if sections and isinstance(sections[0], dict):
            data = sections[0].get("data") or {}
            context = data.get("dashboard") if isinstance(data.get("dashboard"), dict) else None
        for w in overview.get("warnings") or []:
            if isinstance(w, dict):
                warnings.append(
                    _warning(
                        str(w.get("code") or "dashboard_context_warning"),
                        str(w.get("message") or ""),
                        "roadmap",
                    )
                )

    def _build() -> DccStatusSection:
        bundle = load_roadmap_registry_bundle(repo_root=repo_root, dashboard_context=context)
        normalized = normalize_legacy_roadmap_bundle(bundle)
        section_warnings = [str(w) for w in (bundle.get("warnings") or []) if str(w).strip()]
        return DccStatusSection(
            section_id="roadmap",
            status=str(normalized.get("status") or "unknown"),
            data={"bundle": bundle, "normalized": normalized},
            warnings=section_warnings,
        )

    section = _safe_section("roadmap", _build, facade_warnings=warnings, facade_errors=errors)
    result = DccStatusFacadeResult(sections=[section], warnings=warnings, errors=errors)
    return _result_to_dict(result)


def build_dcc_backend_health_section(
    *,
    stale_after_seconds: int = 180,
    history_limit: int = 20,
) -> dict[str, Any]:
    """Backend health evidence section (delegates to ``core.dev_dashboard_backend_health``)."""
    from core.dev_dashboard_backend_health import load_backend_health_snapshot

    warnings: list[DccStatusFacadeWarning] = []
    errors: list[str] = []

    def _build() -> DccStatusSection:
        snapshot = load_backend_health_snapshot(
            stale_after_seconds=stale_after_seconds,
            history_limit=history_limit,
        )
        status = build_section_status(str(snapshot.get("status")))
        if snapshot.get("stale"):
            status = "warning" if status == "ok" else status
        return DccStatusSection(
            section_id="backend_health",
            status=status,
            data={"snapshot": snapshot},
            warnings=["stale_snapshot"] if snapshot.get("stale") else [],
        )

    section = _safe_section("backend_health", _build, facade_warnings=warnings, facade_errors=errors)
    return asdict(section)


def build_dcc_notification_section() -> dict[str, Any]:
    """Notification summary section (delegates to ``core.notification_state``)."""
    from core.notification_state import build_notification_summary

    warnings: list[DccStatusFacadeWarning] = []
    errors: list[str] = []

    def _build() -> DccStatusSection:
        summary = build_notification_summary()
        normalized = normalize_legacy_notification_summary(summary)
        return DccStatusSection(
            section_id="notifications",
            status=str(normalized.get("status") or "unknown"),
            data={"summary": summary, "normalized": normalized},
        )

    section = _safe_section("notifications", _build, facade_warnings=warnings, facade_errors=errors)
    return asdict(section)


def build_dcc_evidence_section(*, max_files: int = 400, repo_root: Path | None = None) -> dict[str, Any]:
    """Evidence index section (delegates to ``core.dev_dashboard``)."""
    from core import dev_dashboard as dev_dashboard_core

    warnings: list[DccStatusFacadeWarning] = []
    errors: list[str] = []

    def _build() -> DccStatusSection:
        index = dev_dashboard_core.build_evidence_index(repo_root=repo_root, max_files=max_files)
        raw_status = str(index.get("status") or "unknown")
        status = build_section_status(raw_status)
        section_warnings = [str(w) for w in (index.get("warnings") or []) if str(w).strip()]
        return DccStatusSection(
            section_id="evidence",
            status=status,
            data={"index": index},
            warnings=section_warnings,
        )

    section = _safe_section("evidence", _build, facade_warnings=warnings, facade_errors=errors)
    return asdict(section)


def _dashboard_body_from_overview(overview: dict[str, Any]) -> dict[str, Any]:
    sections = overview.get("sections") or []
    if not sections or not isinstance(sections[0], dict):
        return {}
    data = sections[0].get("data") or {}
    dashboard = data.get("dashboard")
    return dashboard if isinstance(dashboard, dict) else {}


def _roadmap_bundle_from_overview(overview: dict[str, Any]) -> dict[str, Any]:
    sections = overview.get("sections") or []
    if not sections or not isinstance(sections[0], dict):
        return {}
    data = sections[0].get("data") or {}
    bundle = data.get("bundle")
    return bundle if isinstance(bundle, dict) else {}


def build_dashboard_status_body(
    *,
    repo_root: Path | None = None,
    running_jobs: list[dict[str, Any]] | None = None,
    package_activity: list[dict[str, Any]] | None = None,
    frontend_build_version: str | None = None,
    frontend_runtime_source: str | None = None,
) -> dict[str, Any]:
    """Raw ``build_dashboard_status`` body — canonical sync entry for HTTP/cockpit callers."""
    overview = build_dcc_status_overview(
        repo_root=repo_root,
        running_jobs=running_jobs,
        package_activity=package_activity,
        frontend_build_version=frontend_build_version,
        frontend_runtime_source=frontend_runtime_source,
    )
    return _dashboard_body_from_overview(overview)


def build_dcc_roadmap_api_bundle(
    *,
    repo_root: Path | None = None,
    dashboard_context: dict[str, Any] | None = None,
    include_dashboard_context: bool = False,
    running_jobs: list[dict[str, Any]] | None = None,
    package_activity: list[dict[str, Any]] | None = None,
    frontend_build_version: str | None = None,
    frontend_runtime_source: str | None = None,
) -> dict[str, Any]:
    """Raw roadmap registry bundle for ``GET /api/dev-dashboard/roadmap`` (legacy API shape)."""
    overview = build_dcc_roadmap_overview(
        repo_root=repo_root,
        dashboard_context=dashboard_context,
        include_dashboard_context=include_dashboard_context,
        running_jobs=running_jobs,
        package_activity=package_activity,
        frontend_build_version=frontend_build_version,
        frontend_runtime_source=frontend_runtime_source,
    )
    return _roadmap_bundle_from_overview(overview)


def build_dcc_control_center_summary_api(
    *,
    running_jobs: list[dict[str, Any]] | None = None,
    package_activity: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """API response for ``GET /api/dev-dashboard/control-center-summary``."""
    from core.dev_control_center_summary import build_control_center_summary

    dashboard = build_dashboard_status_body(
        running_jobs=running_jobs or [],
        package_activity=package_activity or [],
    )
    return {"status": "success", "summary": build_control_center_summary(dashboard=dashboard)}


def build_dcc_prompt_findings_api(
    *,
    frontend_build_version: str | None = None,
    frontend_runtime_source: str | None = None,
) -> dict[str, Any]:
    """API response for ``GET /api/dev-dashboard/prompt-findings``."""
    from core import dev_dashboard as dev_dashboard_core
    from core.dev_dashboard_cockpit import build_prompt_findings

    fe_ver = (frontend_build_version or "").strip() or None
    body = build_dashboard_status_body(
        running_jobs=[],
        package_activity=[],
        frontend_build_version=fe_ver,
        frontend_runtime_source=frontend_runtime_source,
    )
    repo = dev_dashboard_core._repo_root()
    findings = build_prompt_findings(repo, body)
    return {"status": "success", "findings": findings}


def build_dcc_cursor_meta_prompt_api(
    *,
    frontend_build_version: str | None = None,
    frontend_runtime_source: str | None = None,
) -> dict[str, Any]:
    """API response for ``GET /api/dev-dashboard/cursor-meta-prompt``."""
    from core import dev_dashboard as dev_dashboard_core
    from core.dev_dashboard_cockpit import build_cursor_meta_prompt, build_prompt_findings

    fe_ver = (frontend_build_version or "").strip() or None
    body = build_dashboard_status_body(
        running_jobs=[],
        package_activity=[],
        frontend_build_version=fe_ver,
        frontend_runtime_source=frontend_runtime_source,
    )
    repo = dev_dashboard_core._repo_root()
    findings = build_prompt_findings(repo, body)
    meta = build_cursor_meta_prompt(repo, findings)
    return {"status": "success", **meta}


def build_dcc_project_overview_body(*, repo_root: Path | None = None) -> dict[str, Any]:
    """Raw project overview state for ``GET /api/dev-dashboard/project-overview``."""
    from core.project_overview_dashboard_state import build_project_overview_dashboard_state

    return build_project_overview_dashboard_state(repo_root=repo_root)


def build_dcc_facade_diagnostics() -> dict[str, Any]:
    """Lightweight facade diagnostics — no heavy aggregation."""
    return {
        "facade_version": FACADE_VERSION,
        "facade_module": "core.dcc_status_facade",
        "status_vocabulary": sorted(FACADE_STATUS_VALUES),
        "legacy_status_map_keys": sorted(_LEGACY_STATUS_MAP.keys()),
        "delegates_to": [
            "core.dev_dashboard.build_dashboard_status",
            "core.dev_dashboard.build_evidence_index",
            "core.dev_dashboard_roadmap.load_roadmap_registry_bundle",
            "core.dev_dashboard_backend_health.load_backend_health_snapshot",
            "core.notification_state.build_notification_summary",
        ],
        "public_functions": [
            "build_dcc_status_overview",
            "build_dcc_roadmap_overview",
            "build_dcc_backend_health_section",
            "build_dcc_notification_section",
            "build_dcc_evidence_section",
            "build_dashboard_status_body",
            "build_dcc_roadmap_api_bundle",
            "build_dcc_control_center_summary_api",
            "build_dcc_prompt_findings_api",
            "build_dcc_cursor_meta_prompt_api",
            "build_dcc_project_overview_body",
            "build_dcc_facade_diagnostics",
        ],
        "routes_pending_facade_migration": [],
        "profile_gate_owner": "core.dev_dashboard_status_service.build_dcc_profile_block_response",
        "read_only": True,
        "writes_allowed": False,
    }
