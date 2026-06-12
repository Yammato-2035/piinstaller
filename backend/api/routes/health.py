"""
Health and lightweight status routes (Phase E.1).

Read-only endpoints extracted from app.py — no storage/safety/mount duplication.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

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


@router.get("/api/logs/tail")
async def logs_tail(lines: int = 200):
    from app import LOG_PATH

    try:
        lines = max(10, min(int(lines), 2000))
    except Exception:
        lines = 200
    p = Path(LOG_PATH)
    if not p.exists():
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": "Log-Datei nicht gefunden. Backend neu starten (Logging ging zuvor nur auf Konsole).",
                "path": str(p),
            },
        )
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        out = "\n".join(txt.splitlines()[-lines:])
        return {"status": "success", "path": str(p), "lines": lines, "content": out}
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e), "path": str(p)})
