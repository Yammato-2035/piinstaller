"""
API-Routen; werden in app.py per include_router eingehängt.
"""

from .pairing import router as pairing_router
from .sessions import router as sessions_router
from .devices import router as devices_router
from .modules import router as modules_router
from .actions import router as actions_router
from .ws import router as ws_router

__all__ = [
    "pairing_router",
    "sessions_router",
    "devices_router",
    "modules_router",
    "actions_router",
    "ws_router",
]
