"""
Rollen und Rechteprüfung für Remote-Companion.
Rollen: viewer, controller, admin, sync.
viewer: nur Lesen; controller: Lesen + Modul-Aktionen (Schreiben); admin: alles; sync: für spätere Sync-Integration.
"""

from typing import Tuple

from fastapi import HTTPException, status

from core.auth import SessionContext

# Erlaubte Rollen (eine Quelle der Wahrheit)
ROLES: Tuple[str, ...] = ("viewer", "controller", "admin", "sync")

# Hierarchie für "mindestens Rolle X": Index höher = mehr Rechte
ROLE_ORDER = ("viewer", "controller", "admin", "sync")


def role_level(role: str) -> int:
    """Index in ROLE_ORDER; unbekannte Rolle = 0 (viewer)."""
    try:
        return ROLE_ORDER.index(role)
    except ValueError:
        return 0


def has_min_role(session: SessionContext, min_role: str) -> bool:
    """True, wenn session.role mindestens min_role hat (nach ROLE_ORDER)."""
    return role_level(session.role) >= role_level(min_role)


def require_roles(session: SessionContext, *allowed_roles: str) -> None:
    """
    Prüft, ob session.role in allowed_roles ist. Sonst 403.
    Für pro-Route-Prüfung: z. B. require_roles(session, "controller", "admin").
    """
    if session.role in allowed_roles:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Unzureichende Rechte. Erforderlich: eine von {allowed_roles}",
    )


def require_min_role(session: SessionContext, min_role: str) -> None:
    """Prüft, ob session mindestens min_role hat. Sonst 403."""
    if has_min_role(session, min_role):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Unzureichende Rechte. Mindestens Rolle '{min_role}' erforderlich.",
    )


def can_perform_write(session: SessionContext) -> bool:
    """True, wenn Rolle Schreibaktionen ausführen darf (controller, admin). viewer darf nicht."""
    return session.role in ("controller", "admin")


def require_write(session: SessionContext) -> None:
    """Erzwingt Schreibrecht (controller oder admin). viewer wird abgewiesen."""
    if can_perform_write(session):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Schreibaktionen sind für Ihre Rolle nicht erlaubt (viewer).",
    )


def require_admin(session: SessionContext) -> None:
    """Erzwingt admin-Rolle für Admin-Endpunkte."""
    require_roles(session, "admin")
