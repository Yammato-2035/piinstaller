"""
Network read-only routes (Phase G.4).

Delegates exclusively to ``core.network_info_facade`` — no shell probes, no network writes.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["network"])


@router.get("/api/status")
async def get_status(request: Request):
    """System-Status abrufen"""
    from app import _is_demo_mode
    from core.network_info_facade import build_api_status_payload

    try:
        return build_api_status_payload(use_demo=_is_demo_mode(request))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/system/network")
async def get_system_network(request: Request):
    """Netzwerk-Informationen (IP-Adressen, Hostname) für Frontend-Zugriff."""
    from app import _is_demo_mode, get_logger, logger
    from core.network_info_facade import build_system_network_response

    log = get_logger("network", "status")
    log.step_start("system_network")
    try:
        use_demo = _is_demo_mode(request)
        payload = build_system_network_response(use_demo=use_demo)
        if use_demo:
            log.step_end("system_network", data={"demo": True})
        else:
            log.step_end(
                "system_network",
                data={
                    "hostname": payload.get("hostname"),
                    "ip_count": len(payload.get("ips", [])),
                },
            )
        return payload
    except Exception as e:
        log.step_end("system_network", data={"error": str(e)})
        log.error(str(e), data={"step": "system_network"})
        logger.error(f"Fehler beim Abrufen der Netzwerk-Info: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})
