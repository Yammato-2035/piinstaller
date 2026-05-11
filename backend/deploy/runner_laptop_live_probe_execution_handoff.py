from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_ROUTES = _REPO_ROOT / "backend" / "deploy" / "routes.py"
_READINESS_REL = "docs/evidence/runtime-results/handoff/laptop_failure_test_execution_readiness_gate.json"
_PLAN_REL = "docs/evidence/runtime-results/handoff/laptop_live_probe_plan.json"
_RESULT_REL = "docs/evidence/runtime-results/handoff/laptop_live_probe_result.json"
_FINAL_REL = "docs/evidence/runtime-results/handoff/laptop_live_probe_final_gate.json"
_MAX_OUTPUT_BYTES = 768 * 1024
_HTTP_TIMEOUT = 5.0

_LEGACY_MARKERS = (
    "pi-installer",
    "piinstaller",
    "pi_installer_",
    "de.pi-installer.app",
    "/opt/pi-installer",
    "pi-installer.service",
)


def _resolve_handoff(rel_path: str, prefix: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, f"{prefix}_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, f"{prefix}_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, f"{prefix}_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, f"{prefix}_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _load_json_handoff(rel: str, prefix: str) -> tuple[Any | None, str | None]:
    p, err = _resolve_handoff(rel, prefix)
    if err or p is None or not p.is_file():
        return None, err or f"{prefix}_MISSING"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception:
        return None, f"{prefix}_JSON_INVALID"


def _http_json(method: str, url: str, body: dict[str, Any] | None, timeout_s: float) -> tuple[int | None, Any | None, str]:
    try:
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            raw = json.dumps(body).encode("utf-8")
            data = raw
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            code = int(getattr(resp, "status", 200) or 200)
            txt = resp.read().decode("utf-8", errors="replace")
            try:
                return code, json.loads(txt), ""
            except json.JSONDecodeError:
                return code, {"_non_json": txt[:2000]}, "LIVE_PROBE_HTTP_NON_JSON"
    except urllib.error.HTTPError as e:
        try:
            payload = e.read().decode("utf-8", errors="replace")
            return int(e.code), json.loads(payload), ""
        except Exception:
            return int(e.code), None, str(e)[:300]
    except Exception as e:
        return None, None, str(e)[:300]


def _validate_live_base_url(url: str) -> tuple[bool, str]:
    u = str(url or "").strip()
    if not u or len(u) > 256:
        return False, "LIVE_BASE_URL_EMPTY_OR_TOO_LONG"
    p = urlparse(u)
    if p.scheme not in ("http", "https"):
        return False, "LIVE_BASE_URL_SCHEME_INVALID"
    if not p.netloc:
        return False, "LIVE_BASE_URL_NO_NETLOC"
    if "@" in p.netloc:
        return False, "LIVE_BASE_URL_CREDENTIALS_FORBIDDEN"
    return True, ""


def _scan_live_probe_routes_safe() -> tuple[bool, list[str]]:
    if not _ROUTES.is_file():
        return False, ["ROUTES_FILE_MISSING"]
    hits: list[str] = []
    for ln in _ROUTES.read_text(encoding="utf-8", errors="replace").splitlines():
        low = ln.lower()
        if "laptop-live-probe" not in low or "@router.post" not in low:
            continue
        for bad in ("/execute", "/apply", "/install", "/delete", "/release", "/publish"):
            if bad in low:
                hits.append(f"{bad}:{ln.strip()[:160]}")
    return len(hits) == 0, hits


def _readiness_body(readiness: Any) -> dict[str, Any]:
    if isinstance(readiness, dict) and isinstance(readiness.get("laptop_failure_test_execution_readiness_gate"), dict):
        return readiness["laptop_failure_test_execution_readiness_gate"]
    if isinstance(readiness, dict) and ("gate_status" in readiness or "abnahme_decision" in readiness):
        return readiness
    return readiness if isinstance(readiness, dict) else {}


def build_laptop_live_probe_plan(
    *,
    explicit_overwrite: bool = False,
    live_base_url: str | None = None,
) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_PLAN_REL, "LIVE_PROBE_PLAN")
    if oerr or out_path is None:
        return _emit_plan("blocked", {}, [oerr or "LIVE_PROBE_PLAN_OUTPUT_INVALID"], [], wrote_file=False)
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _emit_plan("blocked", {}, ["LIVE_PROBE_PLAN_EXISTS_NO_OVERWRITE"], [], wrote_file=False)

    base = str(live_base_url or os.environ.get("SETUPHELFER_READINESS_BASE_URL") or "http://127.0.0.1:8000").strip()
    ok_url, uerr = _validate_live_base_url(base)
    if not ok_url:
        return _emit_plan("blocked", {}, [uerr], [], wrote_file=False)

    raw, rerr = _load_json_handoff(_READINESS_REL, "READINESS")
    if rerr or not isinstance(raw, dict):
        return _emit_plan("blocked", {}, [str(rerr or "READINESS_GATE_HANDOFF_MISSING")], [], wrote_file=False)

    inner = _readiness_body(raw)
    abnahme = str(inner.get("abnahme_decision") or "")
    gate_st = str(inner.get("gate_status") or "")

    routes_ok, forbidden = _scan_live_probe_routes_safe()
    if not routes_ok:
        return _emit_plan("blocked", {}, [f"LIVE_PROBE_FORBIDDEN_ROUTE_PATTERN:{x}" for x in forbidden[:12]], [], wrote_file=False)

    allowed_checks = [
        {"id": "get_version", "method": "GET", "path": "/api/version"},
        {"id": "get_health_api", "method": "GET", "path": "/api/health"},
        {"id": "get_health_root", "method": "GET", "path": "/health"},
        {"id": "get_network", "method": "GET", "path": "/api/system/network"},
        {"id": "get_preflight_sources", "method": "GET", "path": "/api/preflight/sources"},
        {"id": "post_backup_verify_empty", "method": "POST", "path": "/api/backup/verify", "body": {}},
        {
            "id": "post_backup_verify_invalid_contract",
            "method": "POST",
            "path": "/api/backup/verify",
            "body": {"file": "__live_probe_invalid_path__", "mode": "basic"},
        },
        {
            "id": "post_manual_runtime_precheck_min",
            "method": "POST",
            "path": "/api/deploy/runner/manual-runtime/precheck",
            "body": {
                "selected_runbook": "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
                "next_phase_gate": {"allowed_next_phases": ["NEXT_PHASE_MANUAL_RUNTIME_TESTS"]},
                "operator_confirmations": {
                    "full_backup_confirmed": True,
                    "local_control_confirmed": True,
                    "single_test_media_confirmed": True,
                    "productive_media_removed_confirmed": True,
                    "stop_conditions_acknowledged": True,
                    "no_remote_without_local_control_confirmed": True,
                    "no_auto_retry_confirmed": True,
                    "operator_understands_data_loss": True,
                },
                "hardware_gate_report": {},
                "real_write_guard_report": {},
                "runtime_context": {},
            },
        },
        {
            "id": "post_manual_runtime_result_template_min",
            "method": "POST",
            "path": "/api/deploy/runner/manual-runtime/result-template",
            "body": {"precheck": {"precheck_status": "blocked"}, "explicit_overwrite": False},
        },
    ]

    plan_status = "ok"
    warnings: list[str] = []
    if abnahme != "pass":
        plan_status = "review_required"
        warnings.append("LIVE_PROBE_PLAN_READINESS_ABNAHME_NOT_PASS")
    if gate_st == "blocked":
        plan_status = "blocked"
        warnings.append("LIVE_PROBE_PLAN_READINESS_GATE_BLOCKED")
    elif gate_st == "review_required" and plan_status == "ok":
        plan_status = "review_required"

    body: dict[str, Any] = {
        "live_probe_plan_schema_version": 1,
        "strict_mode": "laptop_live_probe_execution_handoff_plan",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plan_status": plan_status,
        "live_base_url": base,
        "readiness_gate_handoff": _READINESS_REL,
        "readiness_abnahme_decision": abnahme,
        "readiness_gate_status": gate_st,
        "allowed_checks": allowed_checks,
        "constraints": {
            "no_restore": True,
            "no_device_write": True,
            "no_low_level_fs_ops": True,
            "no_systemctl_lifecycle": True,
            "no_chmod_chown": True,
            "no_delete": True,
            "max_http_timeout_seconds": _HTTP_TIMEOUT,
            "allow_real_verify_path_default_false": True,
        },
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit_plan("blocked", {}, ["LIVE_PROBE_PLAN_OUTPUT_TOO_LARGE"], warnings, wrote_file=False)
    if plan_status == "blocked":
        return _emit_plan("blocked", body, ["LIVE_PROBE_PLAN_BLOCKED_BY_READINESS"], warnings, wrote_file=False)
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _emit_plan("blocked", {}, ["LIVE_PROBE_PLAN_WRITE_FAILED"], warnings, wrote_file=False)
    return _emit_plan(plan_status, body, [], warnings, wrote_file=True)


def _emit_plan(
    status: str, body: dict[str, Any], errors: list[str], warnings: list[str], *, wrote_file: bool
) -> dict[str, Any]:
    return {
        "laptop_live_probe_plan_status": status,
        "laptop_live_probe_plan_file_path": _PLAN_REL,
        "laptop_live_probe_plan": body,
        "laptop_live_probe_handoff_written": wrote_file,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _response_legacy_hits(js: Any) -> list[str]:
    if js is None:
        return []
    blob = json.dumps(js, ensure_ascii=False).lower()
    hits = [m for m in _LEGACY_MARKERS if m.lower() in blob]
    return list(dict.fromkeys(hits))


def _setuphelfer_version_hits(js: Any) -> bool:
    if not isinstance(js, dict):
        return False
    blob = json.dumps(js, ensure_ascii=False).lower()
    if "setuphelfer" in blob or "project_version" in blob:
        return True
    v = str(js.get("version") or js.get("project_version") or "")
    return bool(re.search(r"\d+\.\d+", v))


def _health_degraded(js: Any) -> bool:
    if not isinstance(js, dict):
        return False
    st = str(js.get("status") or js.get("health") or "").lower()
    return "degrad" in st


def execute_laptop_live_probe_readonly(
    *,
    explicit_overwrite: bool = False,
    explicit_execute_live_probe: bool = False,
    allow_real_verify_path: bool = False,
    live_base_url: str | None = None,
) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_RESULT_REL, "LIVE_PROBE_RESULT")
    if oerr or out_path is None:
        return _emit_exec("blocked", {}, [oerr or "LIVE_PROBE_RESULT_OUTPUT_INVALID"], [], wrote_file=False)
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _emit_exec("blocked", {}, ["LIVE_PROBE_RESULT_EXISTS_NO_OVERWRITE"], [], wrote_file=False)
    if not explicit_execute_live_probe:
        return _emit_exec(
            "blocked",
            {},
            ["LIVE_PROBE_EXECUTE_REQUIRES_EXPLICIT_EXECUTE_LIVE_PROBE"],
            [],
            wrote_file=False,
        )

    plan_raw, perr = _load_json_handoff(_PLAN_REL, "PLAN")
    if perr or not isinstance(plan_raw, dict):
        return _emit_exec("blocked", {}, [str(perr or "LIVE_PROBE_PLAN_MISSING")], [], wrote_file=False)
    if str(plan_raw.get("plan_status") or "") == "blocked":
        return _emit_exec("blocked", {}, ["LIVE_PROBE_PLAN_STATUS_BLOCKED"], [], wrote_file=False)

    base = str(live_base_url or plan_raw.get("live_base_url") or "").strip()
    ok_url, uerr = _validate_live_base_url(base)
    if not ok_url:
        return _emit_exec("blocked", {}, [uerr], [], wrote_file=False)

    checks = plan_raw.get("allowed_checks")
    if not isinstance(checks, list):
        return _emit_exec("blocked", {}, ["LIVE_PROBE_PLAN_ALLOWED_CHECKS_INVALID"], [], wrote_file=False)

    executions: list[dict[str, Any]] = []
    for ch in checks:
        if not isinstance(ch, dict):
            continue
        cid = str(ch.get("id") or "")
        method = str(ch.get("method") or "GET").upper()
        path = str(ch.get("path") or "")
        body = ch.get("body") if isinstance(ch.get("body"), dict) else None
        if method == "POST" and path == "/api/backup/verify" and body and not allow_real_verify_path:
            bf = str((body.get("file") or body.get("backup_file") or "")).strip()
            if bf and bf not in ("", "__live_probe_invalid_path__") and not bf.startswith("__"):
                executions.append(
                    {
                        "id": cid,
                        "skipped": True,
                        "reason": "REAL_VERIFY_PATH_NOT_ALLOWED",
                        "path": path,
                    }
                )
                continue
        url = base.rstrip("/") + path
        code, js, err = _http_json(method, url, body, _HTTP_TIMEOUT)
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
        "live_probe_execution_schema_version": 1,
        "strict_mode": "laptop_live_probe_readonly_execution",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "live_base_url": base,
        "allow_real_verify_path": bool(allow_real_verify_path),
        "executions": executions,
    }
    try:
        _atomic_write(out_path, json.dumps(raw_body, indent=2, sort_keys=True))
    except OSError:
        return _emit_exec("blocked", {}, ["LIVE_PROBE_RESULT_WRITE_FAILED"], [], wrote_file=False)

    res = build_laptop_live_probe_result(explicit_overwrite=True)
    if isinstance(res, dict):
        res["laptop_live_probe_execute_readonly_status"] = "ok"
    return res


