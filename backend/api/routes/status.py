"""
Lightweight status and metadata routes (Phase E.2).

Read-only GET handlers extracted from app.py.
"""

from __future__ import annotations

from pathlib import Path

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


@router.get("/api/self-update/status")
async def self_update_status():
    """
    Status für 'Auf /opt installieren': Quelle (laufendes Repo) vs. Installation in /opt.
    Wenn die App aus einem Entwicklungsverzeichnis läuft (z. B. /home/volker/piinstaller),
    kann hier ein Update verfügbar sein (neue Version noch nicht in /opt).
    """
    from app import OPT_INSTALL_DIR, _read_version_from_path, get_pi_installer_version

    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    source_version = get_pi_installer_version()
    source_path = str(repo_root)
    installed_version = _read_version_from_path(OPT_INSTALL_DIR) if OPT_INSTALL_DIR.exists() else None
    installed_path = str(OPT_INSTALL_DIR) if OPT_INSTALL_DIR.exists() else None

    is_source_opt = repo_root.resolve() == OPT_INSTALL_DIR.resolve()
    update_available = not is_source_opt and (
        installed_version is None or installed_version != source_version
    )

    deploy_script = repo_root / "scripts" / "deploy-to-opt.sh"
    can_run_deploy = deploy_script.is_file()

    return {
        "status": "success",
        "source_path": source_path,
        "source_version": source_version,
        "installed_path": installed_path,
        "installed_version": installed_version,
        "update_available": update_available,
        "is_running_from_opt": is_source_opt,
        "can_run_deploy": can_run_deploy,
        "deploy_script": str(deploy_script),
    }
