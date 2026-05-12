from __future__ import annotations

from core.diagnostics.evidence_store import evidence_sample, evidence_schema, evidence_summary_map
from core.diagnostics.formatters import message_by_level, technical_summary
from core.diagnostics.matcher import match_diagnoses
from core.diagnostics.models import (
    DiagnosticCase,
    DiagnosticsAnalyzeRequest,
    DiagnosticsAnalyzeResponse,
    DiagnosticsEvidence,
    EvidenceSampleResponse,
)
from core.diagnostics.registry import get_case_by_id, get_catalog
from core.diagnostics.severity import max_confidence, max_severity
from core.diagnostics.sources import normalized_signals


def _to_ref(item: DiagnosticCase) -> dict[str, str]:
    return {
        "id": item.id,
        "domain": item.domain,
        "severity": item.severity,
        "confidence": item.confidence,
    }


def run_diagnostics(req: DiagnosticsAnalyzeRequest) -> DiagnosticsAnalyzeResponse:
    hits = match_diagnoses(req)
    primary = hits[0]
    secondary = hits[1:4]
    messages = message_by_level(primary)
    actions = sorted(primary.recommended_actions, key=lambda a: a.priority)

    evidence = [
        DiagnosticsEvidence(source="signals", key=k, value=v)
        for k, v in normalized_signals(req).items()
    ]
    if req.question:
        evidence.append(DiagnosticsEvidence(source="question", key="question", value=req.question))

    return DiagnosticsAnalyzeResponse(
        primary_diagnosis=_to_ref(primary),
        secondary_diagnoses=[_to_ref(x) for x in secondary],
        severity=max_severity([x.severity for x in [primary] + secondary]),
        confidence=max_confidence([x.confidence for x in [primary] + secondary]),
        messages=messages,
        user_message_beginner=messages["beginner"],
        technical_summary=technical_summary(primary, secondary),
        actions_now=[a.text_de for a in actions[:3]],
        actions_later=[a.text_de for a in actions[3:]],
        recommended_actions=[a.model_dump() for a in actions],
        safe_auto_actions=primary.safe_auto_actions,
        evidence=evidence[:25],
        requires_confirmation=primary.requires_confirmation,
    )


def catalog() -> list[dict]:
    smap = evidence_summary_map()
    out: list[dict] = []
    for d in get_catalog():
        m = d.model_copy(deep=True)
        ev = smap.get(m.id)
        if ev is not None:
            m.evidence_counts = {
                "suspected": ev.suspected,
                "confirmed": ev.confirmed,
                "refuted": ev.refuted,
            }
            m.seen_in_platforms = ev.seen_in_platforms
            m.common_storage_contexts = ev.common_storage_contexts
            m.common_boot_contexts = ev.common_boot_contexts
        out.append(m.model_dump())
    return out


def diagnosis_by_id(diagnosis_id: str) -> dict | None:
    item = get_case_by_id(diagnosis_id)
    if item is None:
        return None
    m = item.model_copy(deep=True)
    ev = evidence_summary_map().get(m.id)
    if ev is not None:
        m.evidence_counts = {
            "suspected": ev.suspected,
            "confirmed": ev.confirmed,
            "refuted": ev.refuted,
        }
        m.seen_in_platforms = ev.seen_in_platforms
        m.common_storage_contexts = ev.common_storage_contexts
        m.common_boot_contexts = ev.common_boot_contexts
    return m.model_dump()


def get_evidence_schema() -> dict:
    return evidence_schema()


def get_evidence_sample() -> EvidenceSampleResponse:
    return evidence_sample()
