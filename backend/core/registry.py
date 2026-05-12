"""
Modul-Registry und RemoteModule-Protokoll.
Module liefern: descriptor(), get_state(), perform_action(action_id, payload), optional subscribe_topics().
Neue Module können registriert werden, ohne die API-Struktur zu ändern.
"""

import logging
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from models.module import ModuleDescriptor

logger = logging.getLogger(__name__)


@runtime_checkable
class RemoteModule(Protocol):
    """Vertrag für Remote-Module."""

    def descriptor(self) -> ModuleDescriptor:
        """Liefert die öffentliche Beschreibung des Moduls."""
        ...

    def get_state(self) -> dict[str, Any]:
        """Aktueller Modul-State (für GET /api/modules/{id}/state)."""
        ...

    def perform_action(self, action_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Führt eine Aktion aus. Rückgabe: {success, message?, data?}."""
        ...

    def subscribe_topics(self) -> List[str]:
        """Optionale Eventbus-Topics, die dieses Modul publiziert (z. B. für WebSocket)."""
        ...


class ModuleRegistry:
    """Zentrale Registry für Remote-Module."""

    def __init__(self) -> None:
        self._modules: Dict[str, RemoteModule] = {}

    def register(self, module: RemoteModule) -> None:
        """Registriert ein Modul (id aus descriptor())."""
        desc = module.descriptor()
        self._modules[desc.id] = module
        logger.info("Modul registriert: %s", desc.id)

    def get(self, module_id: str) -> Optional[RemoteModule]:
        """Liefert ein Modul nach ID oder None."""
        return self._modules.get(module_id)

    def get_all(self) -> List[RemoteModule]:
        """Liefert alle registrierten Module."""
        return list(self._modules.values())

    def get_descriptors(self) -> List[ModuleDescriptor]:
        """Liefert alle Modul-Beschreibungen."""
        return [m.descriptor() for m in self._modules.values()]


# Singleton-Registry (wird bei Import über module_loader befüllt)
_registry = ModuleRegistry()


def get_registry() -> ModuleRegistry:
    return _registry


# Module aus services laden (Sabrina Tuner, PI-Installer); keine doppelte Stub-Logik
try:
    from services.module_loader import register_all
    register_all(_registry)
except ImportError:
    logger.warning("services.module_loader nicht importierbar; Registry bleibt leer")
