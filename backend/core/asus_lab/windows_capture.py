"""Windows live-capture readiness + finalize helpers for ASUS lab."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.asus_lab.run_context import utc_now, validate_run_id
from core.rescue_win11_live_capture import (
    ensure_run_tree,
    finalize_capture_status,
    resolve_setup_logs_roots,
)

SCHEMA_VERSION = 1


def prepare_windows_live_capture(
    *,
    setup_logs_candidates: list[Path],
    run_id: str,
) -> dict[str, Any]:
    gate = validate_run_id(run_id)
    if not gate["ok"]:
        return {"ok": False, "blocked_reason": gate["blocked_reason"], "run_id": run_id}
    roots = resolve_setup_logs_roots(setup_logs_candidates)
    if not roots.get("setup_capture_ready"):
        return {
            "ok": False,
            "blocked_reason": "setup_logs_not_writable",
            "run_id": run_id,
            "setup_logs": roots,
        }
    selected = Path(str(roots["selected"]["path"]))
    run_root = selected / "asus-win11" / run_id
    layout = ensure_run_tree(run_root)
    marker = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "prepared_at": utc_now(),
        "setup_capture_ready": True,
        "run_root": str(run_root),
        "layout": layout,
        "auto_import_pending": True,
        "bitlocker_mutation": False,
    }
    (run_root / "collector" / "prepare.json").write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")
    (run_root / "AUTO_IMPORT.READY").write_text(f"{run_id}\n", encoding="utf-8")
    return {"ok": True, **marker, "setup_logs": roots}


def finalize_windows_live_capture(
    *,
    run_id: str,
    panther_files: int,
    rollback_files: int,
    heartbeats: int,
    stall_suspected: bool = False,
) -> dict[str, Any]:
    fin = finalize_capture_status(
        run_id=run_id,
        panther_files=panther_files,
        rollback_files=rollback_files,
        heartbeats=heartbeats,
    )
    fin["setup_stall_suspected"] = bool(stall_suspected)
    fin["definitive_freeze_root_cause_known"] = False
    return fin
