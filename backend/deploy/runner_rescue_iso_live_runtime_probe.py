from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from deploy.runner_laptop_live_probe_execution_handoff import (
    _health_degraded,
    _http_json,
    _response_legacy_hits,
    _setuphelfer_version_hits,
    _validate_live_base_url,
)
from deploy.runner_rescue_io import atomic_write_text, guard_handoff_overwrite, load_json_handoff, resolve_handoff_path

_PLAN_REL = "docs/evidence/runtime-results/handoff/rescue_iso_live_runtime_probe_plan.json"
_RESULT_REL = "docs/evidence/runtime-results/handoff/rescue_iso_live_runtime_probe_result.json"
_MAX_OUTPUT_BYTES = 768 * 1024
_HTTP_TIMEOUT = 5.0


def _emit_plan(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_iso_live_runtime_probe_plan_status": status,
        "rescue_iso_live_runtime_probe_plan_file_path": _PLAN_REL,
        "rescue_iso_live_runtime_probe_plan": body,
        "rescue_iso_live_runtime_probe_plan_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _emit_exec(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_iso_live_runtime_probe_execute_status": status,
        "rescue_iso_live_runtime_probe_result_file_path": _RESULT_REL,
        "rescue_iso_live_runtime_probe_result": body,
        "rescue_iso_live_runtime_probe_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _emit_eval(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_iso_live_runtime_probe_result_status": status,
        "rescue_iso_live_runtime_probe_result_file_path": _RESULT_REL,
        "rescue_iso_live_runtime_probe_result": body,
        "rescue_iso_live_runtime_probe_result_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_iso_live_runtime_probe_plan(
    *,
    explicit_overwrite: bool = False,
    live_base_url: str | None = None,
) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_PLAN_REL, "RESCUE_ISOPLAN")
    if oerr or out_path is None:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_ISOPLAN_OUTPUT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ISOPLAN")
    if gerr:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    base = str(live_base_url or "http://127.0.0.1:8000").strip()
    ok_url, uerr = _validate_live_base_url(base)
    if not ok_url:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[uerr])

    allowed_checks = [
        {"id": "get_version", "method": "GET", "path": "/api/version"},
        {"id": "get_health_api", "method": "GET", "path": "/api/health"},
        {"id": "get_health_root", "method": "GET", "path": "/health"},
        {"id": "get_network", "method": "GET", "path": "/api/system/network"},
        {"id": "get_inspect", "method": "GET", "path": "/api/inspect/run"},
        {"id": "post_branding_guard", "method": "POST", "path": "/api/deploy/setuphelfer-branding-guard-check", "body": {"explicit_overwrite": False}},
    ]

    body: dict[str, Any] = {
        "iso_live_runtime_probe_plan_schema_version": 1,
        "strict_mode": "rescue_iso_live_runtime_probe",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plan_status": "ok",
        "live_base_url": base,
        "allowed_checks": allowed_checks,
        "constraints": {"no_restore_execute": True, "no_device_write": True, "readonly_inspect": True},
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=["ISO_LIVE_PROBE_PLAN_TOO_LARGE"])
    try:
        atomic_write_text(out_path, text)
    except OSError:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=["ISO_LIVE_PROBE_PLAN_WRITE_FAILED"])
    return _emit_plan("ok", body, wrote=True, warnings=[], errors=[])


def execute_rescue_iso_live_runtime_probe(
    *,
    explicit_overwrite: bool = False,
    explicit_execute_iso_live_runtime_probe: bool = False,
    live_base_url: str | None = None,
) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_ISOPROBE")
    if oerr or out_path is None:
        return _emit_exec("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_ISOPROBE_OUTPUT_INVALID"])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _emit_exec("blocked", {}, wrote=False, warnings=[], errors=["ISO_LIVE_PROBE_RESULT_EXISTS_NO_OVERWRITE"])
    if not explicit_execute_iso_live_runtime_probe:
        return _emit_exec(
            "blocked",
            {},
            wrote=False,
            warnings=[],
            errors=["ISO_LIVE_PROBE_EXECUTE_REQUIRES_EXPLICIT_FLAG"],
        )

    plan_raw, _ = load_json_handoff(_PLAN_REL, "PLAN")
    if not isinstance(plan_raw, dict) or str(plan_raw.get("plan_status") or "") == "blocked":
        return _emit_exec("blocked", {}, wrote=False, warnings=[], errors=["ISO_LIVE_PROBE_PLAN_MISSING_OR_BLOCKED"])

    base = str(live_base_url or plan_raw.get("live_base_url") or "").strip()
    ok_url, uerr = _validate_live_base_url(base)
    if not ok_url:
        return _emit_exec("blocked", {}, wrote=False, warnings=[], errors=[uerr])

    checks = plan_raw.get("allowed_checks")
    if not isinstance(checks, list):
        return _emit_exec("blocked", {}, wrote=False, warnings=[], errors=["ISO_LIVE_PROBE_ALLOWED_CHECKS_INVALID"])

    executions: list[dict[str, Any]] = []
    for ch in checks:
        if not isinstance(ch, dict):
            continue
        cid = str(ch.get("id") or "")
        method = str(ch.get("method") or "GET").upper()
        path = str(ch.get("path") or "")
        req_body = ch.get("body") if isinstance(ch.get("body"), dict) else None
        url = base.rstrip("/") + path
        code, js, err = _http_json(method, url, req_body, _HTTP_TIMEOUT)
        row: dict[str, Any] = {
            "id": cid,
            "method": method,
            "path": path,
            "url": url,
            "http_status": code,
            "error": err,
            "response_excerpt": json.dumps(js, ensure_ascii=False)[:8000] if js is not None else None,
        }
        if isinstance(js, (dict, list)):
            row["response_json"] = js
        executions.append(row)

    raw_body: dict[str, Any] = {
        "iso_live_runtime_probe_execution_schema_version": 1,
        "strict_mode": "rescue_iso_live_runtime_probe_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "live_base_url": base,
        "executions": executions,
    }
    try:
        atomic_write_text(out_path, json.dumps(raw_body, indent=2, sort_keys=True))
    except OSError:
        return _emit_exec("blocked", {}, wrote=False, warnings=[], errors=["ISO_LIVE_PROBE_RESULT_WRITE_FAILED"])

    return build_rescue_iso_live_runtime_probe_result(explicit_overwrite=explicit_overwrite)


