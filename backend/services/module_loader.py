"""
Registriert alle Remote-Module in der zentralen Registry.
Neue Module hier eintragen; API-Struktur bleibt unverändert.
"""

import logging
from typing import Optional

from core.registry import ModuleRegistry, get_registry
from services.sabrina_tuner_service import SabrinaTunerService
from services.pi_installer_service import PiInstallerService

logger = logging.getLogger(__name__)


def register_all(registry: Optional[ModuleRegistry] = None) -> None:
    """Registriert alle verfügbaren Remote-Module (Sabrina Tuner, PI-Installer)."""
    reg = registry or get_registry()
    reg.register(SabrinaTunerService())
    reg.register(PiInstallerService())
    logger.debug("Remote-Module registriert: sabrina-tuner, pi-installer")
