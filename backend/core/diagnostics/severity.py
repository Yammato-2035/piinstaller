from __future__ import annotations

from core.diagnostics.models import ConfidenceLevel, Severity

SEVERITY_ORDER: dict[Severity, int] = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

CONFIDENCE_ORDER: dict[ConfidenceLevel, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
}


def max_severity(values: list[Severity]) -> Severity:
    if not values:
        return "info"
    return max(values, key=lambda v: SEVERITY_ORDER[v])


def max_confidence(values: list[ConfidenceLevel]) -> ConfidenceLevel:
    if not values:
        return "low"
    return max(values, key=lambda v: CONFIDENCE_ORDER[v])
