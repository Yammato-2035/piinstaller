"""
REST-Endpunkt für Modul-Aktionen.
POST /api/modules/{module_id}/actions/{action_id}: Aktion ausführen (Schreibrecht erforderlich).
"""

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import get_current_session
from core.permissions import require_write
from core.registry import get_registry
from models.action import ActionInvocation, ActionResult
from storage.db import audit_log_insert

router = APIRouter(prefix="/api/modules", tags=["actions"])


@router.post("/{module_id}/actions/{action_id}", response_model=ActionResult)
async def perform_action(
    module_id: str,
    action_id: str,
    body: ActionInvocation,
    session=Depends(get_current_session),
):
    """
    Führt eine Modul-Aktion aus. Erfordert mindestens Rolle controller (Schreibaktion).
    viewer darf keine Schreibaktionen auslösen.

    Jede Ausführung wird auditiert (wer/welches Gerät, welches Modul,
    welche Aktion, Erfolg/Misserfolg) — vorher fehlte hier jede Audit-Spur,
    obwohl dies die sicherheitsrelevanteste Remote-Operation ist
    (siehe Security Review docs/review/security/modules/remote.md, Punkt 4).
    """
    require_write(session)
    module = get_registry().get(module_id)
    if not module:
        audit_log_insert(
            "remote_action_failed",
            device_id=session.device_id,
            details=f"module={module_id} action={action_id} reason=module_not_found",
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modul nicht gefunden")
    payload = body.payload if body.payload is not None else {}
    try:
        result = module.perform_action(action_id, payload)
    except Exception as exc:
        audit_log_insert(
            "remote_action_failed",
            device_id=session.device_id,
            details=f"module={module_id} action={action_id} exception={exc.__class__.__name__}",
        )
        raise
    success = result.get("success", False)
    audit_log_insert(
        "remote_action_executed" if success else "remote_action_failed",
        device_id=session.device_id,
        details=f"module={module_id} action={action_id} success={success}",
    )
    return ActionResult(
        success=success,
        message=result.get("message"),
        data=result.get("data"),
    )
