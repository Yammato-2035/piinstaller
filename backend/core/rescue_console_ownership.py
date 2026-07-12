"""PI-RS-MSI-GUI-003 — tty1 console ownership model for rescue boot."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONSOLE_OWNERSHIP_SCHEMA_VERSION = 1
AUDIT_WRITE_BLOCKED = "RESCUE_CONSOLE_WRITE_BLOCKED_TUI_OWNED"

_VALID_OWNERS = frozenset({"none", "boot_progress", "tui", "gui"})
_VALID_STATES = frozenset(
    {
        "boot_progress",
        "tui_initializing",
        "tui_owned",
        "gui_transition",
        "gui_owned",
        "shutdown",
    }
)

_DEFAULT_STATE_PATH = Path("/run/setuphelfer/console-ownership.json")
_DEFAULT_SHIELD_PATH = Path("/run/setuphelfer/console-shield.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_console_ownership_path() -> Path:
    return _DEFAULT_STATE_PATH


def default_console_shield_path() -> Path:
    return _DEFAULT_SHIELD_PATH


def build_console_ownership_state(
    *,
    owner: str = "boot_progress",
    lifecycle_state: str = "boot_progress",
    session_id: str = "",
    boot_id: str = "",
) -> dict[str, Any]:
    if owner not in _VALID_OWNERS:
        raise ValueError(f"invalid_console_owner:{owner}")
    if lifecycle_state not in _VALID_STATES:
        raise ValueError(f"invalid_lifecycle_state:{lifecycle_state}")
    tui_owned = lifecycle_state in {"tui_initializing", "tui_owned"}
    return {
        "schema_version": CONSOLE_OWNERSHIP_SCHEMA_VERSION,
        "tty": "tty1",
        "owner": owner,
        "lifecycle_state": lifecycle_state,
        "write_allowed_for": ["tui"] if tui_owned else (["boot_progress"] if owner == "boot_progress" else []),
        "clear_allowed_for": ["tui"] if tui_owned else (["boot_progress"] if owner == "boot_progress" else []),
        "boot_progress_write_allowed": not tui_owned and owner == "boot_progress",
        "boot_progress_clear_allowed": not tui_owned and owner == "boot_progress",
        "gui_write_allowed": False if tui_owned else owner == "gui",
        "gui_transition_allowed": not tui_owned,
        "reason": "tui_owned" if tui_owned else owner,
        "session_id": session_id,
        "boot_id": boot_id,
        "updated_at": _utc_now(),
    }


def build_console_shield_state(
    *,
    reason: str,
    owner_state: dict[str, Any],
    enabled: bool = True,
    journal_blocked: bool = True,
) -> dict[str, Any]:
    owner = str(owner_state.get("owner") or "boot_progress")
    lifecycle = str(owner_state.get("lifecycle_state") or "boot_progress")
    tui_owned = lifecycle in {"tui_initializing", "tui_owned"}
    return {
        "schema_version": 2,
        "enabled": enabled,
        "reason": reason,
        "tty": "tty1",
        "owner": owner,
        "lifecycle_state": lifecycle,
        "tty1_write_allowed": bool(owner_state.get("boot_progress_write_allowed")) and not tui_owned,
        "tty1_clear_allowed": bool(owner_state.get("boot_progress_clear_allowed")) and not tui_owned,
        "boot_progress_write_allowed": bool(owner_state.get("boot_progress_write_allowed")),
        "boot_progress_clear_allowed": bool(owner_state.get("boot_progress_clear_allowed")),
        "gui_write_allowed": bool(owner_state.get("gui_write_allowed")),
        "gui_transition_allowed": bool(owner_state.get("gui_transition_allowed")),
        "write_allowed_for": list(owner_state.get("write_allowed_for") or []),
        "clear_allowed_for": list(owner_state.get("clear_allowed_for") or []),
        "owner_since": owner_state.get("updated_at"),
        "session_id": owner_state.get("session_id") or "",
        "journal_to_console_blocked": journal_blocked,
        "production_ready": False,
    }


def load_console_ownership(path: Path | None = None) -> dict[str, Any]:
    target = path or default_console_ownership_path()
    if not target.is_file():
        return build_console_ownership_state()
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("invalid_console_ownership_state")
    return data


def save_console_ownership(state: dict[str, Any], path: Path | None = None) -> Path:
    target = path or default_console_ownership_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target


def transition_console_owner(
    lifecycle_state: str,
    *,
    session_id: str = "",
    boot_id: str = "",
    path: Path | None = None,
    shield_path: Path | None = None,
    shield_reason: str = "",
) -> dict[str, Any]:
    owner_map = {
        "boot_progress": "boot_progress",
        "tui_initializing": "tui",
        "tui_owned": "tui",
        "gui_transition": "gui",
        "gui_owned": "gui",
        "shutdown": "none",
    }
    owner = owner_map.get(lifecycle_state, "boot_progress")
    state = build_console_ownership_state(
        owner=owner,
        lifecycle_state=lifecycle_state,
        session_id=session_id,
        boot_id=boot_id,
    )
    save_console_ownership(state, path)
    shield = build_console_shield_state(
        reason=shield_reason or lifecycle_state,
        owner_state=state,
    )
    shield_target = shield_path or default_console_shield_path()
    shield_target.parent.mkdir(parents=True, exist_ok=True)
    shield_target.write_text(json.dumps(shield, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return state


def boot_progress_tty_write_allowed(state: dict[str, Any] | None = None, path: Path | None = None) -> bool:
    current = state or load_console_ownership(path)
    return bool(current.get("boot_progress_write_allowed"))


def boot_progress_tty_clear_allowed(state: dict[str, Any] | None = None, path: Path | None = None) -> bool:
    current = state or load_console_ownership(path)
    return bool(current.get("boot_progress_clear_allowed"))


def evaluate_tty_write_attempt(
    *,
    writer: str = "boot_progress",
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    current = state or load_console_ownership()
    allowed = writer == "boot_progress" and bool(current.get("boot_progress_write_allowed"))
    if writer == "tui":
        allowed = current.get("owner") == "tui"
    audit_code = None if allowed else AUDIT_WRITE_BLOCKED
    return {
        "allowed": allowed,
        "audit_code": audit_code,
        "owner": current.get("owner"),
        "lifecycle_state": current.get("lifecycle_state"),
    }
