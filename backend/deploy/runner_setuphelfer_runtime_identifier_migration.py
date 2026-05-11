from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_PLAN_REL = "docs/evidence/runtime-results/handoff/setuphelfer_runtime_identifier_migration_plan.json"
_ALIAS_REL = "docs/evidence/runtime-results/handoff/compatibility_aliases.json"
_WORKSPACE_REL = "docs/evidence/runtime-results/handoff/setuphelfer_workspace_migration_plan.json"
_MAX_OUTPUT_BYTES = 512 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "SETUPHELFER_RUNTIME_IDENTIFIER_MIGRATION_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, "SETUPHELFER_RUNTIME_IDENTIFIER_MIGRATION_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "SETUPHELFER_RUNTIME_IDENTIFIER_MIGRATION_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "SETUPHELFER_RUNTIME_IDENTIFIER_MIGRATION_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _write_json(rel_path: str, payload: dict[str, Any], explicit_overwrite: bool) -> str | None:
    out_path, err = _resolve_handoff(rel_path)
    if err or out_path is None:
        return err or "SETUPHELFER_RUNTIME_IDENTIFIER_MIGRATION_OUTPUT_PATH_INVALID"
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return "SETUPHELFER_RUNTIME_IDENTIFIER_MIGRATION_EXISTS_NO_OVERWRITE"
    text = json.dumps(payload, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return "SETUPHELFER_RUNTIME_IDENTIFIER_MIGRATION_OUTPUT_TOO_LARGE"
    try:
        _atomic_write(out_path, text)
    except OSError:
        return "SETUPHELFER_RUNTIME_IDENTIFIER_MIGRATION_WRITE_FAILED"
    return None


def build_runtime_identifier_migration_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    plan = {
        "migration_schema_version": 1,
        "strict_mode": "setuphelfer_runtime_identifier_migration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "migration_status": "ok",
        "apply_runtime_changes": False,
        "env_mappings": [
            {"from_prefix": "PI_INSTALLER_", "to_prefix": "SETUPHELFER_", "mode": "compat_read_only_alias"}
        ],
        "service_mappings": [{"from": "pi-installer.service", "to": "setuphelfer.service", "mode": "prepare_only"}],
        "path_mappings": [
            {"from": "/opt/pi-installer", "to": "/opt/setuphelfer", "mode": "prepare_only"},
            {"from": "~/.local/share/de.pi-installer.app", "to": "~/.local/share/de.setuphelfer.app", "mode": "prepare_only"},
        ],
        "desktop_mappings": [{"from": "pi-installer.desktop", "to": "setuphelfer.desktop", "mode": "prepare_only"}],
        "tauri_mappings": [{"from": "de.pi-installer.app", "to": "de.setuphelfer.app", "mode": "prepare_only"}],
    }
    aliases = {
        "aliases_schema_version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "aliases": [
            {
                "legacy_identifier": "PI_INSTALLER_*",
                "replacement_identifier": "SETUPHELFER_*",
                "state": "deprecated",
                "mode": "read_only_compatibility",
                "allow_new_writes": False,
                "warning_code": "DEPRECATED_RUNTIME_IDENTIFIER",
            },
            {
                "legacy_identifier": "de.pi-installer.app",
                "replacement_identifier": "de.setuphelfer.app",
                "state": "deprecated",
                "mode": "read_only_compatibility",
                "allow_new_writes": False,
                "warning_code": "DEPRECATED_RUNTIME_IDENTIFIER",
            },
        ],
    }
    workspace_plan = {
        "plan_schema_version": 1,
        "strict_mode": "setuphelfer_workspace_service_prep",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "execution_mode": "prepare_only",
        "workspace_rename_plan": ["pi-installer -> setuphelfer naming in active runtime files only"],
        "service_rename_plan": ["pi-installer.service -> setuphelfer.service (manual rollout)"],
        "desktop_migration_plan": ["pi-installer.desktop -> setuphelfer.desktop (manual switch)"],
        "config_migration_plan": ["PI_INSTALLER_* env -> SETUPHELFER_* env (compatibility aliases remain read-only)"],
        "localstorage_migration_plan": [
            "~/.local/share/de.pi-installer.app -> ~/.local/share/de.setuphelfer.app (one-way migration, no auto-delete)"
        ],
    }
    errors: list[str] = []
    for rel, payload in ((_PLAN_REL, plan), (_ALIAS_REL, aliases), (_WORKSPACE_REL, workspace_plan)):
        err = _write_json(rel, payload, explicit_overwrite)
        if err:
            errors.append(err)
    if errors:
        return {
            "migration_status": "blocked",
            "migration_file_path": _PLAN_REL,
            "compatibility_aliases_file_path": _ALIAS_REL,
            "workspace_migration_plan_file_path": _WORKSPACE_REL,
            "migration_plan": {},
            "warnings": [],
            "errors": list(dict.fromkeys(errors)),
            "blocked_reasons": list(dict.fromkeys(errors)),
        }
    return {
        "migration_status": "ok",
        "migration_file_path": _PLAN_REL,
        "compatibility_aliases_file_path": _ALIAS_REL,
        "workspace_migration_plan_file_path": _WORKSPACE_REL,
        "migration_plan": plan,
        "warnings": [],
        "errors": [],
        "blocked_reasons": [],
    }
