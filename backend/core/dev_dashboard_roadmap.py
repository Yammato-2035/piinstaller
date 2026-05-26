"""
Read-only roadmap and next-prompt registry for the development dashboard.

The registry is intentionally documentation-driven:
- it reads JSON and Markdown files from docs/
- it never executes runtime actions
- it can enrich responses with a read-only runtime overlay when a dashboard
  context is passed in from the existing dev-dashboard status builder
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except Exception:  # noqa: BLE001
    Draft202012Validator = None

UTC = timezone.utc

ROADMAP_FILE = "docs/roadmap/setuphelfer_roadmap.json"
ROADMAP_SCHEMA_FILE = "docs/roadmap/setuphelfer_roadmap.schema.json"
MILESTONES_FILE = "docs/roadmap/setuphelfer_milestones.json"
PROMPTS_FILE = "docs/roadmap/setuphelfer_next_prompts.json"
PROMPT_TEMPLATE_FILE = "docs/roadmap/PROMPT_EXPORT_TEMPLATE.md"

ALLOWED_STATUS_VALUES = frozenset(
    {
        "green",
        "partial_green",
        "yellow",
        "red",
        "blocked",
        "deferred",
        "unknown",
        "deprecated",
    }
)
ALLOWED_EVIDENCE_LEVELS = frozenset(
    {
        "none",
        "planning_only",
        "static_analysis",
        "unit_tested",
        "runtime_smoke_tested",
        "hardware_tested",
        "end_to_end_verified",
    }
)
ALLOWED_PROMPT_STATUSES = frozenset(
    {
        "recommended_next",
        "available",
        "blocked",
        "deferred",
        "completed",
        "obsolete",
    }
)
COMMON_FORBIDDEN_ACTIONS = (
    "backup_start",
    "restore_start",
    "rescue_execute",
    "runtime_deploy",
    "backend_restart",
    "package_build",
    "apt_install",
    "apt_upgrade",
    "sudo",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _iso_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _read_json_file(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        if not path.is_file():
            return None, f"missing:{path}"
        raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        if not isinstance(raw, dict):
            return None, f"not_object:{path}"
        return raw, None
    except Exception as exc:  # noqa: BLE001
        return None, f"read_error:{path}:{exc}"


def _read_text_file(path: Path) -> tuple[str | None, str | None]:
    try:
        if not path.is_file():
            return None, f"missing:{path}"
        return path.read_text(encoding="utf-8", errors="replace"), None
    except Exception as exc:  # noqa: BLE001
        return None, f"read_error:{path}:{exc}"


def _as_str_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        text = str(item or "").strip()
        if text:
            out.append(text)
    return out


def _relative(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:  # noqa: BLE001
        return str(path)


def _build_runtime_overlay(dashboard_context: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(dashboard_context, dict):
        return {"available": False, "source": "none"}

    runtime_gate = dashboard_context.get("runtime_gate") or {}
    safe_test_mode = dashboard_context.get("safe_test_mode") or {}
    rescue_board = dashboard_context.get("rescue_stick_board") or {}
    structure_health = dashboard_context.get("structure_health") or {}
    return {
        "available": True,
        "source": "dev_dashboard_status",
        "generated_at": _iso_now(),
        "runtime_gate_status": runtime_gate.get("status"),
        "runtime_gate_passed": runtime_gate.get("passed"),
        "release_gate_status": dashboard_context.get("release_gate_status"),
        "deploy_drift_status": (dashboard_context.get("deploy_drift") or {}).get("status"),
        "safe_test_mode": safe_test_mode.get("mode"),
        "structure_health_status": structure_health.get("status"),
        "br001_offline_status": rescue_board.get("br001_offline_status"),
        "br001_live_status": rescue_board.get("br001_live_status"),
        "release_gate_primary": dashboard_context.get("release_gate_primary"),
    }


def _flatten_blockers(areas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for area in areas:
        for blocker in area.get("blockers") or []:
            if isinstance(blocker, dict):
                rows.append(blocker)
        for milestone in area.get("milestones") or []:
            if not isinstance(milestone, dict):
                continue
            for blocker in milestone.get("blockers") or []:
                if isinstance(blocker, dict):
                    rows.append(blocker)
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        bid = str(row.get("id") or "").strip()
        if bid:
            deduped[bid] = row
    return [deduped[k] for k in sorted(deduped)]


def _flatten_decisions(areas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for area in areas:
        for decision in area.get("decisions") or []:
            if isinstance(decision, dict):
                rows.append(decision)
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        did = str(row.get("id") or "").strip()
        if did:
            deduped[did] = row
    return [deduped[k] for k in sorted(deduped)]


def _flatten_milestones(areas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for area in areas:
        for milestone in area.get("milestones") or []:
            if isinstance(milestone, dict):
                rows.append(milestone)
    return rows


def _count_statuses(areas: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in sorted(ALLOWED_STATUS_VALUES)}
    for area in areas:
        status = str(area.get("status") or "unknown")
        if status in counts:
            counts[status] += 1
    return counts


def _summary_status(counts: dict[str, int]) -> str:
    if counts.get("blocked") or counts.get("red"):
        return "yellow"
    if counts.get("partial_green"):
        return "partial_green"
    if counts.get("green"):
        return "green"
    if counts.get("deferred"):
        return "deferred"
    return "unknown"


def _build_compatibility_tabs(areas: list[dict[str, Any]]) -> dict[str, Any]:
    tabs: dict[str, list[dict[str, Any]]] = {
        "created": [],
        "in_progress": [],
        "planned": [],
        "blocked": [],
    }
    for area in areas:
        status = str(area.get("status") or "unknown")
        if status == "green":
            category = "created"
        elif status in ("partial_green", "yellow"):
            category = "in_progress"
        elif status in ("blocked", "red"):
            category = "blocked"
        else:
            category = "planned"
        tabs[category].append(
            {
                "title": area.get("title_de") or area.get("title_en") or area.get("id"),
                "status": status,
                "category": category,
                "source": ROADMAP_FILE,
                "summary": area.get("description_de") or area.get("description_en") or "",
                "evidence_refs": _as_str_list(area.get("authoritative_evidence")),
                "last_updated": area.get("completed_at"),
                "hints": [str(area.get("next_recommended_action") or "").strip()] if area.get("next_recommended_action") else [],
            }
        )
    return {
        "tabs": tabs,
        "counts": {key: len(value) for key, value in tabs.items()},
        "changed_to_green": {
            "available": False,
            "message": "Keine belastbare Änderungshistorie vorhanden",
            "items": [],
        },
        "green_without_evidence": [
            str(area.get("title_de") or area.get("id"))
            for area in areas
            if str(area.get("status") or "") == "green" and str(area.get("evidence_level") or "none") in ("none", "planning_only")
        ],
        "missing_matrix_entries": [],
    }


def _validate_schema(schema_data: dict[str, Any] | None, roadmap_data: dict[str, Any] | None) -> tuple[bool, list[str]]:
    if not schema_data:
        return False, ["schema_missing"]
    if not roadmap_data:
        return False, ["roadmap_missing"]
    if Draft202012Validator is None:
        return True, []
    try:
        Draft202012Validator(schema_data).validate(roadmap_data)
        return True, []
    except Exception as exc:  # noqa: BLE001
        return False, [f"schema_validate:{exc}"]


def _validate_roadmap_values(
    roadmap_data: dict[str, Any] | None,
    milestones_data: dict[str, Any] | None,
    prompts_data: dict[str, Any] | None,
) -> list[str]:
    errors: list[str] = []
    if not roadmap_data:
        return ["roadmap_missing"]

    areas = roadmap_data.get("areas")
    if not isinstance(areas, list):
        return ["areas_missing"]

    milestone_ids_from_areas: set[str] = set()
    for area in areas:
        if not isinstance(area, dict):
            errors.append("area_not_object")
            continue
        if str(area.get("status") or "unknown") not in ALLOWED_STATUS_VALUES:
            errors.append(f"invalid_area_status:{area.get('id')}")
        if str(area.get("evidence_level") or "none") not in ALLOWED_EVIDENCE_LEVELS:
            errors.append(f"invalid_area_evidence_level:{area.get('id')}")
        for milestone in area.get("milestones") or []:
            if not isinstance(milestone, dict):
                errors.append(f"milestone_not_object:{area.get('id')}")
                continue
            mid = str(milestone.get("id") or "").strip()
            if mid:
                milestone_ids_from_areas.add(mid)
            if str(milestone.get("status") or "unknown") not in ALLOWED_STATUS_VALUES:
                errors.append(f"invalid_milestone_status:{mid or area.get('id')}")
            for task in milestone.get("tasks") or []:
                if not isinstance(task, dict):
                    errors.append(f"task_not_object:{mid or area.get('id')}")
                    continue
                if str(task.get("status") or "unknown") not in ALLOWED_STATUS_VALUES:
                    errors.append(f"invalid_task_status:{task.get('id')}")
        for blocker in area.get("blockers") or []:
            if isinstance(blocker, dict) and str(blocker.get("status") or "unknown") not in ALLOWED_STATUS_VALUES:
                errors.append(f"invalid_blocker_status:{blocker.get('id')}")

    if milestones_data and isinstance(milestones_data.get("milestones"), list):
        flat_ids = {
            str(item.get("id") or "").strip()
            for item in milestones_data.get("milestones") or []
            if isinstance(item, dict) and str(item.get("id") or "").strip()
        }
        if flat_ids != milestone_ids_from_areas:
            errors.append("milestones_flat_mismatch")

    prompts = []
    if prompts_data and isinstance(prompts_data.get("prompts"), list):
        prompts = [p for p in prompts_data.get("prompts") or [] if isinstance(p, dict)]
        rec_count = 0
        for prompt in prompts:
            if str(prompt.get("status") or "available") not in ALLOWED_PROMPT_STATUSES:
                errors.append(f"invalid_prompt_status:{prompt.get('id')}")
            if str(prompt.get("status") or "") == "recommended_next":
                rec_count += 1
        if rec_count > 1:
            errors.append("multiple_recommended_next")
    return errors


def _select_recommended_prompt(prompts: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not prompts:
        return None
    recommended = [prompt for prompt in prompts if str(prompt.get("status") or "") == "recommended_next"]
    if len(recommended) == 1:
        return deepcopy(recommended[0])
    available = [prompt for prompt in prompts if str(prompt.get("status") or "") == "available"]
    if available:
        fallback = deepcopy(available[0])
        fallback["selection_fallback"] = True
        fallback["selection_reason"] = "no_explicit_recommended_next"
        return fallback
    return deepcopy(prompts[0])


def _build_summary(
    areas: list[dict[str, Any]],
    prompts: list[dict[str, Any]],
    recommended_prompt: dict[str, Any] | None,
) -> dict[str, Any]:
    counts = _count_statuses(areas)
    return {
        "overall_status": _summary_status(counts),
        "area_count": len(areas),
        "status_counts": counts,
        "recommended_next_prompt_id": (recommended_prompt or {}).get("id"),
        "recommended_next_prompt_title_de": (recommended_prompt or {}).get("title_de"),
        "prompt_status_counts": {
            status: len([prompt for prompt in prompts if str(prompt.get("status") or "") == status])
            for status in sorted(ALLOWED_PROMPT_STATUSES)
        },
    }


def load_roadmap_registry_bundle(
    repo_root: Path | None = None,
    *,
    dashboard_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    warnings: list[str] = []

    roadmap_path = repo / ROADMAP_FILE
    schema_path = repo / ROADMAP_SCHEMA_FILE
    milestones_path = repo / MILESTONES_FILE
    prompts_path = repo / PROMPTS_FILE

    roadmap_data, roadmap_err = _read_json_file(roadmap_path)
    schema_data, schema_err = _read_json_file(schema_path)
    milestones_data, milestones_err = _read_json_file(milestones_path)
    prompts_data, prompts_err = _read_json_file(prompts_path)

    for err in (roadmap_err, schema_err, milestones_err, prompts_err):
        if err:
            warnings.append(err)

    schema_valid, schema_errors = _validate_schema(schema_data, roadmap_data)
    warnings.extend(schema_errors)
    validation_errors = _validate_roadmap_values(roadmap_data, milestones_data, prompts_data)
    warnings.extend(validation_errors)

    areas = list((roadmap_data or {}).get("areas") or [])
    milestones = list((milestones_data or {}).get("milestones") or _flatten_milestones(areas))
    prompts = [row for row in list((prompts_data or {}).get("prompts") or []) if isinstance(row, dict)]
    blockers = _flatten_blockers(areas)
    decisions = _flatten_decisions(areas)
    recommended_prompt = _select_recommended_prompt(prompts)
    runtime_overlay = _build_runtime_overlay(dashboard_context)
    compatibility = _build_compatibility_tabs(areas)
    summary = _build_summary(areas, prompts, recommended_prompt)

    status = "success"
    if roadmap_data is None or milestones_data is None or prompts_data is None:
        status = "review_required"
    if not schema_valid or validation_errors:
        status = "review_required"

    roadmap_payload: dict[str, Any]
    if roadmap_data:
        roadmap_payload = deepcopy(roadmap_data)
    else:
        roadmap_payload = {
            "schema_version": "1.0",
            "generated_at": _iso_now(),
            "project_version": None,
            "source_commit": None,
            "areas": [],
        }

    roadmap_payload.update(
        {
            "status": status,
            "read_only": True,
            "execution_allowed": False,
            "runtime_overlay": runtime_overlay,
            "summary": summary,
            "recommended_prompt": recommended_prompt,
            "next_prompts": prompts,
            "blockers_flat": blockers,
            "decisions_flat": decisions,
            "milestones_flat": milestones,
            "schema_valid": schema_valid,
            "validation_warnings": warnings,
            **compatibility,
        }
    )

    return {
        "status": status,
        "read_only": True,
        "execution_allowed": False,
        "warnings": warnings,
        "schema_valid": schema_valid,
        "roadmap": roadmap_payload,
        "areas": areas,
        "milestones": milestones,
        "blockers": blockers,
        "decisions": decisions,
        "next_prompts": prompts,
        "recommended_prompt": recommended_prompt,
        "summary": summary,
        "paths": {
            "roadmap": _relative(roadmap_path, repo),
            "schema": _relative(schema_path, repo),
            "milestones": _relative(milestones_path, repo),
            "next_prompts": _relative(prompts_path, repo),
        },
    }


def build_dashboard_roadmap(
    repo_root: Path | None = None,
    *,
    dashboard_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return load_roadmap_registry_bundle(repo_root, dashboard_context=dashboard_context).get("roadmap") or {}


def _render_bullets(values: list[str], *, fallback: str = "- review_required") -> str:
    items = [f"- {value}" for value in values if str(value or "").strip()]
    return "\n".join(items) if items else fallback


def _default_export_template() -> str:
    return """# STRICT MODE – {{TITLE_DE}}

