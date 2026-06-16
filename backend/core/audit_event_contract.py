"""
Public-safe audit event contract — structure only, no operator internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

CONTRACT_VERSION = 1


class AuditEventArea(str, Enum):
    BACKUP = "backup"
    RESTORE = "restore"
    VERIFY = "verify"
    RESCUE = "rescue"
    RUNTIME = "runtime"
    DEPLOY = "deploy"
    PLATFORM = "platform"


@dataclass(frozen=True)
class AuditEvent:
    """Public-safe audit event envelope (no secrets in message fields)."""

    event_id: str
    created_at: str
    area: AuditEventArea
    action: str
    actor: str
    outcome: str
    message: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    contract_version: int = CONTRACT_VERSION

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "created_at": self.created_at,
            "area": self.area.value,
            "action": self.action,
            "actor": self.actor,
            "outcome": self.outcome,
            "message": self.message,
            "evidence_refs": list(self.evidence_refs),
            "contract_version": self.contract_version,
        }