def build_rescue_iso_live_runtime_probe_result(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_ISOPROBE")
    if oerr or out_path is None:
        return _emit_eval("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_ISOPROBE_PATH_INVALID"])
    if not out_path.is_file():
        return _emit_eval("blocked", {}, wrote=False, warnings=[], errors=["ISO_LIVE_PROBE_RESULT_MISSING_RUN_FIRST"])

    try:
        data = json.loads(out_path.read_text(encoding="utf-8"))
    except Exception:
        return _emit_eval("blocked", {}, wrote=False, warnings=[], errors=["ISO_LIVE_PROBE_RESULT_JSON_INVALID"])

    ex = data.get("executions")
    if not isinstance(ex, list):
        return _emit_eval("blocked", {}, wrote=False, warnings=[], errors=["ISO_LIVE_PROBE_NO_EXECUTIONS"])

    version_js = None
    health_js = None
    network_ok = False
    inspect_ok = False
    branding_ok = False
    legacy_hits_all: list[str] = []
    server_errors = 0
    unreachable = 0
    version_200 = False

    for row in ex:
        if not isinstance(row, dict):
            continue
        cid = str(row.get("id") or "")
        code = row.get("http_status")
        err = str(row.get("error") or "")
        if code is None and err:
            unreachable += 1
        if isinstance(code, int) and code >= 500:
            server_errors += 1
        js = row.get("response_json")
        if js is None:
            excerpt = row.get("response_excerpt")
            if isinstance(excerpt, str) and excerpt.strip().startswith("{"):
                try:
                    js = json.loads(excerpt)
                except json.JSONDecodeError:
                    js = None
        legacy_hits_all.extend(_response_legacy_hits(js))
        if cid == "get_version" and code == 200:
            version_200 = True
            version_js = js if isinstance(js, dict) else version_js
        if cid in ("get_health_api", "get_health_root") and code == 200 and isinstance(js, dict) and health_js is None:
            health_js = js
        if cid == "get_network" and code == 200:
            network_ok = True
        if cid == "get_inspect" and code == 200:
            inspect_ok = True
        if cid == "post_branding_guard" and code == 200 and isinstance(js, dict):
            top = str(js.get("code") or "")
            inner = js.get("setuphelfer_branding_guard_check") if isinstance(js.get("setuphelfer_branding_guard_check"), dict) else {}
            st = str(inner.get("setuphelfer_branding_guard_check_status") or "") if isinstance(inner, dict) else ""
            branding_ok = top.endswith("_OK") or st == "ok"

    legacy_detected = len(set(legacy_hits_all)) > 0
    api_reachable = unreachable == 0 and server_errors == 0 and version_200
    setuphelfer_ok = _setuphelfer_version_hits(version_js)
    health_deg = _health_degraded(health_js)

    eval_status = "ok"
    warnings: list[str] = []
    if legacy_detected:
        eval_status = "blocked"
    elif unreachable > 0 or server_errors > 0:
        eval_status = "blocked"
    elif not api_reachable or not setuphelfer_ok:
        eval_status = "blocked"
    elif health_deg or not network_ok:
        eval_status = "review_required"
        if health_deg:
            warnings.append("ISO_LIVE_PROBE_HEALTH_DEGRADED")
        if not network_ok:
            warnings.append("ISO_LIVE_PROBE_NETWORK_NOT_CONFIRMED")
    elif not inspect_ok:
        eval_status = "review_required"
        warnings.append("ISO_LIVE_PROBE_INSPECT_NOT_CONFIRMED")
    elif not branding_ok:
        eval_status = "review_required"
        warnings.append("ISO_LIVE_PROBE_BRANDING_GUARD_NOT_OK")

    merged = dict(data)
    merged["evaluation"] = {
        "iso_live_runtime_probe_status": eval_status,
        "api_reachable": api_reachable,
        "setuphelfer_version_signal": setuphelfer_ok,
        "health_degraded": health_deg,
        "inspect_readonly_ok": inspect_ok,
        "branding_guard_http_ok": branding_ok,
        "legacy_runtime_detected": legacy_detected,
        "legacy_markers_hit": list(dict.fromkeys(legacy_hits_all)),
        "unreachable_requests": unreachable,
        "http_5xx_count": server_errors,
    }
    text = json.dumps(merged, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit_eval("blocked", {}, wrote=False, warnings=warnings, errors=["ISO_LIVE_PROBE_RESULT_TOO_LARGE"])
    if not explicit_overwrite:
        return _emit_eval("blocked", {}, wrote=False, warnings=warnings, errors=["ISO_LIVE_PROBE_RESULT_REQUIRES_EXPLICIT_OVERWRITE"])
    try:
        atomic_write_text(out_path, text)
    except OSError:
        return _emit_eval("blocked", {}, wrote=False, warnings=warnings, errors=["ISO_LIVE_PROBE_RESULT_MERGE_WRITE_FAILED"])
    return _emit_eval(eval_status, merged, wrote=True, warnings=warnings, errors=[])
