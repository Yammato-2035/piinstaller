from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deploy.runner_lab_acceptance_aggregator import build_runner_lab_acceptance_summary
from deploy.runner_lab_readiness_status import build_runner_lab_readiness_status
from deploy.runner_release_readiness import build_runner_release_readiness_matrix
from deploy.runner_runtime_result_validator import validate_runner_runtime_result_bundle
from deploy.runner_runtime_runbook_export import build_runner_runtime_runbook_export_package

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ALLOWED_ROOTS = (
    (_REPO_ROOT / "docs" / "evidence" / "lab-acceptance").resolve(strict=False),
    (_REPO_ROOT / "docs" / "runbooks" / "deploy-runner" / "reports").resolve(strict=False),
)


def _resolve_safe_target(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "empty_target_path"
    p = Path(raw)
    if p.is_absolute():
        return None, "absolute_target_path_forbidden"
    if ".." in p.parts:
        return None, "traversal_path_forbidden"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "symlink_path_forbidden"
        if cur.parent == cur:
            break
        cur = cur.parent
    target = unresolved.resolve(strict=False)
    if not any(str(target).startswith(str(root) + os.sep) or str(target) == str(root) for root in _ALLOWED_ROOTS):
        return None, "target_outside_allowed_roots"
    return target, None


def _atomic_write(path: Path, content: str) -> None:
    os.makedirs(str(path.parent), exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _report_markdown(*, lang: str, report_id: str, generated_at: str, acceptance: dict[str, Any]) -> str:
    de = lang == "de"
    scope = "Read-only Lab-Abnahmebericht ohne Runtime-Ausfuehrung." if de else "Read-only lab acceptance report without runtime execution."
    inputs = [
        "Lab Readiness Acceptance Aggregator",
        "Runtime Result Ingestion Validator",
        "Runtime Runbook Export Package",
        "Lab Readiness Status",
        "Runner Release Readiness Matrix",
    ]
    lines = [
        "# LAB ACCEPTANCE REPORT (DE)" if de else "# LAB ACCEPTANCE REPORT (EN)",
        "",
        f"- Report-ID: `{report_id}`",
        f"- Generated: `{generated_at}`",
        f"- Acceptance Status: `{acceptance.get('acceptance_status', 'blocked')}`",
        f"- Operator Decision Required: `{bool(acceptance.get('operator_decision_required', True))}`",
        "",
        "## Scope",
        scope,
        "",
        "## Inputquellen" if de else "## Input Sources",
    ]
    lines.extend([f"- {x}" for x in inputs])
    lines.extend(
        [
            "",
            "## Runbook Outcomes",
        ]
    )
    for item in list(acceptance.get("runbook_outcomes") or []):
        lines.append(
            f"- `{item.get('runbook_id')}`: status=`{item.get('status')}`, "
            f"evidence=`{item.get('evidence_status')}`, safety=`{item.get('safety_status')}`"
        )
    lines.extend(
        [
            "",
            "## Evidence Summary",
            f"- `{json.dumps(acceptance.get('evidence_summary') or {}, ensure_ascii=True, sort_keys=True)}`",
            "",
            "## Blocking Findings",
        ]
    )
    for f in list(acceptance.get("blocking_findings") or []):
        lines.append(f"- `{f}`")
    lines.extend(
        [
            "",
            "## Residual Risks",
        ]
    )
    for risk in list(acceptance.get("residual_risks") or []):
        lines.append(f"- `{risk}`")
    lines.extend(
        [
            "",
            "## Required Repeats",
        ]
    )
    for rb in list(acceptance.get("required_repeats") or []):
        lines.append(f"- `{rb}`")
    lines.extend(
        [
            "",
            "## Nicht-Freigaben" if de else "## Non-Approvals",
            "- nicht production-ready" if de else "- not production-ready",
            "- keine automatische Freigabe" if de else "- no automatic approval",
            "- nur Lab-Kandidat bei passender Evidence" if de else "- lab candidate only with matching evidence",
            "",
            "## Abnahmeentscheidung" if de else "## Acceptance Decision",
            "- lab_ready_candidate",
            "- repeat_required",
            "- blocked",
            "",
        ]
    )
    return "\n".join(lines)


def _summary_markdown(*, lang: str, acceptance: dict[str, Any]) -> str:
    de = lang == "de"
    status = str(acceptance.get("acceptance_status") or "blocked")
    pass_count = int((acceptance.get("evidence_summary") or {}).get("pass_count") or 0)
    missing = list((acceptance.get("evidence_summary") or {}).get("missing_runbooks") or [])
    if de:
        return (
            "# LAB ACCEPTANCE SUMMARY (DE)\n\n"
            f"- Ergebnis: `{status}`\n"
            f"- Was bestanden hat: `{pass_count}` Runbooks mit pass\n"
            f"- Was offen bleibt: `{', '.join(missing) if missing else 'none'}`\n"
            "- Warum keine Produktionsfreigabe: not production-ready; residual risks bleiben aktiv und Scope ist lab-only\n"
            "- Naechste manuelle Entscheidung: Operator bewertet repeat_required/blocked/candidate bewusst\n"
        )
    return (
        "# LAB ACCEPTANCE SUMMARY (EN)\n\n"
        f"- Result: `{status}`\n"
        f"- Passed: `{pass_count}` runbooks with pass\n"
        f"- Open items: `{', '.join(missing) if missing else 'none'}`\n"
        "- Why no production approval: not production-ready; residual risks remain active and scope is lab-only\n"
        "- Next manual decision: operator evaluates repeat_required/blocked/candidate explicitly\n"
    )


def build_runner_lab_acceptance_report_export(
    *,
    acceptance: dict[str, Any] | None = None,
    target_files: dict[str, str] | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    generated_files: list[str] = []

    validator_stub = validate_runner_runtime_result_bundle(result_files=[], acceptance_decision="blocked")
    runbook_export = build_runner_runtime_runbook_export_package()
    lab_status = build_runner_lab_readiness_status()
    release = build_runner_release_readiness_matrix()
    acceptance_data = dict(acceptance or {})
    if not acceptance_data:
        acceptance_data = build_runner_lab_acceptance_summary(validated_runtime_results=validator_stub)

    report_id = "RUNNER_LAB_ACCEPTANCE_REPORT_V1"
    generated_at = datetime.now(timezone.utc).isoformat()

    default_targets = {
        "report_de": "docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_DE.md",
        "report_en": "docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_EN.md",
        "report_json": "docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT.json",
        "summary_de": "docs/runbooks/deploy-runner/reports/LAB_ACCEPTANCE_SUMMARY_DE.md",
        "summary_en": "docs/runbooks/deploy-runner/reports/LAB_ACCEPTANCE_SUMMARY_EN.md",
    }
    targets = dict(default_targets)
    targets.update(dict(target_files or {}))

    report_json = {
        "report_id": report_id,
        "generated_at": generated_at,
        "acceptance_status": acceptance_data.get("acceptance_status", "blocked"),
        "operator_decision_required": bool(acceptance_data.get("operator_decision_required", True)),
        "runbook_outcomes": list(acceptance_data.get("runbook_outcomes") or []),
        "evidence_summary": dict(acceptance_data.get("evidence_summary") or {}),
        "blocking_findings": list(acceptance_data.get("blocking_findings") or []),
        "residual_risks": list(acceptance_data.get("residual_risks") or []),
        "required_repeats": list(acceptance_data.get("required_repeats") or []),
        "warnings": list(acceptance_data.get("warnings") or []),
        "errors": list(acceptance_data.get("errors") or []),
    }

    contents = {
        "report_de": _report_markdown(
            lang="de",
            report_id=report_id,
            generated_at=generated_at,
            acceptance=acceptance_data,
        ),
        "report_en": _report_markdown(
            lang="en",
            report_id=report_id,
            generated_at=generated_at,
            acceptance=acceptance_data,
        ),
        "report_json": json.dumps(report_json, ensure_ascii=True, indent=2) + "\n",
        "summary_de": _summary_markdown(lang="de", acceptance=acceptance_data),
        "summary_en": _summary_markdown(lang="en", acceptance=acceptance_data),
    }

    for key, rel in targets.items():
        resolved, err = _resolve_safe_target(rel)
        if err or resolved is None:
            errors.append(f"{key}:{err or 'invalid_target'}")
            continue
        if resolved.exists() and resolved.is_symlink():
            errors.append(f"{key}:symlink_target_forbidden")
            continue
        _atomic_write(resolved, contents.get(key, ""))
        generated_files.append(str(Path(rel)))

    summary = {
        "acceptance_status": acceptance_data.get("acceptance_status", "blocked"),
        "operator_decision_required": bool(acceptance_data.get("operator_decision_required", True)),
        "lab_readiness_status": lab_status.get("lab_readiness_status"),
        "release_readiness_status": release.get("readiness_status"),
        "runtime_export_status": runbook_export.get("export_status"),
    }

    export_status = "ok"
    if errors:
        export_status = "blocked"
    elif warnings:
        export_status = "review_required"

    return {
        "export_status": export_status,
        "report_id": report_id,
        "generated_files": generated_files,
        "summary": summary,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
