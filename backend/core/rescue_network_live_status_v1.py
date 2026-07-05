"""Rescue live boot status builder — no FastAPI dependency."""

from __future__ import annotations

from typing import Any

from core.rescue_network_connectivity_v2 import build_network_connectivity_v2
from core.rescue_telemetry_connectivity_v1 import build_telemetry_connectivity_v1
from rescue.rescue_boot_status import build_rescue_boot_status


def build_live_boot_status() -> dict[str, Any]:
  connectivity = build_network_connectivity_v2()
  telemetry = build_telemetry_connectivity_v1()
  interfaces = connectivity.get("interfaces") or {}
  network_status = "connected" if (
    interfaces.get("wifi_connected") or interfaces.get("lan_connected")
  ) else "disconnected"
  return build_rescue_boot_status(
    network={
      "status": network_status,
      "required": True,
      "wifi_scan_started": bool(interfaces.get("wlan_present")),
      "default_route": connectivity.get("default_route"),
      "dns_ok": connectivity.get("dns_ok"),
      "https_ok": connectivity.get("https_ok"),
    },
    telemetry={
      "status": "reachable" if telemetry.get("targets") else "unknown",
      "required": False,
      "issue_codes": telemetry.get("issue_codes") or [],
    },
  )
