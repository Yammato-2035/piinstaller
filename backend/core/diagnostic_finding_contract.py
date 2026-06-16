"""
Public-safe diagnostic finding contract — plan-only recommendations, no internal rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

CONTRACT_VERSION = 1


class FindingSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecommendationMode(str, Enum):
    """Public contract: diagnostics are plan-only in client context."""

    PLAN_ONLY = "plan_only"
    DOCUMENTATION = "documentation"


@dataclass(frozen=True)
class DiagnosticFinding:
    """Public-safe finding shape for clients and OpenAPI."""

    code: str
    title: str
    message: str
    severity: FindingSeverity
    area: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    recommendation_mode: RecommendationMode = RecommendationMode.PLAN_ONLY
    contract_version: int = CONTRACT_VERSION

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "area": self.area,
            "evidence_refs": list(self.evidence_refs),
            "recommendation_mode": self.recommendation_mode.value,
            "contract_version": self.contract_version,
            # Explicit: no execute/apply/repair in public contract
            "execute_allowed": False,
        }
