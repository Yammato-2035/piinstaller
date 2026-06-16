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


def http_exception(**kwargs):
    from fastapi import HTTPException

    raise HTTPException(**kwargs)


def get_cpu_temp():
    return _app().get_cpu_temp()


def get_updates_categorized():
    return _app().get_updates_categorized()


def get_installed_packages_list():
    return _app()._get_installed_packages_list()


def get_security_config():
    return _app().get_security_config()


def list_running_processes():
    return _app().get_running_processes()


def get_asus_fan_profiles():
    return _app().get_asus_fan_profiles()


def get_asus_fan_status():
    return _app().get_asus_fan_status()


def set_asus_fan_profile(profile: str, sudo_password: str = ""):
    return _app().set_asus_fan_profile(profile, sudo_password)


def is_asus_rog_system():
    return _app().is_asus_rog_system()


def is_asusctl_available():
    return _app().is_asusctl_available()
