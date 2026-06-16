"""
Control Center API router (Phase E.9) — Pi desktop / peripheral settings.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from core import control_center_handlers as handlers

router = APIRouter(tags=["control-center"])

@router.get("/api/control-center/wifi/networks")
async def get_wifi_networks_route():
    return await handlers.get_wifi_networks()

@router.post("/api/control-center/wifi/scan")
async def wifi_scan_post_route(request: Request):
    return await handlers.wifi_scan_post(request)

@router.get("/api/control-center/wifi/config")
async def get_wifi_config_route():
    return await handlers.get_wifi_config()

@router.get("/api/control-center/wifi/status")
async def get_wifi_status_route():
    return await handlers.get_wifi_status()

@router.post("/api/control-center/wifi/disconnect")
async def wifi_disconnect_route(request: Request):
    return await handlers.wifi_disconnect(request)

@router.post("/api/control-center/wifi/enabled")
async def wifi_set_enabled_route(request: Request):
    return await handlers.wifi_set_enabled(request)

@router.post("/api/control-center/wifi/add")
async def add_wifi_network_route(request: Request):
    return await handlers.add_wifi_network(request)

@router.post("/api/control-center/wifi/connect")
async def wifi_connect_route(request: Request):
    return await handlers.wifi_connect(request)

@router.get("/api/control-center/ssh/status")
async def get_ssh_status_route():
    return await handlers.get_ssh_status()

@router.post("/api/control-center/ssh/set")
async def set_ssh_enabled_route(request: Request):
    return await handlers.set_ssh_enabled(request)

@router.post("/api/control-center/ssh/start")
async def start_ssh_route(request: Request):
    return await handlers.start_ssh(request)

@router.get("/api/control-center/vnc/status")
async def get_vnc_status_route():
    return await handlers.get_vnc_status()

@router.post("/api/control-center/vnc/set")
async def set_vnc_enabled_route(request: Request):
    return await handlers.set_vnc_enabled(request)

@router.post("/api/control-center/vnc/start")
async def start_vnc_route(request: Request):
    return await handlers.start_vnc(request)

@router.get("/api/control-center/keyboard")
async def get_keyboard_layout_route():
    return await handlers.get_keyboard_layout()

@router.post("/api/control-center/keyboard/set")
async def set_keyboard_layout_route(request: Request):
    return await handlers.set_keyboard_layout(request)

@router.get("/api/control-center/locale")
async def get_locale_route():
    return await handlers.get_locale()

@router.post("/api/control-center/locale/set")
async def set_locale_route(request: Request):
    return await handlers.set_locale(request)

@router.get("/api/control-center/desktop")
async def get_desktop_settings_route():
    return await handlers.get_desktop_settings()

@router.get("/api/control-center/desktop/boot-target")
async def get_desktop_boot_target_route():
    return await handlers.get_desktop_boot_target()

@router.post("/api/control-center/desktop/boot-target")
async def set_desktop_boot_target_route(request: Request):
    return await handlers.set_desktop_boot_target(request)

@router.get("/api/control-center/display")
async def get_display_settings_route():
    return await handlers.get_display_settings()

@router.post("/api/control-center/display")
async def set_display_settings_route(request: Request):
    return await handlers.set_display_settings(request)

@router.get("/api/control-center/display/telemetry")
async def get_display_telemetry_settings_route():
    return await handlers.get_display_telemetry_settings()

@router.post("/api/control-center/display/telemetry")
async def set_display_telemetry_settings_route(request: Request):
    return await handlers.set_display_telemetry_settings(request)

@router.post("/api/control-center/display/telemetry/runner")
async def set_display_telemetry_runner_route(request: Request):
    return await handlers.set_display_telemetry_runner(request)

@router.get("/api/control-center/printers")
async def get_printers_route():
    return await handlers.get_printers()

@router.get("/api/control-center/scanners")
async def get_scanners_route():
    return await handlers.get_scanners()

@router.get("/api/control-center/performance")
async def get_performance_route():
    return await handlers.get_performance()

@router.post("/api/control-center/performance")
async def set_performance_route(request: Request):
    return await handlers.set_performance(request)

@router.get("/api/control-center/bluetooth/status")
async def get_bluetooth_status_route():
    return await handlers.get_bluetooth_status()

@router.post("/api/control-center/bluetooth/scan")
async def bluetooth_scan_route(request: Request):
    return await handlers.bluetooth_scan(request)

@router.post("/api/control-center/bluetooth/enabled")
async def bluetooth_set_enabled_route(request: Request):
    return await handlers.bluetooth_set_enabled(request)

