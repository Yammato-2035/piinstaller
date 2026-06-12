"""
Settings read-only routes (Phase E.2).

GET handlers extracted from app.py — no writes, no storage/safety/mount duplication.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["settings"])


@router.get("/api/settings")
async def get_settings():
    from app import APP_SETTINGS, CONFIG_PATH, CONFIG_STATE, _user_profile_collect_from_disk

    exp_level = "beginner"
    try:
        cands = _user_profile_collect_from_disk()
        if cands:
            cands.sort(key=lambda x: (x[0], x[1]), reverse=True)
            lv = str(cands[0][2] or "beginner").lower()
            if lv in ("beginner", "advanced", "developer"):
                exp_level = lv
    except Exception:
        pass
    return {
        "status": "success",
        "settings": APP_SETTINGS,
        "config_path": str(CONFIG_PATH),
        "device_id": CONFIG_STATE.get("device_id"),
        "experience_level": exp_level,
    }


@router.get("/api/settings/notifications/email")
async def get_notification_email_settings():
    from app import logger
    from core.notification_settings import build_public_settings

    try:
        return {"status": "success", **build_public_settings()}
    except Exception as exc:
        logger.exception("get_notification_email_settings failed")
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": "Benachrichtigungseinstellungen konnten nicht gelesen werden.",
                "diagnosis_id": "NOTIFY-READ-001",
                "error_class": type(exc).__name__,
            },
        )
