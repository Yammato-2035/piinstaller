"""Diagnostics status query for physical E2E (read-only)."""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from typing import Any, Callable

from core.rescue_physical_e2e_models import DEFAULT_DIAGNOSTICS_CASE_URL_TEMPLATE

HttpGetFn = Callable[[str, int], tuple[int, dict[str, Any]]]


def _default_http_get(url: str, timeout_seconds: int) -> tuple[int, dict[str, Any]]:
    context = ssl.create_default_context()
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds, context=context) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"raw_error": raw[:200]}
        return exc.code, body
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return 0, {}


def build_diagnostics_status_from_case(case_body: dict[str, Any], *, http_status: int) -> dict[str, Any]:
    if http_status != 200:
        return {
            "data_received": False,
            "diagnostics_status": "failed" if http_status else "ausstehend",
            "checks_passed": 0,
            "findings_count": None,
            "remediation_available": False,
            "http_status": http_status,
        }

    checks = case_body.get("checks") or []
    findings = case_body.get("findings") or []
    passed = sum(1 for item in checks if str(item.get("status", "")).lower() == "passed")
    status = str(case_body.get("status") or "wird_verarbeitet")
    mapped = {
        "pending": "ausstehend",
        "processing": "wird_verarbeitet",
        "completed": "abgeschlossen",
        "failed": "fehlgeschlagen",
    }.get(status, status)

    return {
        "data_received": True,
        "diagnostics_status": mapped,
        "checks_passed": passed,
        "findings_count": len(findings),
        "remediation_available": any(f.get("recommended_steps") for f in findings),
        "engine": case_body.get("engine") or "real_input_driven",
        "case_id": case_body.get("case_id"),
        "e2e_run_id": case_body.get("e2e_run_id"),
        "http_status": http_status,
    }


def query_diagnostics_case(
    e2e_run_id: str,
    *,
    base_url_template: str | None = None,
    timeout_seconds: int = 30,
    http_get: HttpGetFn | None = None,
) -> dict[str, Any]:
    template = (
        base_url_template
        or os.getenv("SETUPHELFER_DIAGNOSTICS_CASE_URL_TEMPLATE", DEFAULT_DIAGNOSTICS_CASE_URL_TEMPLATE)
    )
    url = template.format(e2e_run_id=e2e_run_id)
    getter = http_get or _default_http_get
    status, body = getter(url, timeout_seconds)
    return build_diagnostics_status_from_case(body, http_status=status)
