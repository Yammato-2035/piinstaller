"""
Health and lightweight status routes (Phase E.1).

Read-only endpoints extracted from app.py — no storage/safety/mount duplication.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Leichtgewichtiger Liveness-Endpunkt ohne Dashboard-/Dateiscans."""
    from core.install_paths import get_backend_runtime_dir
    from core.liveness import build_health_payload

    return build_health_payload(runtime_path=str(get_backend_runtime_dir().resolve()))


@router.get("/api/init/status")
async def init_status():
    from app import CONFIG_PATH, CONFIG_STATE, get_app_edition

    return {
        "status": "success",
        "config_path": str(CONFIG_PATH),
        "device_id": CONFIG_STATE.get("device_id"),
        "first_run": bool(CONFIG_STATE.get("first_run")),
        "matched_device": bool(CONFIG_STATE.get("matched_device")),
        "app_edition": get_app_edition(),
    }


@router.get("/api/logs/path")
async def logs_path():
    """Log-Dateipfad (z.B. für tail -f)."""
    from app import LOG_PATH

    return {"status": "success", "path": str(LOG_PATH), "exists": LOG_PATH.exists()}
