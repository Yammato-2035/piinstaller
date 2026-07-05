"""
Rescue network connectivity V2 — LAN/WLAN → Internet → DNS → HTTPS chain.
"""

from __future__ import annotations

import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from core.rescue_issue_codes_v2 import RescueIssueCodeV2

CONNECTIVITY_SCHEMA_VERSION = "network-connectivity.v2"
DEFAULT_HTTPS_TEST_URL = "https://www.debian.org/"
DEFAULT_DNS_HOST = "debian.org"


def _utc_now() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _run(cmd: list[str], *, timeout: int = 12) -> str:
  try:
    return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=timeout)
  except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
    return ""


def _interface_states() -> dict[str, Any]:
  ip_link = _run(["ip", "-o", "link"])
  lan_up = bool(re.search(r"\ben\d+.*state UP|\beth\d+.*state UP", ip_link))
  wifi_up = bool(re.search(r"\bwlan\d+.*state UP|\bwlp.*state UP", ip_link))
  nm = _run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device"])
  wifi_connected = ":wifi:connected" in nm
  lan_connected = bool(re.search(r":ethernet:connected", nm))
  return {
    "lan_present": bool(re.search(r"\ben\d+|\beth\d+", ip_link)),
    "wlan_present": bool(re.search(r"\bwlan|\bwlp", ip_link)),
    "lan_link_up": lan_up,
    "wlan_link_up": wifi_up,
    "lan_connected": lan_connected,
    "wifi_connected": wifi_connected,
  }


def _default_route() -> bool:
  routes = _run(["ip", "route"])
  return "default" in routes


def _dns_lookup(host: str = DEFAULT_DNS_HOST) -> bool:
  out = _run(["getent", "hosts", host]) or _run(["host", host])
  return bool(out.strip()) and "not found" not in out.lower()


def _https_get(url: str, *, timeout: int = 8) -> bool:
  try:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Setuphelfer-Rescue/2"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
      return 200 <= resp.status < 400
  except (urllib.error.URLError, TimeoutError, ValueError):
    return False


def detect_lan_blocks_wifi_regression(interfaces: dict[str, Any]) -> bool:
  """Regression: LAN up but WLAN cannot connect while radio on."""
  return (
    interfaces.get("lan_connected") is True
    and interfaces.get("wlan_present") is True
    and interfaces.get("wifi_connected") is False
    and interfaces.get("wlan_link_up") is False
  )


def build_network_connectivity_v2(
  *,
  https_test_url: str = DEFAULT_HTTPS_TEST_URL,
  dns_host: str = DEFAULT_DNS_HOST,
) -> dict[str, Any]:
  interfaces = _interface_states()
  default_route = _default_route()
  dns_ok = _dns_lookup(dns_host) if default_route else False
  https_ok = _https_get(https_test_url) if dns_ok else False

  issue_codes: list[str] = []
  if interfaces.get("lan_link_up") or interfaces.get("lan_connected"):
    issue_codes.append(RescueIssueCodeV2.NETWORK_LAN_UP.value)
  else:
    issue_codes.append(RescueIssueCodeV2.NETWORK_LAN_DOWN.value)
  if interfaces.get("wifi_connected"):
    issue_codes.append(RescueIssueCodeV2.NETWORK_WIFI_CONNECTED.value)
  else:
    issue_codes.append(RescueIssueCodeV2.NETWORK_WIFI_UNCONNECTED.value)
  if detect_lan_blocks_wifi_regression(interfaces):
    issue_codes.append(RescueIssueCodeV2.NETWORK_WIFI_BLOCKED_BY_LAN_REGRESSION.value)
  if dns_ok:
    issue_codes.append(RescueIssueCodeV2.DNS_OK.value)
  elif default_route:
    issue_codes.append(RescueIssueCodeV2.DNS_FAILED.value)
  if https_ok:
    issue_codes.append(RescueIssueCodeV2.HTTPS_OK.value)
  elif dns_ok:
    issue_codes.append(RescueIssueCodeV2.HTTPS_FAILED.value)

  return {
    "schema_version": CONNECTIVITY_SCHEMA_VERSION,
    "collected_at": _utc_now(),
    "test_sequence": ["lan_wlan", "default_route", "dns", "https"],
    "interfaces": interfaces,
    "default_route": default_route,
    "dns_ok": dns_ok,
    "https_ok": https_ok,
    "https_test_url": https_test_url,
    "dns_host": dns_host,
    "issue_codes": sorted(set(issue_codes)),
  }
