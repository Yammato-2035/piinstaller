"""MSI evidence completion marker for physical E2E gate (001D5)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MSI_EVIDENCE_COMPLETE_REL = Path("setuphelfer/evidence/msi-rs011b/msi-evidence-complete.json")
MSI_EVIDENCE_COMPLETE_SCHEMA = "setuphelfer.rescue.msi-evidence-complete.v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def msi_evidence_complete_path(setup_logs_base: Path) -> Path:
    return setup_logs_base / MSI_EVIDENCE_COMPLETE_REL


def write_msi_evidence_complete(
    setup_logs_base: Path,
    *,
    status: str = "passed",
    session_id: str = "",
    payload_version: str = "",
    late_gate_completed: bool = True,
    tui_owned: bool = True,
    evidence_synced: bool = True,
) -> Path:
    path = msi_evidence_complete_path(setup_logs_base)
    if not setup_logs_base.is_dir():
        raise OSError("failed_setup_logs_not_writable")
    test = setup_logs_base / ".setup-logs-write-test.tmp"
    try:
        test.write_text("ok\n", encoding="utf-8")
        test.unlink(missing_ok=True)
    except OSError as exc:
        raise OSError("failed_setup_logs_not_writable") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": MSI_EVIDENCE_COMPLETE_SCHEMA,
        "status": status,
        "session_id": session_id,
        "payload_version": payload_version,
        "late_gate_completed": late_gate_completed,
        "tui_owned": tui_owned,
        "evidence_synced": evidence_synced,
        "completed_at": _utc_now(),
        "recorded_at": _utc_now(),
    }
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with tmp.open("rb") as handle:
        os.fsync(handle.fileno())
    tmp.replace(path)
    try:
        fd = os.open(str(path.parent), os.O_DIRECTORY)
        os.fsync(fd)
        os.close(fd)
    except OSError:
        pass
    return path


def read_msi_evidence_complete(setup_logs_base: Path) -> dict[str, Any] | None:
    path = msi_evidence_complete_path(setup_logs_base)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def msi_evidence_complete_ok(setup_logs_base: Path) -> bool:
    data = read_msi_evidence_complete(setup_logs_base)
    if not data:
        return False
    return (
        data.get("status") == "passed"
        and bool(data.get("late_gate_completed"))
        and bool(data.get("tui_owned"))
        and bool(data.get("evidence_synced"))
    )
