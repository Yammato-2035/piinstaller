"""
Rescue telemetry endpoint connectivity — health checks for lab and beta targets.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from core.rescue_issue_codes_v2 import RescueIssueCodeV2

TELEMETRY_CONNECTIVITY_SCHEMA = "telemetry-connectivity.v1"

TARGETS = {
  "dev_laptop_lab": "http://127.0.0.1:8101/v1/telemetry/health",
  "beta_server": "https://telemetrie.setuphelfer.de/v1/telemetry/health",
}


def _utc_now() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _fetch_health(url: str, *, timeout: int = 6) -> dict[str, Any]:
  try:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Setuphelfer-Rescue-Telemetry/1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
      body = resp.read().decode("utf-8", errors="replace")
      try:
        parsed = json.loads(body)
      except json.JSONDecodeError:
        parsed = {"raw": body[:200]}
      return {"reachable": True, "status_code": resp.status, "body": parsed}
  except (urllib.error.URLError, TimeoutError, ValueError) as exc:
    return {"reachable": False, "error": type(exc).__name__}


def build_telemetry_connectivity_v1(
  *,
  mode: str = "auto",
  custom_targets: dict[str, str] | None = None,
) -> dict[str, Any]:
  targets = dict(TARGETS)
  if custom_targets:
    targets.update(custom_targets)
  results: dict[str, Any] = {}
  for name, url in targets.items():
    results[name] = {"url": url, **_fetch_health(url)}

  issue_codes: list[str] = []
  if results.get("dev_laptop_lab", {}).get("reachable"):
    issue_codes.append(RescueIssueCodeV2.TELEMETRY_DEV_LAPTOP_REACHABLE.value)
  if results.get("beta_server", {}).get("reachable"):
    issue_codes.append(RescueIssueCodeV2.TELEMETRY_BETA_SERVER_REACHABLE.value)
  any_reachable = any(r.get("reachable") for r in results.values())
  if not any_reachable:
    if mode == "disabled":
      issue_codes.append(RescueIssueCodeV2.TELEMETRY_NOT_CONFIGURED.value)
    else:
      issue_codes.append(RescueIssueCodeV2.TELEMETRY_ENDPOINT_UNREACHABLE.value)

  return {
    "schema_version": TELEMETRY_CONNECTIVITY_SCHEMA,
    "collected_at": _utc_now(),
    "mode": mode,
    "targets": results,
    "issue_codes": sorted(set(issue_codes)),
  }
