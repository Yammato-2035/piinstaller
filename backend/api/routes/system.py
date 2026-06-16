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

