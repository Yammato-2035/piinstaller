"""Control Center runtime — lazy app adapters (Phase E.9)."""

from __future__ import annotations

from typing import Any


def _app():
    import app as app_module

    return app_module


def get_control_center_module():
    return _app()._get_control_center_module()


def sudo_store():
    return _app().sudo_store


def logger():
    return _app().logger


def run_command(cmd: str, **kwargs: Any) -> dict[str, Any]:
    return _app().run_command(cmd, **kwargs)


def json_response(**kwargs):
    from fastapi.responses import JSONResponse

    return JSONResponse(**kwargs)
