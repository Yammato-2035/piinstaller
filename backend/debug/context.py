"""
ContextVars für request_id, module_id, step_id (optional).
"""

from contextvars import ContextVar
from typing import Optional

request_id_ctx: ContextVar[Optional[str]] = ContextVar("debug_request_id", default=None)
module_id_ctx: ContextVar[Optional[str]] = ContextVar("debug_module_id", default=None)
step_id_ctx: ContextVar[Optional[str]] = ContextVar("debug_step_id", default=None)


def set_request_id(rid: Optional[str] = None) -> Optional[str]:
    """Setzt request_id für den aktuellen Kontext. Gibt den gesetzten Wert zurück."""
    import uuid
    val = rid if (rid is not None and rid != "") else str(uuid.uuid4())
    request_id_ctx.set(val)
    return val


def get_request_id() -> Optional[str]:
    """Liefert request_id des aktuellen Kontexts (nullable)."""
    return request_id_ctx.get()


def set_module_id(mid: Optional[str]) -> None:
    """Setzt module_id (optional, für Scopes)."""
    module_id_ctx.set(mid)


def get_module_id() -> Optional[str]:
    return module_id_ctx.get()


def set_step_id(sid: Optional[str]) -> None:
    """Setzt step_id (optional)."""
    step_id_ctx.set(sid)


def get_step_id() -> Optional[str]:
    return step_id_ctx.get()


def bind_request_id(rid: Optional[str] = None):
    """Setzt request_id, gibt Token für reset zurück."""
    import uuid
    val = rid if (rid is not None and rid != "") else str(uuid.uuid4())
    return request_id_ctx.set(val)


def reset_request_id(token) -> None:
    """Stellt ContextVar auf Zustand vor bind_request_id wieder her."""
    request_id_ctx.reset(token)
