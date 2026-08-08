"""
High-information boot orchestrator — injectable stage pipeline.

PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007.

Runs a fixed stage sequence with timeout metadata. Stage runners are injectable
so unit tests never need real hardware or shell. Independent stages continue
after ``controlled_drm_xorg_probe`` failure; TUI survival is modeled separately
from Xorg/GUI readiness. Chromium is never auto-started.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping

StageRunner = Callable[[], dict[str, Any]]

HIGH_INFORMATION_BOOT_ORCHESTRATOR_VERSION = 1

DEFAULT_BOOT_PROFILE = "ASUS-TUI-BASELINE-HIGHINFO"

STAGE_SPECS: list[dict[str, Any]] = [
    {"id": "tui_stabilize", "timeout_s": 30, "blocks_dependent": False},
    {"id": "hardware_inventory", "timeout_s": 60, "blocks_dependent": False},
    {"id": "baseline_cpu_ram_storage", "timeout_s": 60, "blocks_dependent": False},
    {"id": "kernel_acpi_pcie_analysis", "timeout_s": 45, "blocks_dependent": False},
    {"id": "driver_firmware_gap_detection", "timeout_s": 45, "blocks_dependent": False},
    {"id": "network_pipeline", "timeout_s": 90, "blocks_dependent": True},
    {"id": "telemetry_connectivity", "timeout_s": 60, "blocks_dependent": False},
    {"id": "controlled_drm_xorg_probe", "timeout_s": 45, "blocks_dependent": True},
    {"id": "optional_gui_probe", "timeout_s": 60, "blocks_dependent": False},
    {"id": "diagnostics_case", "timeout_s": 120, "blocks_dependent": False},
    {"id": "safe_local_remediation", "timeout_s": 60, "blocks_dependent": False},
    {"id": "install_readiness", "timeout_s": 30, "blocks_dependent": False},
    {"id": "final_evidence_flush", "timeout_s": 30, "blocks_dependent": False},
]

# Stages that prefer skip (no hardware/network/display side effects) when no runner is injected.
_SKIP_WITHOUT_RUNNER: frozenset[str] = frozenset(
    {
        "network_pipeline",
        "telemetry_connectivity",
        "controlled_drm_xorg_probe",
        "optional_gui_probe",
    }
)

# Dependents skipped when a blocking ancestor fails or times out.
_DEPENDENTS: dict[str, tuple[str, ...]] = {
    "network_pipeline": ("telemetry_connectivity",),
    "controlled_drm_xorg_probe": ("optional_gui_probe",),
}

_VALID_STATUSES = frozenset({"ok", "failed", "skipped", "timeout"})


def _stage_ids() -> list[str]:
    return [str(spec["id"]) for spec in STAGE_SPECS]


def _default_stage_result(stage_id: str) -> dict[str, Any]:
    if stage_id in _SKIP_WITHOUT_RUNNER:
        return {
            "stage_id": stage_id,
            "status": "skipped",
            "exit_code": 0,
            "duration_ms": 0,
            "evidence": {"reason": "injectable_not_provided"},
            "error": None,
        }
    return {
        "stage_id": stage_id,
        "status": "ok",
        "exit_code": 0,
        "duration_ms": 0,
        "evidence": {},
        "error": None,
    }


def _normalize_stage_result(stage_id: str, raw: Mapping[str, Any] | None, *, duration_ms: int) -> dict[str, Any]:
    data = dict(raw or {})
    status = str(data.get("status") or "ok").strip().lower()
    if status not in _VALID_STATUSES:
        status = "failed"
    exit_code = data.get("exit_code")
    if exit_code is None:
        exit_code = 0 if status in ("ok", "skipped") else 1
    evidence = data.get("evidence")
    if not isinstance(evidence, dict):
        evidence = {} if evidence is None else {"value": evidence}
    error = data.get("error")
    if error is not None:
        error = str(error)
    return {
        "stage_id": stage_id,
        "status": status,
        "exit_code": int(exit_code),
        "duration_ms": int(data.get("duration_ms", duration_ms)),
        "evidence": evidence,
        "error": error,
    }


def _skipped_result(stage_id: str, reason: str) -> dict[str, Any]:
    return {
        "stage_id": stage_id,
        "status": "skipped",
        "exit_code": 0,
        "duration_ms": 0,
        "evidence": {"reason": reason},
        "error": None,
    }


def _run_injected_stage(
    stage_id: str,
    runner: StageRunner,
    *,
    timeout_s: float,
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        raw = runner()
    except Exception as exc:  # noqa: BLE001 — stage isolation; failures become stage results
        duration_ms = int((time.monotonic() - started) * 1000)
        return {
            "stage_id": stage_id,
            "status": "failed",
            "exit_code": 1,
            "duration_ms": duration_ms,
            "evidence": {},
            "error": f"{type(exc).__name__}: {exc}",
        }
    duration_ms = int((time.monotonic() - started) * 1000)
    result = _normalize_stage_result(stage_id, raw if isinstance(raw, Mapping) else {"evidence": {"value": raw}}, duration_ms=duration_ms)
    if result["status"] != "timeout" and duration_ms > int(float(timeout_s) * 1000):
        result["status"] = "timeout"
        result["exit_code"] = int(result["exit_code"] or 1) or 1
        result["error"] = result["error"] or f"stage_timeout:{timeout_s}s"
    return result


def run_high_information_boot(
    *,
    run_id: str,
    boot_id: str,
    boot_profile: str = DEFAULT_BOOT_PROFILE,
    stage_runners: dict[str, Callable[[], dict]] | None = None,
    context: dict | None = None,
) -> dict[str, Any]:
    """
    Execute the high-information boot stage pipeline.

    Parameters
    ----------
    run_id / boot_id:
        Correlation identifiers for evidence.
    boot_profile:
        Boot profile label (default ASUS-TUI-BASELINE-HIGHINFO).
    stage_runners:
        Optional map of stage_id → zero-arg callable returning a stage result dict.
    context:
        Optional injectable state. Recognized keys:
        - ``xorg_ready`` (bool): gate for ``optional_gui_probe``
        - ``tui_survived`` (bool): override TUI survival model
        - ``chromium_started`` (bool): only honored when ``optional_gui_probe`` ran ok
    """
    runners = dict(stage_runners or {})
    ctx = dict(context or {})
    xorg_ready = bool(ctx.get("xorg_ready", False))
    tui_survived = True if "tui_survived" not in ctx else bool(ctx.get("tui_survived"))
    chromium_started = False
    blocked: set[str] = set()
    stages: list[dict[str, Any]] = []
    xorg_probe_status = "skipped"

    for spec in STAGE_SPECS:
        stage_id = str(spec["id"])
        timeout_s = float(spec["timeout_s"])
        blocks_dependent = bool(spec.get("blocks_dependent", False))

        # Prefer the concrete Xorg gate over a generic dependency block.
        if stage_id == "optional_gui_probe" and not xorg_ready:
            result = _skipped_result(stage_id, "xorg_not_ready")
            stages.append(result)
            continue

        if stage_id in blocked:
            result = _skipped_result(stage_id, "blocked_by_failed_dependency")
            stages.append(result)
            continue

        runner = runners.get(stage_id)
        if runner is None:
            result = _default_stage_result(stage_id)
        else:
            result = _run_injected_stage(stage_id, runner, timeout_s=timeout_s)

        stages.append(result)

        if stage_id == "tui_stabilize" and result["status"] in ("failed", "timeout"):
            tui_survived = False

        if stage_id == "controlled_drm_xorg_probe":
            xorg_probe_status = str(result["status"])
            if result["status"] == "ok":
                evidence = result.get("evidence") or {}
                if evidence.get("xorg_ready", True):
                    xorg_ready = True
                else:
                    xorg_ready = False
            else:
                # Probe failure/skip/timeout must not claim Xorg readiness.
                xorg_ready = False

        if stage_id == "optional_gui_probe" and result["status"] == "ok":
            evidence = result.get("evidence") or {}
            if bool(evidence.get("chromium_started")) or bool(ctx.get("chromium_started")):
                chromium_started = True

        if blocks_dependent and result["status"] in ("failed", "timeout"):
            for dep in _DEPENDENTS.get(stage_id, ()):
                blocked.add(dep)

    return {
        "run_id": run_id,
        "boot_id": boot_id,
        "boot_profile": boot_profile,
        "orchestrator_version": HIGH_INFORMATION_BOOT_ORCHESTRATOR_VERSION,
        "stage_order": _stage_ids(),
        "stages": stages,
        "tui_survived": bool(tui_survived),
        "xorg_probe": xorg_probe_status,
        "xorg_ready": bool(xorg_ready),
        "chromium_started": bool(chromium_started),
        "secrets_exposed": False,
    }
