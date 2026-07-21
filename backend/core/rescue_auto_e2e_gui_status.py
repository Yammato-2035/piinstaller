"""GUI-facing auto physical E2E status (PI-RS-MSI-GUI-AUTO-BVR-001 / VT-PROGRESS-002)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.rescue_canonical_bvr_progress import (
    gui_status_from_canonical,
    normalize_phase,
    read_progress_for_display,
)
from core.rescue_physical_e2e_auto_e2e_state import PHASE_LABELS_DE, read_auto_e2e_state


def _cmdline() -> str:
    try:
        return Path("/proc/cmdline").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def msi_e2e_auto_active(cmdline: str | None = None) -> bool:
    text = cmdline if cmdline is not None else _cmdline()
    return "setuphelfer_msi_e2e_auto=1" in text.split()


def build_auto_e2e_gui_status(*, cmdline: str | None = None) -> dict[str, Any]:
    """Return JSON status for the rescue GUI progress page from canonical progress."""
    cmd = cmdline if cmdline is not None else _cmdline()
    active = msi_e2e_auto_active(cmd)
    progress = read_progress_for_display()
    has_canonical = int(progress.get("sequence") or 0) > 0 or bool(
        progress.get("source_component") not in {None, "canonical", ""}
        and progress.get("phase") not in {None, "startup"}
    )
    # Fresh empty canonical → fall back to orchestration state for unit/compat.
    if int(progress.get("sequence") or 0) == 0 and progress.get("phase") == "startup":
        state = read_auto_e2e_state() or {}
        if state:
            phase = str(state.get("phase") or "")
            status = str(state.get("status") or ("waiting" if active else "idle"))
            run_id = str(state.get("run_id") or "")
            progress_msg = str(state.get("last_progress") or "")
            label = PHASE_LABELS_DE.get(phase, phase or ("Automatischer Lab-Lauf" if active else "Kein Auto-E2E"))
            return {
                "schema": "setuphelfer.rescue.auto-e2e-gui-status.v1",
                "active": active,
                "mode": str(state.get("mode") or ("auto_physical_e2e" if active else "idle")),
                "run_id": run_id,
                "phase": phase,
                "phase_label_de": label,
                "phase_label": label,
                "status": status,
                "last_progress": progress_msg,
                "updated_at": state.get("updated_at"),
                "gui_mode": "setuphelfer_mode=gui" in cmd.split(),
                "canonical": False,
                "source_component": "auto-e2e-state-compat",
            }

    payload = gui_status_from_canonical(progress)
    payload["active"] = active
    payload["mode"] = "auto_physical_e2e" if active else "idle"
    payload["gui_mode"] = "setuphelfer_mode=gui" in cmd.split()
    # Prefer localized label from message when present.
    if payload.get("last_progress"):
        payload["phase_label_de"] = str(payload["last_progress"])
        payload["phase_label"] = str(payload["last_progress"])
    if not active and not progress.get("sequence"):
        payload["status"] = "idle"
        payload["phase"] = ""
        payload["phase_label"] = "Kein Auto-E2E"
        payload["phase_label_de"] = "Kein Auto-E2E"
    # Keep legacy phase name aliases visible when message contains them.
    if normalize_phase(str(payload.get("phase") or "")) == "backup" and "Backup" in str(
        payload.get("phase_label_de") or ""
    ):
        pass
    _ = has_canonical
    return payload
