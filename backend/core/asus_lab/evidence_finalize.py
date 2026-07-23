"""Finalize ASUS lab evidence run (honest statuses only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from core.asus_lab.run_context import utc_now

SCHEMA_VERSION = 1


def finalize_run(
    run_root: Path,
    *,
    status: str,
    extras: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    allowed = {
        "capture_finalized",
        "insufficient_evidence",
        "evidence_collected",
        "partial",
        "blocked",
        "failed",
    }
    if status not in allowed:
        raise ValueError("invalid_finalize_status")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "finalized_at": utc_now(),
        "definitive_freeze_root_cause_known": False,
        "bitlocker_mutation": False,
        **dict(extras or {}),
    }
    out = Path(run_root) / "result" / "finalize.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