def build_laptop_live_probe_result(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_RESULT_REL, "LIVE_PROBE_RESULT")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, [oerr or "LIVE_PROBE_RESULT_PATH_INVALID"], [], wrote_file=False)
    if not out_path.is_file():
        return _emit_result("blocked", {}, ["LIVE_PROBE_RESULT_MISSING_RUN_EXECUTE_FIRST"], [], wrote_file=False)

    try:
        data = json.loads(out_path.read_text(encoding="utf-8"))
    except Exception:
        return _emit_result("blocked", {}, ["LIVE_PROBE_RESULT_JSON_INVALID"], [], wrote_file=False)

    ex = data.get("executions")
    if not isinstance(ex, list):
        return _emit_result("blocked", {}, ["LIVE_PROBE_RESULT_NO_EXECUTIONS"], [], wrote_file=False)

    version_js = None
    health_js = None
    network_ok = False
    legacy_hits_all: list[str] = []
    server_errors = 0
    unreachable = 0
    version_200 = False
    for row in ex:
        if not isinstance(row, dict) or row.get("skipped"):
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
            warnings.append("LIVE_PROBE_HEALTH_DEGRADED")
        if not network_ok:
            warnings.append("LIVE_PROBE_NETWORK_NOT_CONFIRMED_200")

    merged = dict(data)
    merged["evaluation"] = {
        "live_probe_result_status": eval_status,
        "api_reachable": api_reachable,
        "setuphelfer_version_signal": setuphelfer_ok,
        "health_degraded": health_deg,
        "legacy_runtime_detected": legacy_detected,
        "legacy_markers_hit": list(dict.fromkeys(legacy_hits_all)),
        "unreachable_requests": unreachable,
        "http_5xx_count": server_errors,
    }
    text = json.dumps(merged, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit_result("blocked", {}, ["LIVE_PROBE_RESULT_OUTPUT_TOO_LARGE"], warnings, wrote_file=False)
    if not explicit_overwrite:
        return _emit_result("blocked", {}, ["LIVE_PROBE_RESULT_REQUIRES_EXPLICIT_OVERWRITE_TO_MERGE_EVAL"], warnings, wrote_file=False)
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _emit_result("blocked", {}, ["LIVE_PROBE_RESULT_MERGE_WRITE_FAILED"], warnings, wrote_file=False)
    return _emit_result(eval_status, merged, [], warnings, wrote_file=True)


def _emit_result(
    status: str, body: dict[str, Any], errors: list[str], warnings: list[str], *, wrote_file: bool
) -> dict[str, Any]:
    return {
        "laptop_live_probe_result_status": status,
        "laptop_live_probe_result_file_path": _RESULT_REL,
        "laptop_live_probe_result": body,
        "laptop_live_probe_handoff_written": wrote_file,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_laptop_live_probe_final_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    fout, ferr = _resolve_handoff(_FINAL_REL, "LIVE_PROBE_FINAL")
    if ferr or fout is None:
        return _emit_final("blocked", {}, [ferr or "LIVE_PROBE_FINAL_OUTPUT_INVALID"], [], wrote_file=False)
    if fout.exists() and fout.is_file() and not explicit_overwrite:
        return _emit_final("blocked", {}, ["LIVE_PROBE_FINAL_EXISTS_NO_OVERWRITE"], [], wrote_file=False)

    plan, perr = _load_json_handoff(_PLAN_REL, "PLAN")
    res, rerr = _load_json_handoff(_RESULT_REL, "RESULT")
    errors: list[str] = []
    if perr or not isinstance(plan, dict):
        errors.append(str(perr or "PLAN_MISSING"))
    if rerr or not isinstance(res, dict):
        errors.append(str(rerr or "RESULT_MISSING"))
    if errors:
        return _emit_final("blocked", {}, errors, [], wrote_file=False)

    ev = res.get("evaluation") if isinstance(res.get("evaluation"), dict) else {}
    api_reachable = bool(ev.get("api_reachable"))
    legacy = bool(ev.get("legacy_runtime_detected"))
    setup_ok = bool(ev.get("setuphelfer_version_signal"))
    res_st = str(ev.get("live_probe_result_status") or "blocked")

    blocked_reasons: list[str] = []
    warnings: list[str] = []
    if str(plan.get("plan_status") or "") != "ok":
        warnings.append("LIVE_PROBE_FINAL_PLAN_NOT_OK")
    if res_st == "review_required":
        warnings.append("LIVE_PROBE_FINAL_RESULT_REVIEW_REQUIRED")

    gate_status = "ok"
    if res_st == "blocked" or legacy or not api_reachable or not setup_ok:
        gate_status = "blocked"
        if legacy:
            blocked_reasons.append("LEGACY_RUNTIME_IN_RESPONSE")
        if not api_reachable:
            blocked_reasons.append("API_NOT_REACHABLE_OR_ERRORS")
        if not setup_ok:
            blocked_reasons.append("SETUPHELFER_VERSION_NOT_CONFIRMED")
        if res_st == "blocked":
            blocked_reasons.append("RESULT_STATUS_BLOCKED")
    elif res_st == "review_required" or str(plan.get("plan_status") or "") != "ok":
        gate_status = "review_required"

    safe = (
        gate_status == "ok"
        and api_reachable
        and setup_ok
        and not legacy
        and str(plan.get("plan_status") or "") == "ok"
        and str(plan.get("readiness_abnahme_decision") or "") == "pass"
    )

    body: dict[str, Any] = {
        "live_probe_final_gate_schema_version": 1,
        "strict_mode": "laptop_live_probe_final_gate",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "live_probe_gate_status": gate_status,
        "api_reachable": api_reachable,
        "setuphelfer_runtime_confirmed": setup_ok,
        "legacy_runtime_detected": legacy,
        "safe_to_start_manual_laptop_failure_run": bool(safe),
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "warnings": list(dict.fromkeys(warnings)),
        "inputs": {"plan": _PLAN_REL, "result": _RESULT_REL},
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit_final("blocked", {}, ["LIVE_PROBE_FINAL_OUTPUT_TOO_LARGE"], warnings, wrote_file=False)
    try:
        _atomic_write(fout, text)
    except OSError:
        return _emit_final("blocked", {}, ["LIVE_PROBE_FINAL_WRITE_FAILED"], warnings, wrote_file=False)
    return _emit_final(gate_status, body, [], warnings, wrote_file=True)


def _emit_exec(
    status: str, body: dict[str, Any], errors: list[str], warnings: list[str], *, wrote_file: bool
) -> dict[str, Any]:
    return {
        "laptop_live_probe_execute_readonly_status": status,
        "laptop_live_probe_result_file_path": _RESULT_REL,
        "laptop_live_probe_result": body,
        "laptop_live_probe_handoff_written": wrote_file,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _emit_final(
    status: str, body: dict[str, Any], errors: list[str], warnings: list[str], *, wrote_file: bool
) -> dict[str, Any]:
    return {
        "laptop_live_probe_final_gate_status": status,
        "laptop_live_probe_final_gate_file_path": _FINAL_REL,
        "laptop_live_probe_final_gate": body,
        "laptop_live_probe_handoff_written": wrote_file,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
