from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, resolve_handoff_path, write_json_handoff

_PLAN_REL = "docs/evidence/runtime-results/handoff/rescue_remote_help_plan.json"
_RESULT_REL = "docs/evidence/runtime-results/handoff/rescue_remote_help_result.json"
_MAX_BYTES = 512 * 1024


def _emit_plan(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_remote_help_plan_status": status,
        "rescue_remote_help_plan_file_path": _PLAN_REL,
        "rescue_remote_help_plan": body,
        "rescue_remote_help_plan_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _emit_result(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_remote_help_result_status": status,
        "rescue_remote_help_result_file_path": _RESULT_REL,
        "rescue_remote_help_result": body,
        "rescue_remote_help_result_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_remote_help_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_PLAN_REL, "RESCUE_RHPLAN")
    if oerr or out_path is None:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_RHPLAN_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RHPLAN")
    if gerr:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    body: dict[str, Any] = {
        "rescue_remote_help_plan_schema_version": 1,
        "strict_mode": "rescue_remote_help_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ssh_auto_start": False,
        "ssh_readonly_help_mode": True,
        "temporary_credentials": {"mode": "manual_operator_generated_later"},
        "session_hints": ["no password in logs", "rotate keys after session"],
        "qr_pairing": "planned_future",
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_plan("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit_plan("ok", body, wrote=True, warnings=[], errors=[])


def build_rescue_remote_help_result(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_RHRES")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_RHRES_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RHRES")
    if gerr:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    wlan_status = "unknown"
    try:
        p = Path("/proc/net/wireless")
        if p.is_file():
            txt = p.read_text(encoding="utf-8", errors="replace")
            wlan_status = "interfaces_present" if len(txt.splitlines()) > 2 else "no_wireless_counters"
    except OSError:
        wlan_status = "unreadable"

    body: dict[str, Any] = {
        "rescue_remote_help_result_schema_version": 1,
        "strict_mode": "rescue_remote_help_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "network_status": "not_probed_deep",
        "local_ip_hint": "127.0.0.1",
        "wlan_status": wlan_status,
        "ssh_service_auto_started": False,
        "ssh_readonly_help_mode_ready": True,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit_result("ok", body, wrote=True, warnings=[], errors=[])
