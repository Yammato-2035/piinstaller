from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from core.diagnostics.models import EvidenceRecord, EvidenceSampleResponse, EvidenceSummary

logger = logging.getLogger(__name__)

EVIDENCE_DIR = Path(__file__).resolve().parents[3] / "data" / "diagnostics" / "evidence"
PROFILES_DIR = Path(__file__).resolve().parents[3] / "data" / "diagnostics" / "profiles"


def _json_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return sorted(path.glob("*.json"))


_ALLOWED_EVIDENCE_KEYS = frozenset(EvidenceRecord.model_fields.keys())


def _coerce_evidence_dict(raw: dict[str, Any]) -> dict[str, Any]:
    """Mappt ältere / abweichende Evidence-JSON-Felder auf das EvidenceRecord-Schema."""
    data = dict(raw)
    if "evidence_id" in data and "id" not in data:
        data["id"] = data.pop("evidence_id")
    if "timestamp" not in data:
        if "timestamp_utc" in data:
            data["timestamp"] = data.pop("timestamp_utc")
        elif "date_utc" in data:
            du = str(data.get("date_utc", "")).strip()
            data["timestamp"] = f"{du}T12:00:00Z" if du else "1970-01-01T00:00:00Z"
    for key in ("docs_updated", "faq_updated", "catalog_updated", "tests_added"):
        v = data.get(key, False)
        if isinstance(v, list):
            data[key] = len(v) > 0
        elif v is None:
            data[key] = False

    st = data.get("source_type")
    if st == "runtime_smoke":
        data["source_type"] = "vm_test"

    if not data.get("source_type"):
        data["source_type"] = "hardware_test"
    if not data.get("domain"):
        data["domain"] = "backup_restore"
    if not data.get("platform"):
        data["platform"] = "linux_pc"
    if not data.get("scenario"):
        data["scenario"] = str(data.get("phase") or data.get("run_id") or data.get("id") or "unknown")
    if not (data.get("test_goal") or "").strip():
        data["test_goal"] = str(data.get("scenario") or data.get("phase") or "Hardware / runtime evidence")
    if not data.get("severity"):
        data["severity"] = "medium"
    if not data.get("confidence"):
        data["confidence"] = "medium"

    dl = data.get("diagnosis_links")
    if isinstance(dl, list) and dl and isinstance(dl[0], str):
        data["diagnosis_links"] = [{"diagnosis_id": x, "status": "suspected"} for x in dl]

    extras = {k: data.pop(k) for k in list(data.keys()) if k not in _ALLOWED_EVIDENCE_KEYS}
    if extras:
        rs = data.get("raw_signals")
        base = dict(rs) if isinstance(rs, dict) else {}
        base["_legacy_report"] = extras
        data["raw_signals"] = base

    return data


def load_evidence_records() -> list[EvidenceRecord]:
    records: list[EvidenceRecord] = []
    for fp in _json_files(EVIDENCE_DIR):
        try:
            raw = json.loads(fp.read_text(encoding="utf-8"))
            data = _coerce_evidence_dict(raw)
            records.append(EvidenceRecord.model_validate(data))
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as e:
            logger.warning("diagnostics evidence skipped %s: %s", fp.name, e)
            continue
    return records


def evidence_summary_map() -> dict[str, EvidenceSummary]:
    summary: dict[str, EvidenceSummary] = {}
    for rec in load_evidence_records():
        links = rec.diagnosis_links or []
        if not links and rec.matched_diagnosis_ids:
            links = [{"diagnosis_id": x, "status": "suspected"} for x in rec.matched_diagnosis_ids]
        for link in links:
            if isinstance(link, dict):
                did = str(link.get("diagnosis_id") or "")
                st = str(link.get("status") or "suspected")
            else:
                did = link.diagnosis_id
                st = link.status
            if not did:
                continue
            if did not in summary:
                summary[did] = EvidenceSummary(diagnosis_id=did)
            item = summary[did]
            if st == "confirmed":
                item.confirmed += 1
            elif st == "refuted":
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
