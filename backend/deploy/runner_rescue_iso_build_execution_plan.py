from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, resolve_handoff_path, write_json_handoff

_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_iso_execution_plan.json"
_MAX_BYTES = 768 * 1024


def _emit(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_iso_execution_plan_status": status,
        "rescue_iso_execution_plan_file_path": _OUT_REL,
        "rescue_iso_execution_plan": body,
        "rescue_iso_execution_plan_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_iso_execution_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_ISOPLAN")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_ISOPLAN_OUTPUT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ISOPLAN")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    body: dict[str, Any] = {
        "rescue_iso_execution_plan_schema_version": 1,
        "strict_mode": "setuphelfer_rescue_iso_phase1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "allowed_steps": [
            {"order": 1, "id": "ensure_workspace", "description": "mkdir build/rescue/*"},
            {"order": 2, "id": "precheck_tooling", "description": "verify live-build (lb) present"},
            {"order": 3, "id": "run_controlled_script", "description": "bash scripts/rescue/build-rescue-iso-controlled.sh"},
            {"order": 4, "id": "validate_iso", "description": "size + sha256 under build/rescue/output/"},
        ],
        "build_timeouts": {"iso_build_seconds": 7200, "precheck_seconds": 120},
        "resource_limits": {"min_free_disk_bytes": 12_000_000_000, "max_iso_bytes": 4_000_000_000},
        "forbidden_commands": ["dd", "mkfs", "wipefs", "mount /dev/sd", "systemctl", "apt install", "apt-get install"],
        "allowed_workdirs": ["build/rescue/", "build/rescue/live-build/", "build/rescue/output/", "build/rescue/logs/", "build/rescue/evidence/"],
        "allowed_output_globs": ["build/rescue/output/*.iso", "build/rescue/logs/*.log", "build/rescue/evidence/*.json"],
        "notes": [
            "Host systemctl and host apt installs are forbidden from runners.",
            "Real build requires SETUPHELFER_RESCUE_BUILD_APPROVED=1 in the controlled script environment.",
        ],
    }

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit("ok", body, wrote=True, warnings=[], errors=[])
