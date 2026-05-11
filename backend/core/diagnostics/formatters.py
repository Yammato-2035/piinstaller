from __future__ import annotations

from core.diagnostics.models import DiagnosticCase


def beginner_message(primary: DiagnosticCase) -> str:
    return (
        f"{primary.title_de}: {primary.summary_de} "
        "Bitte zuerst die priorisierten Schritte ausfuehren und keine riskanten Manuell-Fixes starten."
    )


def technical_summary(primary: DiagnosticCase, secondary: list[DiagnosticCase]) -> str:
    ids = ", ".join([primary.id] + [s.id for s in secondary])
    return f"primary={primary.id}; secondary=[{ids}]; domain={primary.domain}; severity={primary.severity}; confidence={primary.confidence}"


def message_by_level(primary: DiagnosticCase) -> dict[str, str]:
    return {
        "beginner": beginner_message(primary),
        "advanced": f"{primary.title_de}: {primary.summary_de} Ursache fokussieren, dann verifizieren.",
        "expert": f"{primary.id} ({primary.domain}) severity={primary.severity} confidence={primary.confidence}",
    }
