from __future__ import annotations

from typing import Any

from app_bootstrap.startup_diagnostics import get_last_startup_diagnostics, router_registry_summary


def inject_router_diagnostics(body: dict[str, Any]) -> dict[str, Any]:
    diag = get_last_startup_diagnostics()
    rescue_status = "unknown"
    rescue_error = ""
    for item in diag.get("router_registry") or []:
        if item.get("router") == "rescue_agent":
            rescue_status = str(item.get("status") or "unknown")
            rescue_error = str(item.get("error") or "")
            break
    body["rescue_agent_router_status"] = rescue_status
    body["rescue_agent_router_error"] = rescue_error
    body["router_registry_summary"] = router_registry_summary()
    body["startup_diagnostics_status"] = diag.get("startup_status", "unknown")
    return body

