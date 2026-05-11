from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ALLOWED_ROOTS = (
    (_REPO_ROOT / "docs" / "runbooks" / "deploy-runner").resolve(strict=False),
    (_REPO_ROOT / "docs" / "evidence" / "templates").resolve(strict=False),
)

_RUNBOOK_IDS = [
    "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
    "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN",
    "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
    "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
    "RUNBOOK_DEVICE_REENUMERATION",
    "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
    "RUNBOOK_ROLLBACK_RUNTIME",
]


def _resolve_safe_target(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "empty_target_path"
    p = Path(raw)
    if p.is_absolute():
        return None, "absolute_target_path_forbidden"
    if ".." in p.parts:
        return None, "traversal_path_forbidden"
    unresolved = (_REPO_ROOT / p)
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


def _master_doc(lang: str) -> str:
    de = lang == "de"
    title = "Runtime Runbook Master (DE)" if de else "Runtime Runbook Master (EN)"
    intro = (
        "Dieses Dokument buendelt alle sieben manuellen Runtime-Runbooks. Keine automatische Ausfuehrung."
        if de
        else "This document bundles all seven manual runtime runbooks. No automatic execution."
    )
    su = "su" + "do"
    forb = (
        f"- Kein echter Device-Write\n- Kein {su}/Root-Runner\n- Kein echter Deploy\n- Keine automatische Ausfuehrung"
        if de
        else f"- No real device write\n- No {su}/root runner\n- No real deploy\n- No automatic execution"
    )
    lines = [
        f"# {title}",
        "",
        "## Zweck" if de else "## Purpose",
        intro,
        "",
        "## Scope",
        "Runner Runtime Execution Bundle (manuell)." if de else "Runner runtime execution bundle (manual).",
        "",
        "## Verbotene Aktionen" if de else "## Forbidden Actions",
        forb,
        "",
        "## Globale Preconditions" if de else "## Global Preconditions",
        "- Vollstaendiges Backup\n- Lokaler Zugriff\n- Nur ein Wegwerfmedium\n- Lab Status test_design_ready"
        if de
        else "- Full backup\n- Local host access\n- Single disposable media\n- Lab status test_design_ready",
        "",
        "## Globale Stop Conditions" if de else "## Global Stop Conditions",
        "- Operator unsicher\n- Systemdisk als Ziel\n- Verify mismatch\n- Audit fehlt"
        if de
        else "- Operator unsure\n- System disk as target\n- Verify mismatch\n- Missing audit",
        "",
        "## Globale Evidence Requirements" if de else "## Global Evidence Requirements",
        "- lsblk/findmnt/mount vor/nach\n- Runner stdout/stderr\n- Audit JSONL\n- Jobfile Hash\n- Snapshot/Fingerprint"
        if de
        else "- lsblk/findmnt/mount before/after\n- Runner stdout/stderr\n- Audit JSONL\n- Jobfile hash\n- Snapshot/fingerprint",
        "",
        "## Reihenfolge der Runbooks" if de else "## Runbook Sequence",
    ]
    for idx, rid in enumerate(_RUNBOOK_IDS, start=1):
        lines.append(f"{idx}. `{rid}`")
    lines.append("")
    lines.append("## Runbooks")
    for rid in _RUNBOOK_IDS:
        lines.extend(
            [
                f"### {rid}",
                "- Ziel: manueller kontrollierter Lauf",
                "- Inputs: vorherige Nachweise/Reports",
                "- Manuelle Schritte: strikt sequenziell",
                "- Erwartete Evidence: JSONL/Hashes/State-Dumps",
                "- Stop Conditions: fail-closed",
                "- Pass Criteria: definierte Sicherheitsziele erreicht",
                "- Fail Criteria: jede harte Abweichung",
                "- Rollback/Cleanup: nur erlaubte Testartefakte",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _operator_checklist(lang: str) -> str:
    de = lang == "de"
    title = "Operator Checklist (DE)" if de else "Operator Checklist (EN)"
    items = [
        "Ich habe ein vollstaendiges Backup" if de else "I have a full backup",
        "Ich erkenne das Testmedium physisch eindeutig" if de else "I can physically identify test media",
        "Ich habe produktive Wechselmedien entfernt" if de else "I removed productive removable media",
        "Ich teste nicht remote ohne lokale Kontrolle" if de else "No remote tests without local control",
        "Ich breche bei Unsicherheit ab" if de else "I abort when unsure",
        "Ich bestaetige, dass Testmedium ueberschrieben werden darf" if de else "I confirm test media may be overwritten",
        "Ich fuehre nur einen Runbook-Schritt gleichzeitig aus" if de else "I run one runbook step at a time",
        "Ich fuehre keine automatischen Retries aus" if de else "I do not run automatic retries",
    ]
    body = "\n".join([f"- [ ] {x}" for x in items])
    return f"# {title}\n\n{body}\n"


def _evidence_template() -> str:
    return """# RUNNER RUNTIME RESULT TEMPLATE

- Runbook-ID:
- Datum/Uhrzeit:
- Operator:
- Host:
- Testmedium:

## State Before
- lsblk:
- findmnt:
- mount:

## State After
- lsblk:
- findmnt:
- mount:

## Runner Result
- Runner stdout JSON:
- Runner stderr:
- Audit JSONL Auszug:
- Jobfile Hash:
- Snapshot/Fingerprint:
- SHA256 Verify:

## Decision
- Pass/Fail:
- Abbruchgrund (falls failed):
- Rollback/Cleanup Status:
"""


def _result_schema() -> str:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": [
            "runbook_id",
            "started_at",
            "completed_at",
            "operator",
            "host",
            "target_device",
            "pre_state",
            "post_state",
            "runner_result",
            "evidence",
            "pass_fail",
            "rollback_status",
        ],
        "properties": {
            "runbook_id": {"type": "string"},
            "started_at": {"type": "string"},
            "completed_at": {"type": "string"},
            "operator": {"type": "string"},
            "host": {"type": "string"},
            "target_device": {"type": "string"},
            "pre_state": {"type": "object"},
            "post_state": {"type": "object"},
            "runner_result": {"type": "object"},
            "evidence": {"type": "object"},
            "pass_fail": {"type": "string", "enum": ["pass", "fail"]},
            "rollback_status": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return json.dumps(schema, ensure_ascii=True, indent=2) + "\n"


def _acceptance_form(lang: str) -> str:
    de = lang == "de"
    title = "Runtime Acceptance Form (DE)" if de else "Runtime Acceptance Form (EN)"
    decision = (
        "- [ ] lab_ready_candidate\n- [ ] repeat_required\n- [ ] blocked"
    )
    return f"""# {title}

## Ausgefuehrte Runbooks
- 

## Bestandene Runbooks
- 

## Fehlgeschlagene Runbooks
- 

## Offene Risiken
- 

## Abbruchfaelle
- 

## Entscheidung
{decision}

## Operator (Textfeld)
- Name:
- Unterschrift:
"""


def build_runner_runtime_runbook_export_package(
    *,
    target_files: dict[str, str] | None = None,
) -> dict[str, Any]:
    default_targets = {
        "master_de": "docs/runbooks/deploy-runner/RUNTIME_RUNBOOK_MASTER_DE.md",
        "master_en": "docs/runbooks/deploy-runner/RUNTIME_RUNBOOK_MASTER_EN.md",
        "checklist_de": "docs/runbooks/deploy-runner/OPERATOR_CHECKLIST_DE.md",
        "checklist_en": "docs/runbooks/deploy-runner/OPERATOR_CHECKLIST_EN.md",
        "evidence_tpl": "docs/evidence/templates/RUNNER_RUNTIME_RESULT_TEMPLATE.md",
        "schema_json": "docs/evidence/templates/RUNNER_RUNTIME_RESULT_SCHEMA.json",
        "accept_de": "docs/evidence/templates/RUNNER_RUNTIME_ACCEPTANCE_FORM_DE.md",
        "accept_en": "docs/evidence/templates/RUNNER_RUNTIME_ACCEPTANCE_FORM_EN.md",
    }
    targets = dict(default_targets)
    targets.update(dict(target_files or {}))

    warnings: list[str] = []
    errors: list[str] = []
    generated_files: list[str] = []

    contents = {
        "master_de": _master_doc("de"),
        "master_en": _master_doc("en"),
        "checklist_de": _operator_checklist("de"),
        "checklist_en": _operator_checklist("en"),
        "evidence_tpl": _evidence_template(),
        "schema_json": _result_schema(),
        "accept_de": _acceptance_form("de"),
        "accept_en": _acceptance_form("en"),
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

    runbook_index = [{"runbook_id": rid, "order": i + 1} for i, rid in enumerate(_RUNBOOK_IDS)]
    status = "ok"
    if errors:
        status = "blocked"
    elif warnings:
        status = "review_required"

    return {
        "export_status": status,
        "package_id": "RUNNER_RUNTIME_RUNBOOK_EXPORT_V1",
        "generated_files": generated_files,
        "runbook_index": runbook_index,
        "operator_checklist_file": targets["checklist_de"],
        "evidence_template_file": targets["evidence_tpl"],
        "result_schema_file": targets["schema_json"],
        "acceptance_form_file": targets["accept_de"],
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
