"""
REST-Endpunkt für Geräte-Info (der Pi als Remote-Host).
GET /api/device: Geräte-ID, Name, ggf. Basis-URL (geschützt).
"""

from typing import Any

from fastapi import APIRouter, Request, Depends

from core.auth import get_current_session

router = APIRouter(prefix="/api", tags=["device"])


@router.get("/device")
async def device_info(request: Request, _session=Depends(get_current_session)):
    """
    Liefert Informationen zum aktuellen Gerät (Pi), auf dem die Remote-API läuft.
    Erfordert gültige Session.
    """
    device_id = getattr(request.app.state, "device_id", "") or "unknown-device"
    settings = getattr(request.app.state, "app_settings", None) or {}
    remote = (settings.get("remote") or {}) if isinstance(settings, dict) else {}
    name = (remote.get("REMOTE_DEVICE_NAME") or "").strip() or None
    base_url = (remote.get("REMOTE_BASE_URL") or remote.get("REMOTE_PUBLIC_HOST") or "").strip() or None
    out: dict[str, Any] = {"device_id": device_id}
    if name:
        out["name"] = name
    if base_url:
        out["base_url"] = base_url
    return out
