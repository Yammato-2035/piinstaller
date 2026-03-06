"""
REST-Endpunkte für Remote-Module (Registry).
GET /api/modules: Liste aller Module (Deskriptoren).
GET /api/modules/{module_id}: Ein Modul (Deskriptor).
GET /api/modules/{module_id}/state: Aktueller State eines Moduls.
Alle geschützt durch Session.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import get_current_session
from core.registry import get_registry
from models.module import ModuleDescriptor

router = APIRouter(prefix="/api/modules", tags=["modules"])


@router.get("", response_model=List[ModuleDescriptor])
async def list_modules(_session=Depends(get_current_session)):
    """Liefert die Deskriptoren aller registrierten Module."""
    return get_registry().get_descriptors()


@router.get("/{module_id}", response_model=ModuleDescriptor)
async def get_module(module_id: str, _session=Depends(get_current_session)):
    """Liefert den Deskriptor eines Moduls."""
    module = get_registry().get(module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modul nicht gefunden")
    return module.descriptor()


@router.get("/{module_id}/state")
async def get_module_state(module_id: str, _session=Depends(get_current_session)):
    """Liefert den aktuellen State eines Moduls."""
    module = get_registry().get(module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modul nicht gefunden")
    return module.get_state()
