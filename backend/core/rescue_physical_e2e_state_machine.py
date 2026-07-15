"""Persistent state machine for unattended physical E2E (001D4)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_physical_e2e_journal import append_jsonl, read_json, write_json

E2E_STATES: tuple[str, ...] = (
    "initialized",
    "boot_verified",
    "machine_identity_verified",
    "setup_logs_ready",
    "network_waiting",
    "network_ready",
    "test_target_discovered",
    "test_target_verified",
    "test_data_creating",
    "test_data_ready",
    "backup_running",
    "backup_completed",
    "verify_running",
    "verify_completed",
    "restore_running",
    "restore_completed",
    "manifest_comparison_running",
    "manifest_comparison_completed",
    "telemetry_sending",
    "telemetry_receipts_complete",
    "diagnostics_waiting",
    "diagnostics_complete",
    "evidence_syncing",
    "evidence_complete",
    "shutdown_requested",
    "passed",
    "failed",
    "blocked",
)

DANGEROUS_FORWARD: dict[str, frozenset[str]] = {
    "backup_running": frozenset({"backup_completed", "failed", "blocked", "passed", "shutdown_requested"}),
    "verify_running": frozenset({"verify_completed", "failed", "blocked", "passed", "shutdown_requested"}),
    "restore_running": frozenset({"restore_completed", "failed", "blocked", "passed", "shutdown_requested"}),
    "manifest_comparison_running": frozenset(
        {"manifest_comparison_completed", "failed", "blocked", "passed", "shutdown_requested"}
    ),
}

TERMINAL_STATES = frozenset({"passed", "failed", "blocked", "shutdown_requested"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class PhysicalE2EStateMachine:
    def __init__(self, journal_dir: Path, *, e2e_run_id: str, correlation_id: str) -> None:
        self.journal_dir = journal_dir
        self.state_path = journal_dir / "state.json"
        self.journal_path = journal_dir / "journal.jsonl"
        self.e2e_run_id = e2e_run_id
        self.correlation_id = correlation_id
        journal_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        data = read_json(self.state_path)
        if not data:
            data = {
                "e2e_run_id": self.e2e_run_id,
                "correlation_id": self.correlation_id,
                "state": "initialized",
                "updated_at": _utc_now(),
            }
            self._atomic_write(data)
        return data

    def _atomic_write(self, data: dict[str, Any]) -> None:
        data["updated_at"] = _utc_now()
        tmp = self.state_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        with tmp.open("rb") as handle:
            os.fsync(handle.fileno())
        tmp.replace(self.state_path)
        try:
            fd = os.open(str(self.journal_dir), os.O_DIRECTORY)
            os.fsync(fd)
            os.close(fd)
        except OSError:
            pass

    def transition(self, new_state: str, *, detail: dict[str, Any] | None = None) -> dict[str, Any]:
        if new_state not in E2E_STATES:
            raise ValueError(f"invalid_state:{new_state}")
        current = self.load()
        prev = str(current.get("state") or "initialized")
        if prev in DANGEROUS_FORWARD and new_state not in TERMINAL_STATES:
            allowed = DANGEROUS_FORWARD.get(prev, frozenset())
            if new_state not in allowed:
                raise ValueError(f"unsafe_resume_from:{prev}")
        current["state"] = new_state
        current["previous_state"] = prev
        if detail:
            current.setdefault("details", {}).update(detail)
        self._atomic_write(current)
        append_jsonl(
            self.journal_path,
            {
                "e2e_run_id": self.e2e_run_id,
                "correlation_id": self.correlation_id,
                "from_state": prev,
                "to_state": new_state,
                "detail": detail or {},
            },
        )
        return current

    def can_shutdown(self) -> bool:
        state = str(self.load().get("state") or "")
        return state in TERMINAL_STATES or state == "evidence_complete"
