"""
Pydantic-Modelle für Remote-Companion (Pairing, Session, Gerät, Audit).
"""

from .pairing import (
    PairingTicketCreate,
    PairingTicketRow,
    PairingTicketStatus,
    PairingClaimRequest,
    PairingCreateResponse,
    PairingClaimResponse,
)
from .session import SessionCreate, SessionRow, SessionInfo
from .device import RemoteDeviceProfileCreate, RemoteDeviceProfileRow
from .audit import AuditLogCreate, AuditLogRow
from .module import ModuleDescriptor
from .widget import WidgetDescriptor
from .action import ActionDescriptor, ActionInvocation, ActionResult
from .events import EventMessage, EVENT_TOPICS

__all__ = [
    "PairingTicketCreate",
    "PairingTicketRow",
    "PairingTicketStatus",
    "PairingClaimRequest",
    "PairingCreateResponse",
    "PairingClaimResponse",
    "SessionCreate",
    "SessionRow",
    "SessionInfo",
    "RemoteDeviceProfileCreate",
    "RemoteDeviceProfileRow",
    "AuditLogCreate",
    "AuditLogRow",
    "ModuleDescriptor",
    "WidgetDescriptor",
    "ActionDescriptor",
    "ActionInvocation",
    "ActionResult",
    "EventMessage",
    "EVENT_TOPICS",
]
