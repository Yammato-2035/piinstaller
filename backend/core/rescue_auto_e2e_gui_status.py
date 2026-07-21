"""GUI-facing auto physical E2E status (PI-RS-MSI-GUI-AUTO-BVR-001)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.rescue_physical_e2e_auto_e2e_state import (
    PHASE_LABELS_DE,
    read_auto_e2e_state,
)


def _cmdline() -> str:
    try:
        return Path("/proc/cmdline").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def msi_e2e_auto_active(cmdline: str | None = None) -> bool:
    text = cmdline if cmdline is not None else _cmdline()
    return "setuphelfer_msi_e2e_auto=1" in text.split()


def build_auto_e2e_gui_status(*, cmdline: str | None = None) -> dict[str, Any]:
    """Return a JSON-serializable status payload for the rescue GUI progress page."""
    cmd = cmdline if cmdline is not None else _cmdline()
    active = msi_e2e_auto_active(cmd)
    state = read_auto_e2e_state() or {}
    phase = str(state.get("phase") or "")
    status = str(state.get("status") or ("waiting" if active else "idle"))
    run_id = str(state.get("run_id") or "")
    progress = str(state.get("last_progress") or "")
    label = PHASE_LABELS_DE.get(phase, phase or ("Automatischer Lab-Lauf" if active else "Kein Auto-E2E"))
    return {
        "schema": "setuphelfer.rescue.auto-e2e-gui-status.v1",
        "active": active,
        "mode": str(state.get("mode") or ("auto_physical_e2e" if active else "idle")),
        "run_id": run_id,
        "phase": phase,
        "phase_label_de": label,
        "status": status,
        "last_progress": progress,
        "updated_at": state.get("updated_at"),
        "gui_mode": "setuphelfer_mode=gui" in cmd.split(),
    }
