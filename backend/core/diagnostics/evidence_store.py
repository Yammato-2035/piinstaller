from __future__ import annotations

import json
from pathlib import Path

from core.diagnostics.models import EvidenceRecord, EvidenceSampleResponse, EvidenceSummary

EVIDENCE_DIR = Path(__file__).resolve().parents[3] / "data" / "diagnostics" / "evidence"
PROFILES_DIR = Path(__file__).resolve().parents[3] / "data" / "diagnostics" / "profiles"


def _json_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return sorted(path.glob("*.json"))


def load_evidence_records() -> list[EvidenceRecord]:
    records: list[EvidenceRecord] = []
    for fp in _json_files(EVIDENCE_DIR):
        data = json.loads(fp.read_text(encoding="utf-8"))
        records.append(EvidenceRecord(**data))
    return records


def evidence_summary_map() -> dict[str, EvidenceSummary]:
    summary: dict[str, EvidenceSummary] = {}
    for rec in load_evidence_records():
        links = rec.diagnosis_links or []
        if not links and rec.matched_diagnosis_ids:
            links = [{"diagnosis_id": x, "status": "suspected"} for x in rec.matched_diagnosis_ids]
        for link in links:
            did = link.diagnosis_id
            if did not in summary:
                summary[did] = EvidenceSummary(diagnosis_id=did)
            item = summary[did]
            if link.status == "confirmed":
                item.confirmed += 1
            elif link.status == "refuted":
                item.refuted += 1
            else:
                item.suspected += 1
            if rec.platform not in item.seen_in_platforms:
                item.seen_in_platforms.append(rec.platform)
            if rec.storage_profile and rec.storage_profile not in item.common_storage_contexts:
                item.common_storage_contexts.append(rec.storage_profile)
            if rec.boot_profile and rec.boot_profile not in item.common_boot_contexts:
                item.common_boot_contexts.append(rec.boot_profile)
    return summary


def evidence_schema() -> dict:
    return EvidenceRecord.model_json_schema()


def evidence_sample() -> EvidenceSampleResponse:
    records = load_evidence_records()
    if records:
        return EvidenceSampleResponse(sample=records[0], total_records=len(records))
    fallback = EvidenceRecord(
        id="EVIDENCE-SAMPLE-000",
        timestamp="1970-01-01T00:00:00Z",
        source_type="manual_test",
        domain="backup_restore",
        platform="vm",
        scenario="sample",
        test_goal="sample",
        outcome="inconclusive",
        severity="low",
        confidence="low",
    )
    return EvidenceSampleResponse(sample=fallback, total_records=0)
