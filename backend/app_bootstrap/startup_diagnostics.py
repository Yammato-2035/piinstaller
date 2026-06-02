from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

UTC = timezone.utc


@dataclass
class RouterRegistrationStatus:
    router: str
    status: str
    prefix: str
    profile: str
    error: str | None = None


def _now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


_LAST_STARTUP_DIAGNOSTICS: dict[str, Any] = {
    "startup_status": "unknown",
    "created_at": _now_iso(),
    "install_profile": "unknown",
    "backend_runtime_path": "",
    "router_registry": [],
    "warnings": [],
    "errors": [],
}


def record_router_registry_result(
    *,
    install_profile: str,
    backend_runtime_path: str,
    router_registry: list[RouterRegistrationStatus],
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    for item in router_registry:
        if item.status == "import_failed":
            warnings.append(f"router_import_failed:{item.router}")
            if item.error:
                errors.append(f"{item.router}:{item.error[:200]}")
    startup_status = "ok"
    if errors:
        startup_status = "degraded"
    elif warnings:
        startup_status = "review_required"
    diag = {
        "startup_status": startup_status,
        "created_at": _now_iso(),
        "install_profile": install_profile,
        "backend_runtime_path": backend_runtime_path,
        "router_registry": [asdict(item) for item in router_registry],
        "warnings": warnings,
        "errors": errors,
    }
    global _LAST_STARTUP_DIAGNOSTICS
    _LAST_STARTUP_DIAGNOSTICS = diag
    return diag


def get_last_startup_diagnostics() -> dict[str, Any]:
    return dict(_LAST_STARTUP_DIAGNOSTICS)


def router_registry_summary() -> dict[str, int]:
    items = _LAST_STARTUP_DIAGNOSTICS.get("router_registry") or []
    summary = {"registered": 0, "disabled_by_profile": 0, "import_failed": 0, "skipped": 0, "unknown": 0}
    for item in items:
        status = str((item or {}).get("status") or "unknown")
        if status not in summary:
            status = "unknown"
        summary[status] += 1
    return summary

