"""System runtime — lazy app adapters (Phase E.10)."""

from __future__ import annotations

from pathlib import Path
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


def get_config_dir() -> Path:
    return _app().get_config_dir()


def root_mount_device() -> str | None:
    return _app()._root_mount_device()


def ensure_packagekit_stopped(sudo_password: str) -> None:
    _app()._ensure_packagekit_stopped(sudo_password)
