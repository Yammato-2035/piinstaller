"""Central rescue run-mode evaluation (001D7B)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.rescue_discovery_run_control import load_discovery_run_control
from core.rescue_physical_e2e_evidence_import import find_setup_logs_mount
from core.rescue_physical_e2e_run_control import load_run_control

RUN_MODES = (
    "interactive",
    "auto_discovery_only",
    "auto_physical_e2e",
    "manual_physical_e2e",
)

BLOCKED_RUN_MODE_CONFLICT = "blocked_run_mode_conflict"


def _cmdline_tokens() -> set[str]:
    try:
        raw = Path("/proc/cmdline").read_text(encoding="utf-8")
    except OSError:
        return set()
    return {tok for tok in raw.split() if tok}


def _cmdline_flag(flag: str) -> bool:
    return flag in _cmdline_tokens()


def _mode_from_cmdline() -> str | None:
    """Return an explicit cmdline mode, or None when cmdline is silent/ambiguous."""
    if _cmdline_flag("setuphelfer_auto_discovery=1"):
        return "auto_discovery_only"
    if _cmdline_flag("setuphelfer_msi_e2e_auto=1"):
        return "auto_physical_e2e"
    # Lab-auto alone is ambiguous; discovery/physical controls decide.
    return None


def resolve_run_mode(
    *,
    setup_logs_base: Path | None = None,
    discovery_control: dict[str, Any] | None = None,
    physical_control: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve run_mode once. Run-control wins over kernel cmdline."""
    base = setup_logs_base or find_setup_logs_mount()
    disc = discovery_control
    phys = physical_control
    if disc is None and base is not None:
        disc = load_discovery_run_control(base)
    if phys is None and base is not None:
        phys = load_run_control(base)

    control_mode: str | None = None
    source = "default"

    if (
        disc
        and disc.get("enabled")
        and not disc.get("consumed")
        and disc.get("run_mode") in RUN_MODES
    ):
        control_mode = str(disc["run_mode"])
        source = "discovery_run_control"
    elif (
        phys
        and phys.get("enabled")
        and not phys.get("consumed")
    ):
        control_mode = "auto_physical_e2e"
        source = "physical_e2e_run_control"

    cmdline_mode = _mode_from_cmdline()

    if control_mode and cmdline_mode and control_mode != cmdline_mode:
        # Discovery-only control must win over stale e2e cmdline flags.
        if control_mode == "auto_discovery_only" and cmdline_mode == "auto_physical_e2e":
            return {
                "ok": True,
                "run_mode": control_mode,
                "source": source,
                "conflict": False,
                "code": "ok",
            }
        return {
            "ok": False,
            "run_mode": None,
            "source": source,
            "conflict": True,
            "code": BLOCKED_RUN_MODE_CONFLICT,
            "control_mode": control_mode,
            "cmdline_mode": cmdline_mode,
        }

    if control_mode:
        return {
            "ok": True,
            "run_mode": control_mode,
            "source": source,
            "conflict": False,
            "code": "ok",
        }

    if cmdline_mode:
        return {
            "ok": True,
            "run_mode": cmdline_mode,
            "source": "kernel_cmdline",
            "conflict": False,
            "code": "ok",
        }

    # Lab-auto without explicit mode: discovery control absent → interactive/lab evidence only.
    if _cmdline_flag("setuphelfer_msi_lab_auto=1"):
        return {
            "ok": True,
            "run_mode": "auto_physical_e2e",
            "source": "kernel_cmdline_lab_auto",
            "conflict": False,
            "code": "ok",
        }

    return {
        "ok": True,
        "run_mode": "interactive",
        "source": "default",
        "conflict": False,
        "code": "ok",
    }


def physical_e2e_start_allowed(
    *,
    setup_logs_base: Path | None = None,
) -> dict[str, Any]:
    resolved = resolve_run_mode(setup_logs_base=setup_logs_base)
    if not resolved.get("ok"):
        return {
            "physical_e2e_start_allowed": False,
            "reason": resolved.get("code") or BLOCKED_RUN_MODE_CONFLICT,
            "run_mode": resolved.get("run_mode"),
            "skip_class": "skipped_by_run_mode",
        }
    mode = str(resolved.get("run_mode") or "")
    if mode == "auto_discovery_only":
        return {
            "physical_e2e_start_allowed": False,
            "reason": "run_mode_auto_discovery_only",
            "run_mode": mode,
            "skip_class": "skipped_by_run_mode",
        }
    if mode not in {"auto_physical_e2e", "manual_physical_e2e"}:
        return {
            "physical_e2e_start_allowed": False,
            "reason": f"run_mode_{mode}",
            "run_mode": mode,
            "skip_class": "skipped_by_run_mode",
        }
    return {
        "physical_e2e_start_allowed": True,
        "reason": "run_mode_allows_physical_e2e",
        "run_mode": mode,
        "skip_class": "",
    }