## Ziel
{{REASON_DE}}

## Nicht-Ziele
{{NON_GOALS}}

## Sicherheitsregeln
{{SAFETY_RULES}}

## Phase 0 Runtime-/Repo-Gate
1. `git status --short`
2. `git branch --show-current`
3. `git rev-parse --short HEAD`
4. `./scripts/check-runtime-deploy-gate.sh` falls vorhanden, sonst `./scripts/check-backend-version-gate.sh`
5. `GET /api/version`
6. `GET /api/dev-dashboard/status` falls verfügbar

Wenn das Runtime-Gate fehlschlägt:
- keine Runtime-Tests gegen Port 8000
- keine API-Abnahme behaupten
- Abschlussbericht muss `runtime_gate_blocked_static_or_ui_work_only` enthalten

## Konkrete Aufgaben
{{PROMPT_TEXT}}

## Erlaubte Dateien/Bereiche
{{ALLOWED_PATHS}}

## Verbotene Aktionen
{{FORBIDDEN_ACTIONS}}

## Tests
{{TESTS}}

## Doku / FAQ / i18n
{{DOCUMENTATION_TARGETS}}

## Abschlussbericht
{{EXPECTED_OUTPUTS}}
"""


def export_next_prompt_text(prompt_id: str, repo_root: Path | None = None) -> tuple[str | None, dict[str, Any] | None]:
    repo = repo_root or _repo_root()
    bundle = load_roadmap_registry_bundle(repo)
    prompts = bundle.get("next_prompts") or []
    selected = next((prompt for prompt in prompts if str(prompt.get("id") or "") == str(prompt_id or "").strip()), None)
    if not isinstance(selected, dict):
        return None, {
            "status": "error",
            "error": "prompt_not_found",
            "prompt_id": prompt_id,
            "read_only": True,
            "execution_allowed": False,
        }

    template_path = repo / PROMPT_TEMPLATE_FILE
    template_text, template_err = _read_text_file(template_path)
    if template_err:
        template_text = _default_export_template()

    safety_rules = _as_str_list(selected.get("safety_rules")) + [
        "Kein Backup starten.",
        "Kein Restore starten.",
        "Kein Rescue-/Hardwaretest starten.",
        "Kein Deploy.",
        "Kein Backend-Restart.",
        "Kein Paketbau.",
        "Kein apt install/upgrade.",
        "Kein sudo.",
        "Kein git add -A.",
        "Keine Runtime-Aktion aus der Roadmap heraus ausführen.",
    ]
    forbidden_actions = _as_str_list(selected.get("forbidden_actions")) + list(COMMON_FORBIDDEN_ACTIONS)

    replacements = {
        "{{TITLE_DE}}": str(selected.get("title_de") or selected.get("id") or "Next Prompt"),
        "{{REASON_DE}}": str(selected.get("reason_de") or "review_required"),
        "{{NON_GOALS}}": _render_bullets(_as_str_list(selected.get("non_goals"))),
        "{{SAFETY_RULES}}": _render_bullets(sorted(set(safety_rules))),
        "{{PROMPT_TEXT}}": str(selected.get("prompt_text") or "review_required"),
        "{{ALLOWED_PATHS}}": _render_bullets(_as_str_list(selected.get("allowed_paths"))),
        "{{FORBIDDEN_ACTIONS}}": _render_bullets(sorted(set(forbidden_actions))),
        "{{TESTS}}": _render_bullets(_as_str_list(selected.get("tests"))),
        "{{DOCUMENTATION_TARGETS}}": _render_bullets(_as_str_list(selected.get("documentation_targets"))),
        "{{EXPECTED_OUTPUTS}}": _render_bullets(_as_str_list(selected.get("expected_outputs"))),
    }

    rendered = template_text or _default_export_template()
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)

    return rendered.rstrip() + "\n", None
