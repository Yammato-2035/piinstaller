"""Security runtime — lazy app adapters (Phase E.14)."""

from __future__ import annotations

from typing import Any


def _app():
    import app as app_module

    return app_module


def sudo_store():
    return _app().sudo_store


def logger():
    return _app().logger


def run_command(cmd: str, **kwargs: Any) -> dict[str, Any]:
    return _app().run_command(cmd, **kwargs)


def json_response(**kwargs):
    from fastapi.responses import JSONResponse

    return JSONResponse(**kwargs)


def http_exception(**kwargs):
    from fastapi import HTTPException

    raise HTTPException(**kwargs)


def get_running_services():
    return _app().get_running_services()


def get_installed_apps():
    return _app().get_installed_apps()


def get_security_config():
    return _app().get_security_config()


def get_updates_categorized():
    return _app().get_updates_categorized()


def check_installed(name: str) -> bool:
    return _app().check_installed(name)


def ensure_packagekit_stopped(sudo_password: str) -> None:
    _app()._ensure_packagekit_stopped(sudo_password)


def audit_rules_path():
    return _app()._audit_rules_path()
