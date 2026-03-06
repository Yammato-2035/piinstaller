"""
REST-Endpunkt für Modul-Aktionen.
POST /api/modules/{module_id}/actions/{action_id}: Aktion ausführen (Schreibrecht erforderlich).
"""

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import get_current_session
from core.permissions import require_write
from core.registry import get_registry
from models.action import ActionInvocation, ActionResult

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
    """
    require_write(session)
    module = get_registry().get(module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modul nicht gefunden")
    payload = body.payload if body.payload is not None else {}
    result = module.perform_action(action_id, payload)
    return ActionResult(
        success=result.get("success", False),
        message=result.get("message"),
        data=result.get("data"),
    )
