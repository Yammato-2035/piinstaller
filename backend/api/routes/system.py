"""
System API router (Phase E.10) — read-only probes and safe system POST actions.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from core import system_handlers as handlers

router = APIRouter(tags=["system"])

@router.get("/api/system/paths")
async def get_system_paths_route():
    return await handlers.get_system_paths()

@router.get("/api/system/devices")
async def get_system_devices_route():
    return await handlers.get_system_devices()

@router.get("/api/system/terminal-available")
async def check_terminal_available_route():
    return await handlers.check_terminal_available()

@router.post("/api/system/reboot")
async def reboot_system_route(request: Request):
    return await handlers.reboot_system(request)

@router.post("/api/system/packagekit/stop")
async def stop_packagekit_route(request: Request):
    return await handlers.stop_packagekit(request)


@router.get("/api/system/service-conflicts")
async def get_service_conflicts_route():
    return await handlers.get_service_conflicts()


@router.get("/api/system/resources")
async def get_system_resources_route():
    return await handlers.get_system_resources()


@router.get("/api/system/installed-packages")
async def get_installed_packages_route():
    return await handlers.get_installed_packages()


@router.get("/api/system/running-processes")
async def get_running_processes_route():
    return await handlers.get_running_processes_endpoint()


@router.get("/api/system/security-config")
async def get_security_config_route(request: Request):
    return await handlers.get_security_config_endpoint(request)


@router.get("/api/system/updates")
async def get_system_updates_route():
    return await handlers.get_system_updates()


@router.get("/api/system/status")
async def system_status_route():
    return await handlers.system_status()


@router.get("/api/system/freenove-detection")
async def get_freenove_detection_route():
    return await handlers.get_freenove_detection()


@router.get("/api/system/asus-rog/fan/profiles")
async def get_asus_fan_profiles_route():
    return await handlers.get_asus_fan_profiles()


@router.get("/api/system/asus-rog/fan/status")
async def get_asus_fan_status_route():
    return await handlers.get_asus_fan_status()


@router.post("/api/system/asus-rog/fan/set-profile")
async def set_asus_fan_profile_route(request: Request):
    return await handlers.set_asus_fan_profile(request)


@router.get("/api/system/asus-rog/detection")
async def get_asus_rog_detection_route():
    return await handlers.get_asus_rog_detection()

