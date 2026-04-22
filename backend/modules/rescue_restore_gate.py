"""
Phase 3A: Zugangskontrolle für echten Rescue-Restore (Dry-Run-Pflicht).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from core.rescue_allowlist import RESCUE_DRYRUN_STATE_DIR, normalize_rescue_abs_path

Runner = Callable[..., Any] | None

DRYRUN_GRANT_MAX_AGE_SECONDS = 3600


def _run_capture(
    argv: list[str],
    *,
    runner: Runner = None,
    timeout: int = 30,
) -> Any:
    import subprocess

    run = runner or subprocess.run
    return run(argv, capture_output=True, text=True, timeout=timeout, check=False)


def get_root_block_parent(*, runner: Runner = None) -> str | None:
    """Parent-Blockgerät des laufenden Root-Dateisystems (Whole-Disk), z. B. /dev/sda."""
    r = _run_capture(["findmnt", "-n", "-o", "SOURCE", "-T", "/"], runner=runner, timeout=15)
    line = (r.stdout or "").strip().splitlines()
    if not line:
        return None
    dev = line[0].strip()
    if not dev.startswith("/dev/"):
        return None
    r2 = _run_capture(["lsblk", "-n", "-o", "PKNAME", "-p", dev], runner=runner, timeout=15)
    pk = (r2.stdout or "").strip()
    if r2.returncode == 0 and pk.startswith("/dev/"):
        return pk
    return dev


def is_running_system_disk(target_device: str | None, *, runner: Runner = None) -> bool:
    """True wenn ``target_device`` dieselbe Whole-Disk-Instanz wie das laufende Root ist."""
    if not target_device or not str(target_device).strip():
        return False
    rootp = get_root_block_parent(runner=runner)
    if not rootp:
        return False
    td = str(target_device).strip()
    r3 = _run_capture(["lsblk", "-n", "-o", "PKNAME", "-p", td], runner=runner, timeout=15)
    tparent = (r3.stdout or "").strip() if r3.returncode == 0 and (r3.stdout or "").strip().startswith("/dev/") else td
    try:
        return normalize_rescue_abs_path(tparent) == normalize_rescue_abs_path(rootp) or normalize_rescue_abs_path(
            td
        ) == normalize_rescue_abs_path(rootp)
    except ValueError:
        return False


def _state_path(token: str) -> Path:
    return Path(RESCUE_DRYRUN_STATE_DIR) / f"{token}.json"


def load_dry_run_grant(token: str) -> dict[str, Any] | None:
    """Lädt gespeicherten Dry-Run-Grant oder None."""
    t = (token or "").strip()
    if not t or "/" in t or ".." in t:
        return None
    p = _state_path(t)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def persist_dry_run_grant(token: str, payload: dict[str, Any]) -> Path:
    """Schreibt Grant-Datei unter ``/tmp/setuphelfer-rescue-dryrun-state``."""
    RESCUE_DRYRUN_STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = _state_path(token)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def consume_dry_run_grant(token: str) -> None:
    try:
        _state_path(token).unlink(missing_ok=True)
    except OSError:
        pass


def validate_restore_preconditions(
    *,
    dry_run_token: str,
    backup_file: str,
    target_device: str | None,
    confirmation: bool,
    risk_acknowledged: bool,
    session_id: str | None,
) -> tuple[bool, str, dict[str, Any]]:
    """
    Rückgabe: (ok, code, state_dict).

    Zusätzliche Codes: ``rescue.restore.session_*``, ``rescue.restore.dryrun_missing``,
    ``rescue.restore.confirmation_missing``, ``rescue.restore.risk_ack_missing``.
    """
    if not confirmation:
        return False, "rescue.restore.confirmation_missing", {}
    state = load_dry_run_grant(dry_run_token)
    if not state:
        return False, "rescue.restore.dryrun_missing", {}

    try:
        created = datetime.fromisoformat(str(state.get("created_at", "")).replace("Z", "+00:00"))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - created).total_seconds()
    except Exception:
        return False, "rescue.restore.session_invalid", {}

    if age > DRYRUN_GRANT_MAX_AGE_SECONDS:
        return False, "rescue.restore.session_stale", {}

    sid_grant = str(state.get("session_id") or "").strip()
    sid_req = (session_id or "").strip()
    if not sid_grant:
        return False, "rescue.restore.session_invalid", {}
    if not sid_req:
        return False, "rescue.restore.session_missing", {}
    if sid_req != sid_grant:
        return False, "rescue.restore.session_invalid", {}

    if not state.get("allow_restore"):
        return False, "rescue.restore.RESTORE_BLOCKED_NO_DRYRUN", {}

    if str(state.get("dryrun_mode") or "") != "dryrun":
        return False, "rescue.restore.RESTORE_BLOCKED_NO_DRYRUN", {}

    if str(state.get("dryrun_simulation_status") or "") != "DRYRUN_OK":
        return False, "rescue.restore.RESTORE_BLOCKED_INVALID_STATE", {}

    dec = str(state.get("restore_decision") or "")
    if dec not in ("proceed_possible", "proceed_with_explicit_risk_ack"):
        return False, "rescue.restore.RESTORE_BLOCKED_RED_RISK", {}

    risk = str(state.get("restore_risk_level") or "")
    if risk == "red":
        return False, "rescue.restore.RESTORE_BLOCKED_RED_RISK", {}

    if risk == "yellow" and not risk_acknowledged:
        return False, "rescue.restore.risk_ack_missing", {}

    try:
        bf_state = normalize_rescue_abs_path(str(state.get("backup_file") or ""))
        bf_req = normalize_rescue_abs_path(backup_file)
    except ValueError:
        return False, "rescue.restore.RESTORE_BLOCKED_INVALID_STATE", {}

    if bf_state != bf_req:
        return False, "rescue.restore.RESTORE_BLOCKED_INVALID_STATE", {}

    td_state = (state.get("target_device") or None) or None
    td_req = (target_device or None) or None
    if (td_state or "") != (td_req or ""):
        return False, "rescue.restore.RESTORE_BLOCKED_INVALID_STATE", {}

    return True, "rescue.restore.RESTORE_GATE_OK", state


def validate_target_confirmation_phrase(target_device: str | None, phrase: str) -> bool:
    """Nutzer muss den Basisnamen des Ziel-Blockgeräts exakt eingeben (falls gesetzt)."""
    p = (phrase or "").strip()
    if not target_device or not str(target_device).strip():
        return p == "RESTORE_NO_BLOCK_DEVICE"
    return p == Path(str(target_device).strip()).name


__all__ = [
    "DRYRUN_GRANT_MAX_AGE_SECONDS",
    "consume_dry_run_grant",
    "get_root_block_parent",
    "is_running_system_disk",
    "load_dry_run_grant",
    "persist_dry_run_grant",
    "validate_restore_preconditions",
    "validate_target_confirmation_phrase",
]
