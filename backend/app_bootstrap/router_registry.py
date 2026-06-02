from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from fastapi import FastAPI

from app_bootstrap.startup_diagnostics import RouterRegistrationStatus


@dataclass
class RouterRegistryResult:
    statuses: list[RouterRegistrationStatus] = field(default_factory=list)

    def add(self, *, router: str, status: str, prefix: str, profile: str, error: str | None = None) -> None:
        self.statuses.append(
            RouterRegistrationStatus(
                router=router,
                status=status,
                prefix=prefix,
                profile=profile,
                error=(error[:200] if error else None),
            )
        )


def register_core_routes(app: FastAPI, profile_context: dict[str, str]) -> RouterRegistryResult:
    # Bestehende Kernrouten bleiben derzeit in app.py; hier nur Ergebnisobjekt.
    _ = app
    _ = profile_context
    return RouterRegistryResult()


def _register_optional_router(
    *,
    app: FastAPI,
    result: RouterRegistryResult,
    profile: str,
    router_name: str,
    prefix: str,
    enabled: bool,
    importer: Callable[[], object],
) -> None:
    if not enabled:
        result.add(router=router_name, status="disabled_by_profile", prefix=prefix, profile=profile)
        return
    try:
        router_obj = importer()
        app.include_router(router_obj)  # type: ignore[arg-type]
        result.add(router=router_name, status="registered", prefix=prefix, profile=profile)
    except Exception as exc:  # noqa: BLE001
        result.add(router=router_name, status="import_failed", prefix=prefix, profile=profile, error=f"{type(exc).__name__}:{exc}")


def register_optional_routes(
    app: FastAPI,
    profile_context: dict[str, str],
    *,
    should_register_dev_server_router: Callable[[], bool],
    should_register_fleet_router: Callable[[], bool],
    should_register_dev_diagnostics_router: Callable[[], bool],
    should_register_rescue_remote_router: Callable[[], bool],
    should_register_rescue_agent_router: Callable[[], bool],
) -> RouterRegistryResult:
    profile = profile_context.get("install_profile", "unknown")
    result = RouterRegistryResult()

    _register_optional_router(
        app=app,
        result=result,
        profile=profile,
        router_name="dev_server",
        prefix="/api/dev-server",
        enabled=should_register_dev_server_router(),
        importer=lambda: __import__("devserver.routers", fromlist=["router"]).router,
    )
    _register_optional_router(
        app=app,
        result=result,
        profile=profile,
        router_name="fleet_sessions",
        prefix="/api/fleet",
        enabled=should_register_fleet_router(),
        importer=lambda: __import__("fleet.routers", fromlist=["router"]).router,
    )
    _register_optional_router(
        app=app,
        result=result,
        profile=profile,
        router_name="dev_diagnostics",
        prefix="/api/dev-diagnostics",
        enabled=should_register_dev_diagnostics_router(),
        importer=lambda: __import__("dev_diagnostics.routers", fromlist=["router"]).router,
    )
    _register_optional_router(
        app=app,
        result=result,
        profile=profile,
        router_name="rescue_remote",
        prefix="/api/rescue-remote",
        enabled=should_register_rescue_remote_router(),
        importer=lambda: __import__("rescue_remote.routers", fromlist=["router"]).router,
    )
    _register_optional_router(
        app=app,
        result=result,
        profile=profile,
        router_name="rescue_agent",
        prefix="/api/rescue-agent",
        enabled=should_register_rescue_agent_router(),
        importer=lambda: __import__("rescue_agent.routers", fromlist=["router"]).router,
    )

    return result


def register_all_routes(
    app: FastAPI,
    profile_context: dict[str, str],
    *,
    should_register_dev_server_router: Callable[[], bool],
    should_register_fleet_router: Callable[[], bool],
    should_register_dev_diagnostics_router: Callable[[], bool],
    should_register_rescue_remote_router: Callable[[], bool],
    should_register_rescue_agent_router: Callable[[], bool],
) -> RouterRegistryResult:
    result = register_core_routes(app, profile_context)
    optional = register_optional_routes(
        app,
        profile_context,
        should_register_dev_server_router=should_register_dev_server_router,
        should_register_fleet_router=should_register_fleet_router,
        should_register_dev_diagnostics_router=should_register_dev_diagnostics_router,
        should_register_rescue_remote_router=should_register_rescue_remote_router,
        should_register_rescue_agent_router=should_register_rescue_agent_router,
    )
    result.statuses.extend(optional.statuses)
    return result

