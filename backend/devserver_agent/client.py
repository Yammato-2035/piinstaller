"""HTTP-Client für den Setuphelfer Development Server."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

INGEST_PATH = "/api/dev-server/ingest/report"
HEALTH_PATH = "/api/dev-server/health"


def _request_json(
    url: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: float = 5.0,
) -> tuple[int, dict[str, Any] | None, str | None]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["X-Dev-Server-Token"] = token
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(raw) if raw.strip() else {}, None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw) if raw.strip() else {"detail": raw}
        except json.JSONDecodeError:
            parsed = {"detail": raw}
        return exc.code, parsed, None
    except urllib.error.URLError as exc:
        return 0, None, str(exc.reason)
    except TimeoutError:
        return 0, None, "timeout"
    except OSError as exc:
        return 0, None, str(exc)


def health_check(server_url: str, *, timeout: float = 5.0) -> dict[str, Any]:
    url = server_url.rstrip("/") + HEALTH_PATH
    status, body, err = _request_json(url, timeout=timeout)
    return {
        "ok": status == 200 and body is not None,
        "http_status": status,
        "health": body or {},
        "error": err,
    }


def validate_server_health(health: dict[str, Any], mode: str) -> dict[str, Any]:
    h = health.get("health") if "health" in health else health
    if not isinstance(h, dict):
        return {"ok": False, "errors": ["invalid_health_response"]}
    errors: list[str] = []
    if not h.get("enabled"):
        errors.append("dev_server_disabled")
    if mode == "local_lab" and h.get("mode") != "local_lab":
        errors.append("dev_server_not_local_lab")
    if h.get("public_uploads_allowed") and mode == "public_rescue":
        errors.append("public_uploads_unexpected")
    return {"ok": not errors, "errors": errors, "health": h}


def post_report(
    server_url: str,
    node: dict[str, Any],
    report: dict[str, Any],
    token: str | None = None,
    *,
    timeout: float = 5.0,
) -> dict[str, Any]:
    url = server_url.rstrip("/") + INGEST_PATH
    body = {"node": node, "report": report}
    status, parsed, err = _request_json(url, method="POST", body=body, token=token, timeout=timeout)
    if err:
        logger.warning("dev_agent upload failed: %s", err[:200] if err else "unknown")
        return {
            "ok": False,
            "http_status": status,
            "code": "DEV_AGENT_UPLOAD_FAILED",
            "error": err,
            "response": None,
        }
    if status == 200 and isinstance(parsed, dict):
        return {
            "ok": True,
            "http_status": status,
            "code": parsed.get("code", "DEV_SERVER_REPORT_ACCEPTED"),
            "response": parsed,
            "error": None,
        }
    detail = parsed.get("detail") if isinstance(parsed, dict) else parsed
    if isinstance(detail, dict):
        return {
            "ok": False,
            "http_status": status,
            "code": detail.get("code", "DEV_AGENT_UPLOAD_BLOCKED"),
            "response": detail,
            "error": ",".join(detail.get("errors") or []) or "upload_blocked",
        }
    return {
        "ok": False,
        "http_status": status,
        "code": "DEV_AGENT_UPLOAD_FAILED",
        "response": parsed,
        "error": str(detail) if detail else f"http_{status}",
    }
