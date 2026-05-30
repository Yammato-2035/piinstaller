"""Prompt-Kandidaten-Stub aus gespeicherten Berichten."""

from __future__ import annotations

from typing import Any

from devserver.models import new_id, utc_now_iso
from devserver.storage import DevServerStorage


def build_prompt_candidate_from_reports(report_ids: list[str], *, storage: DevServerStorage) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    source_ids: list[str] = []
    patterns: list[str] = []
    problem_parts: list[str] = []

    for rid in report_ids:
        report = storage.load_report(rid.strip())
        if not report:
            errors.append(f"report_not_found:{rid}")
            continue
        source_ids.append(rid)
        rtype = str(report.get("report_type") or "manual")
        patterns.append(f"{rtype}@{report.get('node_id')}")
        if report.get("warnings"):
            problem_parts.append(f"{rtype}: {', '.join(report['warnings'][:3])}")
        if report.get("errors"):
            problem_parts.append(f"{rtype} errors: {', '.join(report['errors'][:3])}")

    if not source_ids:
        return {
            "candidate_id": None,
            "status": "failed",
            "created_at": utc_now_iso(),
            "source_report_ids": [],
            "problem_summary": "",
            "observed_patterns": [],
            "suggested_cursor_task": "",
            "required_docs": [],
            "safety_rules": ["no backup", "no restore", "no write"],
            "warnings": warnings,
            "errors": errors or ["no_reports"],
        }

    problem_summary = "; ".join(problem_parts) if problem_parts else "Lab reports collected — review for follow-up task."

    return {
        "candidate_id": new_id("prompt"),
        "status": "draft",
        "created_at": utc_now_iso(),
        "source_report_ids": source_ids,
        "problem_summary": problem_summary,
        "observed_patterns": patterns,
        "suggested_cursor_task": (
            "Review lab telemetry reports and propose a read-only diagnostic or documentation "
            "improvement — no backup, restore, or write actions."
        ),
        "required_docs": [
            "docs/knowledge-base/development/LOCAL_LAB_TELEMETRY.md",
            "docs/knowledge-base/development/READ_ONLY_SSH_CONTROL.md",
            "docs/faq/DEV_SERVER_FAQ_DE.md",
            "docs/faq/DEV_SERVER_FAQ_EN.md",
            "frontend/src/locales/de.json",
            "frontend/src/locales/en.json",
        ],
        "safety_rules": ["no backup", "no restore", "no write"],
        "warnings": warnings,
        "errors": errors,
    }
