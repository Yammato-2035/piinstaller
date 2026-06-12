"""
Lightweight status and metadata routes (Phase E.2).

Read-only GET handlers extracted from app.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["status"])


@router.get("/api/presets/list")
async def api_list_presets():
    """
    Liefert eine Liste verfügbarer Konfigurations-Presets (Voreinstellungen).
    """
    from app import _list_presets_impl, logger

    if _list_presets_impl is None:
        return {"status": "error", "message": "Presets-Modul nicht verfügbar."}
    try:
        items = _list_presets_impl()
    except Exception as e:
        logger.error("Fehler beim Laden der Presets: %s", e)
        return {"status": "error", "message": f"Fehler beim Laden der Presets: {str(e)}"}
    return {"status": "success", "items": items}


@router.get("/api/debug/routes")
async def debug_routes(request: Request):
    """Listet alle registrierten API-Pfade (z. B. zum Prüfen ob /api/peripherals/scan geladen ist)."""
    from app import get_pi_installer_version

    paths = []
    for r in request.app.routes:
        path = getattr(r, "path", "")
        if path and "/api/" in path:
            paths.append(path)
    return {"paths": sorted(set(paths)), "version": get_pi_installer_version()}


@router.get("/api/user-profile")
async def get_user_profile():
    """
    Gibt das Benutzerprofil zurück (Erfahrungslevel etc.).
    Liest primär neben config.json, sonst Fallback unter ~/.config/pi-installer/.
    """
    from app import UserProfile, _now_iso, _user_profile_collect_from_disk, logger

    try:
        cands = _user_profile_collect_from_disk()
        if cands:
            cands.sort(key=lambda x: (x[0], x[1]), reverse=True)
            updated_at, _mtime, level, _path = cands[0]
            return {"status": "success", "profile": UserProfile(experience_level=level, updated_at=updated_at).dict()}
    except Exception as e:
        logger.error("Fehler beim Lesen von user_profile.json: %s", e, exc_info=True)
    default = UserProfile(experience_level="beginner", updated_at=_now_iso())
    return {"status": "success", "profile": default.dict()}
