"""
Read-only loader for manual operator/Cursor command-run evidence (JSON files).

No shell execution. No writes from API.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MANUAL_RUNS_REL_DIR = Path("docs/evidence/dev-dashboard/manual_command_runs")
SCHEMA_FILENAME = "manual_command_run.schema.json"
EXAMPLE_FILENAME = "example_manual_command_run.json"
README_FILENAME = "README.md"

_VALID_SAFETY = frozenset({"read_only", "operator_action", "forbidden"})
_VALID_SUMMARY_STATUS = frozenset({"ok", "yellow", "blocked"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _runs_dir(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / MANUAL_RUNS_REL_DIR


def _iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw)
        if isinstance(data, dict):
            return data, None
        return None, f"not_object:{path.name}"
    except OSError as exc:
        return None, f"read_error:{path.name}:{exc}"
    except json.JSONDecodeError as exc:
        return None, f"json_error:{path.name}:{exc}"


def _normalize_run(data: dict[str, Any], *, source_file: str) -> dict[str, Any]:
    commands = data.get("commands") if isinstance(data.get("commands"), list) else []
    normalized_commands: list[dict[str, Any]] = []
    has_forbidden = False
    excerpt_only = False

    for row in commands:
        if not isinstance(row, dict):
            continue
        safety = str(row.get("safety_class") or "read_only").strip().lower()
        if safety not in _VALID_SAFETY:
            safety = "read_only"
        if safety == "forbidden":
            has_forbidden = True
        stdout_ex = str(row.get("stdout_excerpt") or "").strip()
        full_log = str(row.get("full_log_path") or "").strip()
        if stdout_ex and not full_log:
            excerpt_only = True
        notes = str(row.get("notes") or "")
        if "ausschnitt" in notes.lower() or "excerpt" in notes.lower():
            excerpt_only = True
        normalized_commands.append(
            {
                "command": str(row.get("command") or ""),
                "purpose": str(row.get("purpose") or ""),
                "started_at": row.get("started_at"),
                "completed_at": row.get("completed_at"),
                "exit_code": row.get("exit_code"),
                "stdout_excerpt": stdout_ex[:2000] if stdout_ex else "",
                "stderr_excerpt": str(row.get("stderr_excerpt") or "")[:2000],
                "full_log_path": full_log or None,
                "safety_class": safety,
                "notes": notes,
                "excerpt_only": bool(stdout_ex and not full_log),
            }
        )

    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    sum_status = str(summary.get("status") or "yellow").strip().lower()
    if sum_status not in _VALID_SUMMARY_STATUS:
        sum_status = "yellow"
    if has_forbidden and sum_status == "ok":
        sum_status = "blocked"

    return {
        "run_id": str(data.get("run_id") or source_file),
        "created_at": str(data.get("created_at") or ""),
        "operator": str(data.get("operator") or ""),
        "branch": str(data.get("branch") or ""),
        "head": str(data.get("head") or ""),
        "phase0_gate": data.get("phase0_gate") if isinstance(data.get("phase0_gate"), dict) else {},
        "commands": normalized_commands,
        "artifacts": data.get("artifacts") if isinstance(data.get("artifacts"), list) else [],
        "tests": data.get("tests") if isinstance(data.get("tests"), list) else [],
        "not_executed": data.get("not_executed") if isinstance(data.get("not_executed"), list) else [],
        "summary": {
            "status": sum_status,
            "reason": str(summary.get("reason") or ""),
        },
        "source_file": source_file,
        "excerpt_only_warning": excerpt_only,
        "has_forbidden_commands": has_forbidden,
        "read_only": True,
        "execution_allowed": False,
    }


def build_manual_command_runs_index(
    repo_root: Path | None = None,
    *,
    max_runs: int = 40,
) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    base = _runs_dir(repo)
    warnings: list[str] = []
    runs: list[dict[str, Any]] = []

    if not base.is_dir():
        warnings.append("manual_command_runs_dir_missing")
        return {
            "status": "success",
            "read_only": True,
            "execution_allowed": False,
            "generated_at": _iso_now(),
            "runs_dir": str(MANUAL_RUNS_REL_DIR).replace("\\", "/"),
            "runs": [],
            "warnings": warnings,
            "schema_path": str((MANUAL_RUNS_REL_DIR / SCHEMA_FILENAME)).replace("\\", "/"),
        }

    skip_names = {SCHEMA_FILENAME, EXAMPLE_FILENAME, README_FILENAME}
    for path in sorted(base.glob("*.json"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True):
        if path.name in skip_names or path.name.startswith("."):
            continue
        rel = str(path.relative_to(repo)).replace("\\", "/")
        data, err = _read_json(path)
        if err:
            warnings.append(err)
            continue
        if not data:
            continue
        try:
            runs.append(_normalize_run(data, source_file=rel))
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"normalize_error:{path.name}:{exc}")

    runs.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    runs = runs[:max_runs]

    any_excerpt = any(r.get("excerpt_only_warning") for r in runs)
    any_forbidden = any(r.get("has_forbidden_commands") for r in runs)
    overall = "ok"
    if any_forbidden:
        overall = "blocked"
    elif any_excerpt or warnings:
        overall = "yellow"

    return {
        "status": "success",
        "read_only": True,
        "execution_allowed": False,
        "generated_at": _iso_now(),
        "runs_dir": str(MANUAL_RUNS_REL_DIR).replace("\\", "/"),
        "runs": runs,
        "run_count": len(runs),
        "warnings": warnings,
        "schema_path": str((MANUAL_RUNS_REL_DIR / SCHEMA_FILENAME)).replace("\\", "/"),
        "overall_status": overall,
        "excerpt_only_detected": any_excerpt,
        "forbidden_commands_detected": any_forbidden,
    }
